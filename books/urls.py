"""
URL Configuration for Books App

Professional routing with comprehensive image handling endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.utils import extend_schema_view

from .views import BookViewSet, AuthorViewSet, PublisherViewSet, CategoryViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'books', BookViewSet, basename='book')
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'publishers', PublisherViewSet, basename='publisher')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    # Include all router URLs
    path('', include(router.urls)),
]

app_name = 'books'