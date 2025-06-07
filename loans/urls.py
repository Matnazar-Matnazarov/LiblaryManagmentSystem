"""
Professional URL Configuration for Loans App

Provides clean and organized URL routing for:
- Loan management endpoints
- Reservation management endpoints
- Statistics and analytics endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoanViewSet, ReservationViewSet

# Create router for loans app
router = DefaultRouter()
router.register(r'loans', LoanViewSet, basename='loans')
router.register(r'reservations', ReservationViewSet, basename='reservations')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]

# Custom URL names for easier referencing
app_name = 'loans'