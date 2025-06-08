"""
Professional URL Configuration for Analytics App

Provides comprehensive analytics endpoints:
- Dashboard and KPI monitoring
- Activity tracking and analysis
- Book popularity metrics
- Custom reporting system
- Model-specific monitoring
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardViewSet
from .views.monitor import (
    UserModelMonitorView,
    BookModelMonitorView,
    LoanModelMonitorView,
    AnalyticsModelMonitorView,
    SystemOverviewMonitorView,
)
from .views.dashboard import MonitoringDashboardView, PublicDashboardView

# Create router for analytics app
router = DefaultRouter()

# Dashboard and overview endpoints
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

# URL patterns
urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # HTML Dashboard Interface
    path('dashboard/', MonitoringDashboardView.as_view(), name='monitoring_dashboard'),
    path('public-dashboard/', PublicDashboardView.as_view(), name='public_dashboard'),
    
    # Model-specific monitoring endpoints
    path('monitor/users/', UserModelMonitorView.as_view(), name='monitor_users'),
    path('monitor/books/', BookModelMonitorView.as_view(), name='monitor_books'),
    path('monitor/loans/', LoanModelMonitorView.as_view(), name='monitor_loans'),
    path('monitor/analytics/', AnalyticsModelMonitorView.as_view(), name='monitor_analytics'),
    path('monitor/system/', SystemOverviewMonitorView.as_view(), name='monitor_system'),
]

# Custom URL names for easier referencing
app_name = 'analytics'
