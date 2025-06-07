"""
Professional Views for Accounts App

This module provides organized imports for all authentication and user management views.
"""

from .auth import (
    CustomTokenObtainPairView,
    UserRegistrationView,
    EmailVerificationView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    PasswordChangeView,
    logout_view,
    resend_verification_email,
)

from .users import UserViewSet

__all__ = [
    # Authentication views
    'CustomTokenObtainPairView',
    'UserRegistrationView',
    'EmailVerificationView',
    'PasswordResetRequestView',
    'PasswordResetConfirmView',
    'PasswordChangeView',
    'logout_view',
    'resend_verification_email',
    
    # User management views
    'UserViewSet',
] 