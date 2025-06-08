"""
Dashboard Views for Monitoring Interface

Bu modul monitoring dashboard uchun HTML interface taqdim etadi.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


def is_admin_user(user):
    """Check if user is admin"""
    return user.is_authenticated and (user.is_superuser or user.is_staff)


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin_user), name='dispatch')
class MonitoringDashboardView(TemplateView):
    """
    Monitoring Dashboard HTML Interface
    
    GET /api/analytics/dashboard/
    """
    template_name = 'analytics/monitoring_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Library Management System - Monitoring Dashboard',
            'user': self.request.user,
        })
        return context


# Public dashboard (simplified version without authentication)
class PublicDashboardView(TemplateView):
    """
    Public Dashboard (limited data)
    
    GET /dashboard/
    """
    template_name = 'analytics/public_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Library Management System - Public Dashboard',
        })
        return context 