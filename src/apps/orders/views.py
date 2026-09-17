import stripe
from django.db import transaction
from rest_framework.response import Response
from rest_framework import viewsets, views, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from .serializers import (
    CartItemSerializer, CartReadSerializer,
    OrderItemSerializer, OrderReadSerializer, CreateOrderSerializer
)
from utils.stripeConfig import create_payment_intent, verify_webhook_signature
from .models import CartItem, Cart, Order
from apps.products.models import ProductVariant
from django.http import HttpResponse
from django.db.models import F

class CartItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return CartItem.objects.filter(cart__creator = self.request.user).select_related('product_variant__product')
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CartReadSerializer
        return CartItemSerializer
    

class CreateOrderView(views.APIView):
    permission_classes = [IsAuthenticated]
    with transaction.atomic():
        def post(self):
            serializer = CreateOrderSerializer(data=self.request.data, context={'request': self.request})
            serializer.is_valid(raise_exception=True)
            order = serializer.save(user=self.request.user, status='PENDING')
            amount_in_cents = int(order.total_price * 100)

            try:
                payment_intent = create_payment_intent(
                    amount_in_cents=amount_in_cents,
                    metadata={'order_id': order.id, 'user_id': self.request.user.id},
                    merchant_stripe_account_id=self.request.user.stripe_account_id,
                    application_fee_in_cents=amount_in_cents*0.1
                )

                order.stripe_payment_intent_id = payment_intent.id
                order.save()
            except stripe.StripeError as e:
                raise ValidationError({'stripe_error': str(e)})
            
            
class OrderReadView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderReadSerializer
    def get_queryset(self):
        return Order.objects.filter(orderer = self.request.user).select_related('seller').prefetch_related('items__product_variant__product')
    
class OrderWebhookVerifyView(views.APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self):
        payload = self.request.body
        sig_header = self.request.META.get('HTTP_STRIPE_SIGNATURE')

        if not sig_header:
            return Response({"error": "Missing Stripe signature header."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            event = verify_webhook_signature(
                payload=payload,
                sig_header=sig_header
            )

        except (ValueError, stripe.SignatureVerificationError):
            return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
        
        stripe_obj = event['data']['object']
        metadata = stripe_obj.get('metadata', {})
        order_id = metadata.get('order_id')

        if not order_id:
            return Response({'error': 'Missing order_id in metadata'}, status=status.HTTP_400_BAD_REQUEST)
        
        if event['type'] == 'payment_intent.succeeded':
            try:
                with transaction.atomic():
                    order = (
                        Order.objects
                        .prefetch_related('order_items__product_variant')
                        .select_for_update()
                        .filter(id=order_id)
                    )
                    if order.payment_status != Order.PaymentStatus.PAID:
                        order.payment_status = Order.PaymentStatus.PAID
                        order.save(update_fields=['payment_status'])

                        for item in order.order_items.all():
                            ProductVariant.objects.filter(id=item.product_variant).update(
                                stock_quantity=F('stock_quantity') - item.quantity
                            )

                        Cart.objects.filter(creator=order.orderer).delete()

            except Order.DoesNotExist:
                return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
            
        elif event['type'] == 'payment_intent.payment_failed':
            Order.objects.filter(id=order_id).update(payment_status=Order.PaymentStatus.FAILED)

        return Response({'status': 'success'}, status=status.HTTP_200_OK)