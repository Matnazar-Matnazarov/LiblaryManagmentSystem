"""
Analytics Views Package

Bu package analytics app uchun barcha view larni o'z ichiga oladi:
- Dashboard views
- Monitoring views  
- Report views
- API endpoints
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from datetime import timedelta

from .monitor import (
    UserModelMonitorView,
    BookModelMonitorView,
    LoanModelMonitorView,
    AnalyticsModelMonitorView,
    SystemOverviewMonitorView,
    DashboardViewSet
)


__all__ = [
    'DashboardViewSet',
    'UserModelMonitorView',
    'BookModelMonitorView', 
    'LoanModelMonitorView',
    'AnalyticsModelMonitorView',
    'SystemOverviewMonitorView',
    'DashboardViewSet',
] 