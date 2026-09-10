from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ValidationError

class UserManager(BaseUserManager):
    def create_user(self, email, username, password = None, **other_fields):
        if (not email) or (not username):
            raise ValidationError('User must have username, email')
        
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            **other_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user
    
class User(AbstractBaseUser):
    class UserType(models.TextChoices):
        MERCHANT = 'merchant', 'Merchant'
        CUSTOMER = 'customer', 'Customer'

    class UserStatus(models.TextChoices):
        VERIFIED = 'verified', 'Verified'
        UNVERIFIED = 'unverified', 'Unverified'

    email = models.EmailField(verbose_name='email is must', max_length=200, unique=True)
    username = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.URLField(blank=True, null=True)
    type = models.CharField(choices=UserType.choices, default=UserType.CUSTOMER, max_length=20)
    status = models.CharField(choices=UserStatus.choices, default=UserStatus.UNVERIFIED, max_length=20)
    is_active = models.BooleanField(default=True)
    image_id = models.CharField(blank=True, max_length=200, null=True)
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    paypal_account_id = models.CharField(max_length=255, blank=True, null=True, unique=True)

    objects=UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def clean(self):
        super().clean()
        if self.type == self.UserType.MERCHANT and not self.image:
            raise ValidationError('A merchant must have an image')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save()

    def __str__(self):
        print(f'Email: {self.email}, Username: {self.username}')



