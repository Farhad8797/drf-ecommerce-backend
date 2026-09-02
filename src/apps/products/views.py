from .serializers import (
    CategorySerializer,
    ProductCreateOrUpdateSerializer,
    ProductVariantCreateSerializer,
    ProductReadSerializer,
    ProductVariantReadSerializer,
    ProductVariantUpdateSerializer
)

from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.generics import DestroyAPIView
from .permissions import IsMerchantOwner
from .models import Category, Product, ProductVariant

class CategoryView(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer
    lookup_field = 'product_type'

class ProductReadView(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    permission_classes = [AllowAny]
    serializer_class = ProductReadSerializer
    lookup_field = 'slug'

class ProductVariantReadView(viewsets.ReadOnlyModelViewSet):
    queryset = ProductVariant.objects.all()
    permission_classes = [AllowAny]
    serializer_class = ProductVariantReadSerializer
    lookup_field = 'id'

class ProductCreateUpdateDeleteRetrieveViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsMerchantOwner]
    serializer_class = ProductCreateOrUpdateSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Product.objects.none()
        return Product.objects.filter(seller = self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)
    
class ProductVariantCreateListViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsMerchantOwner]
    serializer_class = ProductVariantCreateSerializer

class ProductVariantUpdateRetrieveDeleteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsMerchantOwner]
    serializer_class = ProductVariantUpdateSerializer
    lookup_field = 'id'

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Product.objects.none()
        return ProductVariant.objects.filter(product__seller=self.request.user)
    
