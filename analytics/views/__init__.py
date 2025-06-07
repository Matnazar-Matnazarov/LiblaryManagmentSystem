"""
Analytics Views Module

Professional analytics views with modular structure:
- DashboardViewSet: Real-time dashboard and KPIs
- ActivityViewSet: User activity tracking and analysis
- PopularityViewSet: Book popularity and trending analytics
- ReportViewSet: Custom report generation and management
"""

from .dashboard_views import DashboardViewSet

__all__ = [
    'DashboardViewSet',
] 