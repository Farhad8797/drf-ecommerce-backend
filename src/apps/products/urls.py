from .views import (
    CategoryView,
    ProductVariantUpdateRetrieveDeleteViewSet,
    ProductReadView,
    ProductCreateUpdateDeleteRetrieveViewSet,
    ProductVariantCreateListViewSet,
    ProductVariantReadView
)

from django.urls import path

urlpatterns = [
    path('category/<str:product_type>/', CategoryView.as_view({'get':'retrieve'}), name='category'),
    path('product/<slug:slug>/', ProductReadView.as_view({'get':'retrieve'}), name='product'),
    path('product-variant/<int:pk>/', ProductVariantReadView.as_view({'get':'retrieve'}), name='product_variant'),
    path('c/product/', ProductCreateUpdateDeleteRetrieveViewSet.as_view({'get':'list', 'post':'create'}), name='created_product'),
    path('u/product/<slug:slug>/', 
         ProductCreateUpdateDeleteRetrieveViewSet.as_view({'get':'retrieve', 'patch':'partial_update', 'put':'update', 'delete':'destroy'}), 
         name='updated_product'
    ),
    path('c/product-variant/', ProductVariantCreateListViewSet.as_view({'get':'list', 'post':'create'}), name='created_product_variant'),
    path('u/product-variant/<int:pk>/', 
         ProductVariantUpdateRetrieveDeleteViewSet.as_view({'get':'retrieve', 'patch':'partial_update', 'put':'update', 'delete':'destroy'}), 
         name='updated_product_variant'
    )
]
