import stripe
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework import viewsets, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .serializers import (
    CartItemSerializer, CartReadSerializer,
    OrderItemSerializer, OrderReadSerializer, CreateOrderSerializer
)
from utils.stripe import create_payment_intent, verify_webhook_signature
from .models import CartItem, Cart, Order
from django.http import HttpResponse

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
    
@csrf_exempt
def verify_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        event = verify_webhook_signature(payload=payload, sig_header=sig_header)
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponse('Could not verify stripe signature', status=400)
    
    order_id = event['data']['object']['metadata']['order_id']
    # handle successful payment
    if event['type'] == 'payment_intent.succeeded':
        try:
            order = Order.objects.get(id=order_id)
            if order.payment_status != Order.PaymentStatus.PAID:
                order.payment_status = Order.PaymentStatus.PAID
                order.save()
                Cart.objects.filter(creator = order.orderer).delete()
        except Order.DoesNotExist:
            return HttpResponse('No order found!', status=404)
        
    elif event['type'] == 'payment_intent.payment_failed':
        try:
            order = Order.objects.get(id=order_id)
            if order.payment_status != Order.PaymentStatus.FAILED:
                order.payment_status = Order.PaymentStatus.FAILED
                order.save()
        except Order.DoesNotExist:
            return HttpResponse('No order found!', status=404)
        
    else: 
        pass

    return HttpResponse('Payment successful!', status=200)
