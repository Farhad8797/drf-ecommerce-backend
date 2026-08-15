from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
import uuid
from decimal import Decimal
from django.db.models import Sum, F

class Order(models.Model):
    class PaymentMethod(models.TextChoices):
        CARD = 'CARD', 'Card'
        PAYPAL = 'PAYPAL', 'Paypal'
        STRIPE = 'STRIPE', 'Stripe'
        CASH_ON_DELIVERY = 'CASH_ON_DELIVERY', 'Cash_on_delivery'

    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'

    class DeliveryStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SHIPPED = 'SHIPPED', 'Shipped'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    orderer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='customer_orders')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='seller_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(choices=PaymentMethod.choices, default=PaymentMethod.CARD, max_length=20)
    payment_status = models.CharField(choices=PaymentStatus.choices, default=PaymentStatus.PENDING, max_length=20)
    delivery_status = models.CharField(choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING, max_length=20)

    def calculate_total_price(self):
        total = self.order_items.aggregate(
            total = Sum(F('price') * F('quantity'))
        )['total']
        self.total_price = total or Decimal('0.00')
        self.save(update_fields=['total_price']) 


class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_items')
    product_variant = models.ForeignKey('products.ProductVariant', on_delete=models.PROTECT, related_name='order_items_variants')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1, validators=[MaxValueValidator(100, 'Cannot order more than 100 same items in 1 order'), MinValueValidator(1, 'At least 1 item is required')])
    
    @property
    def items_total(self) -> Decimal:
        return self.quantity * self.price
    

class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey('products.ProductVariant', on_delete=models.PROTECT, related_name='cart_items_variants')
    quantity = models.PositiveIntegerField(default=1, validators=[MaxValueValidator(100, 'Cannot order more than 100 same items in 1 order'), MinValueValidator(1, 'At least 1 item is required')])

    @property
    def items_total(self) -> Decimal:
        if self.product_variant and hasattr(self.product_variant, 'price'):
            return self.product_variant.price * self.quantity
        return Decimal('0.00')