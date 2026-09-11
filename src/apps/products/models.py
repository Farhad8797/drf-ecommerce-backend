from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid
from django.utils.text import slugify

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
    category = models.ForeignKey('Category', on_delete=models.PROTECT, related_name='products')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='products')
    slug = models.SlugField(unique=True, max_length=255, db_index=True, blank=True)

    def save(self, *, force_insert = False, force_update = False, using = None, update_fields = None):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

class ProductVariant(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='variants')
    image = models.URLField(max_length=500)
    expiry_in_months = models.PositiveIntegerField(default=6, validators=[MinValueValidator(1, 'Must have at least one month if specified')], null=True, blank=True)
    manufacturing_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=1)
    product_image_id = models.CharField(max_length=250)