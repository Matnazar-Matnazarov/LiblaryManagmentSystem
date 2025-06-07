"""
Main URL Configuration for Library Management System.

Includes:
- API v1 routing
- Admin interface
- API documentation (Swagger & ReDoc)
- Media file serving (development)
- Health check endpoints
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# API URL patterns with separated namespaces
api_patterns = [
    # Authentication & User Management (accounts app handles both auth/ and users/)
    path('', include('accounts.urls')),
    
    # Books Management  
    path('', include('books.urls')),
    
    # Other Services
    path('loans/', include('loans.urls')),
    path('analytics/', include('analytics.urls')),
    path('notifications/', include('notifications.urls')),
]

# Main URL patterns
urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include(api_patterns)),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
        
    # Prometheus metrics (if enabled)
    path('metrics/', include('django_prometheus.urls')),
    
    # Root redirect to API docs
    path('', RedirectView.as_view(url='/api/docs/', permanent=False)),
]

# Development settings
if settings.DEBUG:
    # Serve media files during development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    

# Admin customization
admin.site.site_header = "Library Management System"
admin.site.site_title = "Library Admin"
admin.site.index_title = "Welcome to Library Management System Administration"
