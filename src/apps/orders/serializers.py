from rest_framework import serializers
from .models import Order, OrderItem, Cart, CartItem
from decimal import Decimal
from django.db import transaction
from collections import defaultdict

class CartItemSerializer(serializers.ModelSerializer):
    items_total = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = [
            'id',
            'cart',
            'quantity',
            'product_variant',
            'items_total'
        ]
        read_only_fields = ['id','cart']


class CartReadSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    cart_total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id',
            'items',
            'creator',
            'created_at',
            'cart_total'
        ]
        read_only_fields = fields

    def get_cart_total(self, obj: Cart) -> Decimal:
        return sum((item.item_total for item in obj.items.all()), Decimal('0.00'))
    

class OrderItemSerializer(serializers.ModelSerializer):
    items_total = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'order',
            'product_variant',
            'price',
            'quantity',
            'items_total'
        ]
        read_only_fields = ['id','order','price', 'items_total']


class OrderReadSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'orderer',
            'seller',
            'created_at',
            'total_price',
            'payment_method',
            'payment_status',
            'delivery_status',
            'order_items',
        ]
        read_only_fields = fields


class CreateOrderSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=Order.payment_method.choices)

    def validate(self, attrs):
        user = self.context['request'].user

        try:
            cart = Cart.objects.prefetch_related('items__product_variant__product__seller').filter(creator = user).order_by('-created_at').first()
        except Cart.DoesNotExist:
            raise serializers.ValidationError('User does not have any active Cart')
        
        cart_items = cart.items.all()
        if not cart_items.exists():
            raise serializers.ValidationError('Cart is empty')
        
        attrs['cart_items'] = cart_items
        return attrs
    
    def create(self, validated_data):
        user = self.context['request'].user
        payment_method = validated_data['payment_method']
        cart_items = validated_data['cart_items']

        items_by_seller = defaultdict(list)

        for item in cart_items:
            seller = item.product_variant.product.seller
            items_by_seller[seller].append(item)

        created_orders = []

        with transaction.atomic():
            for seller, items in items_by_seller.items():
                total_price_for_this_seller = sum(item.product_variant.price * item.quantity for item in items)

                order = Order.objects.create(
                    orderer=user,
                    seller=seller,
                    total_price=total_price_for_this_seller,
                    payment_method=payment_method,
                    payment_status=Order.PaymentStatus.PENDING,
                    delivery_status=Order.DeliveryStatus.PENDING,
                )

                order_items_to_be_created = [
                    OrderItem(
                        order = order,
                        product_variant = item.product_variant,
                        price = item.product_variant.price,
                        quantity = item.quantity
                    ) for item in items
                ]

                OrderItem.objects.bulk_create(order_items_to_be_created)
                created_orders.append(order)

            if payment_method == Order.PaymentMethod.CASH_ON_DELIVERY:
                cart_items.delete()

        return created_orders