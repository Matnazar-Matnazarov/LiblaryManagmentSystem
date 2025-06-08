"""
Professional URL Configuration for Accounts App

Comprehensive user management with image handling endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet
from .views.auth import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    UserRegistrationView,
    EmailVerificationView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    PasswordChangeView,
    logout_view,
    resend_verification_email,
)
from .views.custom_google_login import CustomGoogleLoginView

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Authentication endpoints (Authentication tag)
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/register/', UserRegistrationView.as_view(), name='user_register'),
    path('auth/verify-email/<str:uidb64>/<str:token>/', EmailVerificationView.as_view(), name='email_verify'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/password-reset-confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/password-change/', PasswordChangeView.as_view(), name='password_change'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/resend-verification/', resend_verification_email, name='resend_verification'),
    
    # JWT Token endpoints (JWT Tokens tag)
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', CustomTokenVerifyView.as_view(), name='token_verify'),
    
    # Include all router URLs (Users tag)
    path('', include(router.urls)),
      # Google login endpoints - providing multiple paths to ensure frontend can connect
    path("api/google-login/", CustomGoogleLoginView.as_view(), name="google-login"),
    path("api/google/login/", CustomGoogleLoginView.as_view(), name="google-login-alt"),
    path("accounts/api/google/login/", CustomGoogleLoginView.as_view(), name="google-login-accounts"),
    path("accounts/api/google-login/", CustomGoogleLoginView.as_view(), name="google-login-accounts-dash"),
]

# Add app namespace
app_name = 'accounts'