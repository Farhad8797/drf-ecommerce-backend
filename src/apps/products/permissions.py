from rest_framework import permissions
from apps.accounts.models import User

class IsMerchantOwner(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        is_merchant = getattr(request.user, 'type', None) == User.UserType.MERCHANT
        return bool(request.user and request.user.is_authenticated and is_merchant)
    
    def has_object_permission(self, request, view, obj) -> bool:
        if hasattr(obj, 'seller'):
            return obj.seller == request.user
        if hasattr(obj, 'product'):
            return obj.product.seller == request.user
        
        return False