from django.urls import path
from .views import (
    CartItemViewSet,
    CreateOrderView,
    OrderReadView,
    OrderWebhookVerifyView
)

urlpatterns = [
    path('cart/items/',CartItemViewSet.as_view({'get': 'list', 'post': 'create'}),name='cart_item_list'),
    path(
        'cart/items/<int:pk>/', 
        CartItemViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), 
        name='cart_item_detail'
    ),
    path('orders/', CreateOrderView.as_view(), name='create_order'),
    path('orders/history/', OrderReadView.as_view({'get': 'list'}), name='order_history'),
    path('payment/webhook/', OrderWebhookVerifyView.as_view(), name='verify_webhook')
]
