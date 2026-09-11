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
from utils.stripe import create_express_account, create_account_onboarding_link, verify_webhook_signature

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

    def post(self, request: Request):
        refresh_token = request.COOKIES.get('refresh_token') or request.data.get('refresh_token')
        if not refresh_token:
                return Response({'error': 'refresh token not found'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data={'refresh':refresh_token})
        serializer.is_valid(raise_exception=True)
        access_token = serializer.validated_data['access']
        response = Response({'access_token': access_token}, status=status.HTTP_200_OK)
        response.set_cookie(key='access_token', value=access_token, max_age=int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds()), httponly=True, secure=False)
        return response 

class StripeOnboardingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self):
        user = self.request.user
        if user.type != user.UserType.MERCHANT:
            return Response(
                {"error": "Only merchant accounts can initiate payment onboarding."},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            if not user.stripe_account_id:
                stripe_account = create_express_account(email=user.email)
                user.stripe_account_id = stripe_account.id
                user.save(update_fields=['stripe_account_id'])

            return_url  = 'http://127.0.0.1:8000/api/accounts/stripe/return/'
            refresh_url = 'http://127.0.0.1:8000/api/accounts/stripe/refresh/'

            account_link = create_account_onboarding_link(stripe_account_id=user.stripe_account_id, refresh_url=refresh_url)
            return Response({"onboarding_url": account_link.url}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StripeAccountWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self):
        payload = self.request.body
        sig_header = self.request.META.get('HTTP_STRIPE_SIGNATURE')

        if not sig_header:
            return Response({"error": "Missing Stripe signature header."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            event: dict = verify_webhook_signature(payload=payload, sig_header=sig_header)
            if event['type'] == 'account.updated':
                obj: dict = event['data']['object']
                id = obj['id']
                charges_enabled, payouts_enabled = obj.get('charges_enabled', False), obj.get('payouts_enabled', False)

                user = User.objects.filter(stripe_account_id=id).first()
                if charges_enabled and payouts_enabled:
                    if user.status != user.UserStatus.VERIFIED:
                        user.status = User.UserStatus.VERIFIED
                        user.save(update_fields=['status'])
                        return Response({"status": "success"}, status=status.HTTP_200_OK)
                else:
                    if user.status != user.UserStatus.UNVERIFIED:
                        user.status = User.UserStatus.UNVERIFIED
                        user.save(update_fields=['status'])
                        return Response({"status": "User unverified"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Webhook verification failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class DeleteAccountView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def destroy(self, request: Request, *args, **kwargs):
        user: User = request.user
        user.is_active = False
        user.delete()
        response =  Response(
            {"message": "Account deleted successfully"},
            status=status.HTTP_200_OK,
        )

        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
