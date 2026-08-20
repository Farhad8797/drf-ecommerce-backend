from django.urls import path, include
from .views import (
    CartItemViewSet,
    CreateOrderView,
    OrderReadView,
    verify_wenhook
)
from rest_framework.routers import DefaultRouter

# Router for viewset
router = DefaultRouter()
router.register('cart/items/', CartItemViewSet, basename='cart-items')

urlpatterns = [
    path('', include(router.urls)),
    path('orders/', CreateOrderView.as_view(), name='create-order'),
    path('orders/history/', OrderReadView.as_view(), name='order-history'),
    path('payment/webhook/', verify_wenhook, name='verify-webhook')
]
