from django.urls import path
from .views import (
    SignInView,
    SignOutView,
    SignUpView,
    AccountInfoView,
    UpdateAccountInfoView,
    ChangePasswordView,
    NewAccessTokenView,
    DeleteAccountView
)

urlpatterns = [
    path('sign-up/', SignUpView.as_view(), name='sign_up'),
    path('sign-in/', SignInView.as_view(), name='sign_in'),
    path('sign-out/', SignOutView.as_view(), name='sign_out'),
    path('u/', AccountInfoView.as_view(), name='account_info'),
    path('u/update-info/', UpdateAccountInfoView.as_view(), name='update_info'),
    path('u/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('new-access-token/', NewAccessTokenView.as_view(), name='new_access_token'),
    path('u/delete-account/', DeleteAccountView.as_view(), name='delete_account')
]
