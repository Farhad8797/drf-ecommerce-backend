from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid

class Category(models.Model):
    class ProductType(models.TextChoices):
        HARDWARE = 'HARDWARE', 'Hardware & Equipment'
        DIGITAL = 'DIGITAL', 'Digital Software, Licenses & E-books'
        OTHERS = 'OTHERS', 'Luxury & Cosmetics'

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    product_type = models.CharField(choices=ProductType.choices, max_length=100)


class Product(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=150)
    brand = models.CharField(max_length=50)
    catergory = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')


class ProductVariant(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='variants')
    image = models.URLField(max_length=500)
    expiry_in_months = models.PositiveIntegerField(default=6, validators=[MinValueValidator(1, 'Must have at least one month if specified')], null=True, blank=True)
    manufacturing_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=1)