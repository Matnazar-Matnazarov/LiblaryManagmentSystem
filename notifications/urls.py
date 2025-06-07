"""
Professional URL Configuration for Notifications App
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Create router for ViewSets (when implemented)
router = DefaultRouter()

# URL patterns
urlpatterns = [
    # ViewSet URLs (when implemented)
    path('', include(router.urls)),
]

# Custom URL names for easier referencing
app_name = 'notifications'