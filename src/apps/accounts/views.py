from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
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
    authentication_classes = []


class SignInView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens: dict = serializer.validated_data

        access_token = tokens.get('access')
        refresh_token = tokens.get('refresh')

        response = Response({'detail': 'authentication successful!'}, status=status.HTTP_200_OK)

        response.set_cookie(
            key='access_token', 
            value=access_token, 
            secure=False, 
            httponly=True, 
            samesite='Lax', 
            max_age=int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds())
        )
        
        response.set_cookie(
            key='refresh_token', 
            value=refresh_token, 
            secure=False, 
            httponly=True, 
            samesite='Lax', 
            max_age=int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds())
        )

        return response


class SignOutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request):
        try:
            refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh')
            if not refresh_token:
                return Response({'error': 'refresh token not found'}, status=status.HTTP_400_BAD_REQUEST)
            token =  RefreshToken(refresh_token)
            token.blacklist()
            response = Response({'success': 'Successfully logged out User'}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response({'error': 'invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)

        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response



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

    def get(self, request: Request):
        refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh_token')
        serializer = self.get_serializer(data={'refresh':refresh_token})
        serializer.is_valid(raise_exception=True)
        access_token = serializer.validated_data['access']
        response = Response({'access_token': access_token}, status=status.HTTP_200_OK)
        response.set_cookie(key='access_token', value=access_token, max_age=int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds()), httponly=True, secure=False)
        return response 


class DeleteAccountView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def destroy(self, request: Request, *args, **kwargs):
        user: User = self.request.user
        user.is_active = False
        user.delete()
        response =  Response(
            {"message": "Account deleted successfully"},
            status=status.HTTP_200_OK,
        )

        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
