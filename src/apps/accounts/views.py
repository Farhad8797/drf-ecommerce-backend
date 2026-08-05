from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .serializers import (UserSerializer, 
                         UserRegistrationSerializer, 
                         UpdateAccountInfoSerializer, 
                         ChangePasswordSerializer)

User = get_user_model()

class SignUpView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class SignInView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]


class SignOutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request):
        try:
            refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh')
            if not refresh_token:
                return Response({'error': 'refresh token not found'}, status=status.HTTP_400_BAD_REQUEST)
            token =  RefreshToken(refresh_token)
            token.blacklist()
            return Response({'success': 'Successfully logged out User'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({'error': 'invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)


class AccountInfoView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
    

class UpdateAccountInfoView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UpdateAccountInfoSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request: Request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return Response(
                {"message": "Password updated successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NewAccessTokenView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class DeleteAccountView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def destroy(self, request: Request, *args, **kwargs):
        user: User = self.request.user
        user.is_active = False
        user.status = getattr(User.UserStatus, 'DELETED', 'deleted')
        user.save()
        return Response(
            {"message": "Account deactivated successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )
    
