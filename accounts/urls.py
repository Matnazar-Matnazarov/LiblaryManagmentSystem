"""
Professional URL Configuration for Accounts App

Comprehensive user management with image handling endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import UserViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # JWT Token endpoints
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Include all router URLs (includes auth endpoints from UserViewSet)
    path('', include(router.urls)),
]

# Add app namespace
app_name = 'accounts'