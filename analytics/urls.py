"""
Professional URL Configuration for Analytics App

Provides comprehensive analytics endpoints:
- Dashboard and KPI monitoring
- Activity tracking and analysis
- Book popularity metrics
- Custom reporting system
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardViewSet

# Create router for analytics app
router = DefaultRouter()

# Dashboard and overview endpoints
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]

# Custom URL names for easier referencing
app_name = 'analytics'