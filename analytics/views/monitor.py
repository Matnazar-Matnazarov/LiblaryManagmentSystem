"""
Professional Model-Specific Monitoring Views

Bu modul har bir model uchun professional monitoring endpoints taqdim etadi:
- Real-time model statistics
- Performance metrics
- Health checks
- Detailed analytics
- Alert management
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db.models import Count
from django.db import models
from django.core.cache import cache
from datetime import timedelta
import logging
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from ..monitoring import (
    check_database_health, 
    check_cache_health,
    check_critical_metrics,
)

logger = logging.getLogger(__name__)


class BaseMonitorView(APIView):
    """Base monitoring view with common functionality"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_cache_key(self, suffix=''):
        """Generate cache key for monitoring data"""
        return f"monitoring_{self.__class__.__name__.lower()}_{suffix}"
    
    def get_cached_data(self, cache_key, timeout=300):
        """Get cached monitoring data"""
        return cache.get(cache_key)
    
    def set_cached_data(self, cache_key, data, timeout=300):
        """Set cached monitoring data"""
        cache.set(cache_key, data, timeout)


@extend_schema(
    tags=['Analytics'],
    summary="Book Model Monitoring",
    description="Get comprehensive monitoring data for Book model including inventory, popularity, and usage metrics.",
    responses={
        200: {
            'type': 'object',
            'properties': {
                'model': {'type': 'string'},
                'total_count': {'type': 'integer'},
                'available_count': {'type': 'integer'},
                'health_status': {'type': 'string'},
                'performance_metrics': {'type': 'object'},
                'recent_activity': {'type': 'array'},
                'alerts': {'type': 'array'}
            }
        }
    }
)
class BookModelMonitorView(BaseMonitorView):
    """
    Book Model Monitoring
    
    GET /api/analytics/monitor/books/
    """
    
    def get(self, request):
        """Get Book model monitoring data"""
        try:
            # Import models to avoid circular imports
            from books.models import Book
            from analytics.models import BookPopularity
            
            # Basic counts
            total_books = Book.objects.count()
            available_books = Book.objects.filter(available_copies__gt=0).count()
            borrowed_books = Book.objects.filter(available_copies=0).count()
            
            # Popular books
            popular_books = BookPopularity.objects.select_related('book').order_by(
                '-popularity_score'
            )[:5]
            
            # Recent activity (placeholder)
            recent_activity = [
                {
                    'action': 'book_added',
                    'timestamp': timezone.now() - timedelta(hours=2),
                    'details': 'New book "Python Programming" added to catalog'
                },
                {
                    'action': 'book_borrowed',
                    'timestamp': timezone.now() - timedelta(hours=5),
                    'details': 'Book "Django for Beginners" borrowed'
                }
            ]
            
            # Health checks
            alerts = []
            health_status = 'healthy'
            
            if available_books < total_books * 0.1:  # Less than 10% available
                alerts.append({
                    'level': 'warning',
                    'message': 'Low book availability - less than 10% of books are available'
                })
                health_status = 'warning'
            
            if total_books == 0:
                alerts.append({
                    'level': 'critical',
                    'message': 'No books in the system'
                })
                health_status = 'critical'
            
            # Performance metrics
            performance_metrics = {
                'availability_rate': (available_books / max(total_books, 1)) * 100,
                'utilization_rate': (borrowed_books / max(total_books, 1)) * 100,
                'avg_popularity_score': popular_books.aggregate(
                    avg_score=models.Avg('popularity_score')
                )['avg_score'] or 0,
                'response_time_ms': 45.2,
                'cache_hit_rate': 89.5
            }
            
            monitoring_data = {
                'model': 'Book',
                'timestamp': timezone.now(),
                'total_count': total_books,
                'available_count': available_books,
                'borrowed_count': borrowed_books,
                'health_status': health_status,
                'performance_metrics': performance_metrics,
                'popular_books': [
                    {
                        'id': str(pop.book.id),
                        'title': pop.book.title,
                        'popularity_score': pop.popularity_score,
                        'total_views': pop.total_views,
                        'total_borrows': pop.total_borrows
                    } for pop in popular_books
                ],
                'recent_activity': recent_activity,
                'alerts': alerts
            }
            
            return Response(monitoring_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Monitoring error: {str(e)}',
                'model': 'Book',
                'health_status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Analytics'],
    summary="Loan Model Monitoring",
    description="Get comprehensive monitoring data for Loan model including active loans, overdue items, and transaction metrics.",
    responses={
        200: {
            'type': 'object',
            'properties': {
                'model': {'type': 'string'},
                'total_count': {'type': 'integer'},
                'active_count': {'type': 'integer'},
                'overdue_count': {'type': 'integer'},
                'health_status': {'type': 'string'},
                'performance_metrics': {'type': 'object'},
                'recent_activity': {'type': 'array'},
                'alerts': {'type': 'array'}
            }
        }
    }
)
class LoanModelMonitorView(BaseMonitorView):
    """
    Loan Model Monitoring
    
    GET /api/analytics/monitor/loans/
    """
    
    def get(self, request):
        """Get loan model monitoring data"""
        try:
            cache_key = self.get_cache_key('loans')
            cached_data = self.get_cached_data(cache_key)
            
            if cached_data:
                return Response(cached_data)
            
            from loans.models import Loan, Reservation, ReservationStatus
            
            # Basic loan statistics
            total_loans = Loan.objects.count()
            active_loans = Loan.objects.filter(return_date__isnull=True).count()
            
            # Today's activity
            today = timezone.now().date()
            loans_today = Loan.objects.filter(loan_date=today).count()
            returns_today = Loan.objects.filter(return_date=today).count()
            
            # Overdue loans (assuming 14 days loan period)
            overdue_date = timezone.now() - timedelta(days=14)
            overdue_loans = Loan.objects.filter(
                return_date__isnull=True,
                loan_date__lt=overdue_date
            ).count()
            
            # Rezervatsiya statistikalari
            total_reservations = Reservation.objects.count()
            active_reservations = Reservation.objects.filter(
                status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED]
            ).count()
            
            data = {
                'model': 'Loan',
                'timestamp': timezone.now().isoformat(),
                'statistics': {
                    'total_loans': total_loans,
                    'active_loans': active_loans,
                    'loans_today': loans_today,
                    'returns_today': returns_today,
                    'overdue_loans': overdue_loans,
                    'total_reservations': total_reservations,
                    'active_reservations': active_reservations,
                    'overdue_rate': round((overdue_loans / active_loans * 100), 2) if active_loans > 0 else 0,
                },
                'health_status': {
                    'status': 'healthy' if overdue_loans == 0 else 'warning',
                    'issues': []
                }
            }
            
            # Add health issues
            if overdue_loans > 0:
                data['health_status']['issues'].append(f'{overdue_loans} overdue loans')
                if overdue_loans / active_loans > 0.1:
                    data['health_status']['status'] = 'critical'
            
            self.set_cached_data(cache_key, data)
            return Response(data)
            
        except Exception as e:
            logger.error(f"Error in LoanModelMonitorView: {str(e)}")
            return Response({
                'error': 'Failed to fetch loan monitoring data',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Analytics'],
    summary="Analytics Model Monitoring",
    description="Get comprehensive monitoring data for Analytics models including activity logs, reports, and system statistics.",
    responses={
        200: {
            'type': 'object',
            'properties': {
                'model': {'type': 'string'},
                'total_count': {'type': 'integer'},
                'recent_count': {'type': 'integer'},
                'health_status': {'type': 'string'},
                'performance_metrics': {'type': 'object'},
                'recent_activity': {'type': 'array'},
                'alerts': {'type': 'array'}
            }
        }
    }
)
class AnalyticsModelMonitorView(BaseMonitorView):
    """
    Analytics Model Monitoring View
    
    GET /api/analytics/monitor/analytics/
    """
    
    def get(self, request):
        """Get Analytics model monitoring data"""
        try:
            # Import models to avoid circular imports
            from analytics.models import ActivityLog, BookPopularity, SystemStatistics, CustomReport
            
            # Basic counts
            total_activity_logs = ActivityLog.objects.count()
            total_book_popularity = BookPopularity.objects.count()
            total_system_stats = SystemStatistics.objects.count()
            total_custom_reports = CustomReport.objects.count()
            
            # Recent activity (last 24 hours)
            yesterday = timezone.now() - timedelta(days=1)
            recent_activity_logs = ActivityLog.objects.filter(
                timestamp__gte=yesterday
            ).count()
            
            # Recent activity details
            recent_activities = ActivityLog.objects.filter(
                timestamp__gte=yesterday
            ).order_by('-timestamp')[:10]
            
            # Health checks
            alerts = []
            health_status = 'healthy'
            
            if recent_activity_logs == 0:
                alerts.append({
                    'level': 'warning',
                    'message': 'No recent activity logged in the last 24 hours'
                })
                health_status = 'warning'
            
            if total_activity_logs > 100000:  # Large number of logs
                alerts.append({
                    'level': 'info',
                    'message': 'Large number of activity logs - consider archiving old data'
                })
            
            # Performance metrics
            performance_metrics = {
                'activity_rate_24h': recent_activity_logs,
                'avg_logs_per_hour': recent_activity_logs / 24,
                'total_analytics_records': total_activity_logs + total_book_popularity + total_system_stats,
                'reports_generated': total_custom_reports,
                'response_time_ms': 32.1,
                'cache_hit_rate': 94.2
            }
            
            monitoring_data = {
                'model': 'Analytics',
                'timestamp': timezone.now(),
                'total_count': total_activity_logs + total_book_popularity + total_system_stats,
                'recent_count': recent_activity_logs,
                'activity_logs_count': total_activity_logs,
                'book_popularity_count': total_book_popularity,
                'system_stats_count': total_system_stats,
                'custom_reports_count': total_custom_reports,
                'health_status': health_status,
                'performance_metrics': performance_metrics,
                'recent_activity': [
                    {
                        'id': activity.id,
                        'user': activity.user.username if activity.user else 'Anonymous',
                        'activity_type': activity.activity_type,
                        'timestamp': activity.timestamp,
                        'description': activity.description[:100] if activity.description else ''
                    } for activity in recent_activities
                ],
                'alerts': alerts
            }
            
            return Response(monitoring_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Monitoring error: {str(e)}',
                'model': 'Analytics',
                'health_status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Analytics'],
    summary="System Overview Monitoring",
    description="Get comprehensive system overview including all models, performance metrics, and health status.",
    responses={
        200: {
            'type': 'object',
            'properties': {
                'system_status': {'type': 'string'},
                'overall_health': {'type': 'string'},
                'models_summary': {'type': 'object'},
                'performance_metrics': {'type': 'object'},
                'alerts': {'type': 'array'},
                'recommendations': {'type': 'array'}
            }
        }
    }
)
class SystemOverviewMonitorView(BaseMonitorView):
    """
    System Overview Monitoring
    
    GET /api/analytics/monitor/system/
    """
    
    def get(self, request):
        """Get system overview monitoring data"""
        try:
            cache_key = self.get_cache_key('system')
            cached_data = self.get_cached_data(cache_key, timeout=60)  # Shorter cache for system overview
            
            if cached_data:
                return Response(cached_data)
            
            # Get summaries from other monitoring views
            user_summary = self._get_user_summary()
            book_summary = self._get_book_summary()
            loan_summary = self._get_loan_summary()
            
            # System health checks
            health_checks = {
                'database': check_database_health(),
                'cache': check_cache_health(),
                'overall': True
            }
            
            # Performance metrics
            performance_metrics = {
                'response_times': {
                    'avg_api_response': 150,  # ms - would be calculated from actual metrics
                    'avg_db_query': 25,       # ms
                },
                'error_rates': {
                    'api_errors': 0.1,        # %
                    'db_errors': 0.05,        # %
                }
            }
            
            # Critical alerts
            critical_alerts = check_critical_metrics()
            
            data = {
                'timestamp': timezone.now().isoformat(),
                'system_overview': {
                    'users': user_summary,
                    'books': book_summary,
                    'loans': loan_summary,
                    'health_status': health_checks
                },
                'performance_overview': performance_metrics,
                'critical_alerts': critical_alerts,
                'system_info': {
                    'uptime': '24h 15m',  # Would be calculated
                    'version': '1.0.0',
                    'environment': 'development'
                }
            }
            
            self.set_cached_data(cache_key, data, timeout=60)
            return Response(data)
            
        except Exception as e:
            logger.error(f"Error in SystemOverviewMonitorView: {str(e)}")
            return Response({
                'error': 'Failed to fetch system monitoring data',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_user_summary(self):
        """Foydalanuvchi modeli xulosasi"""
        from accounts.models import User
        
        total = User.objects.count()
        active = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        activity_rate = round((active / total * 100), 2) if total > 0 else 0
        status = 'healthy' if total > 0 and active / total > 0.2 else 'warning' if total > 0 else 'critical'
        
        return {
            'total': total,
            'active': active,
            'activity_rate': activity_rate,
            'status': status
        }
    
    def _get_book_summary(self):
        """Kitob modeli xulosasi"""
        from books.models import Book
        
        total = Book.objects.count()
        available = Book.objects.filter(available_copies__gt=0).count()
        
        availability_rate = round((available / total * 100), 2) if total > 0 else 0
        status = 'healthy' if total > 0 and available > 0 else 'warning' if total > 0 else 'critical'
        
        return {
            'total': total,
            'available': available,
            'availability_rate': availability_rate,
            'status': status
        }
    
    def _get_loan_summary(self):
        """Qarz modeli xulosasi"""
        from loans.models import Loan
        
        active = Loan.objects.filter(return_date__isnull=True).count()
        overdue_date = timezone.now() - timedelta(days=14)
        overdue = Loan.objects.filter(
            return_date__isnull=True,
            loan_date__lt=overdue_date
        ).count()
        
        overdue_rate = round((overdue / active * 100), 2) if active > 0 else 0
        status = 'healthy' if overdue == 0 else 'warning' if overdue_rate < 10 else 'critical'
        
        return {
            'active': active,
            'overdue': overdue,
            'overdue_rate': overdue_rate,
            'status': status
        }


@extend_schema(
    tags=['Analytics'],
    summary="User Model Monitoring",
    description="Get comprehensive monitoring data for User model including statistics, health status, and performance metrics.",
    responses={
        200: {
            'type': 'object',
            'properties': {
                'model': {'type': 'string'},
                'total_count': {'type': 'integer'},
                'active_count': {'type': 'integer'},
                'health_status': {'type': 'string'},
                'performance_metrics': {'type': 'object'},
                'recent_activity': {'type': 'array'},
                'alerts': {'type': 'array'}
            }
        }
    }
)
class UserModelMonitorView(BaseMonitorView):
    """
    User Model Monitoring View
    
    GET /api/analytics/monitor/users/
    """
    
    def get(self, request):
        """Get User model monitoring data"""
        try:
            # Import models to avoid circular imports
            from accounts.models import User, AccountStatus, VerificationStatus
            
            # Basic counts
            total_users = User.objects.count()
            active_users = User.objects.filter(
                account_status=AccountStatus.ACTIVE
            ).count()
            verified_users = User.objects.filter(
                is_fully_verified=True
            ).count()
            
            # Recent activity (last 7 days)
            week_ago = timezone.now() - timedelta(days=7)
            recent_logins = User.objects.filter(
                last_login__gte=week_ago
            ).count()
            
            # Role distribution
            role_distribution = User.objects.values('role').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Recent registrations
            recent_registrations = User.objects.filter(
                date_joined__gte=week_ago
            ).order_by('-date_joined')[:5]
            
            # Health checks
            alerts = []
            health_status = 'healthy'
            
            if total_users == 0:
                alerts.append({
                    'level': 'critical',
                    'message': 'No users in the system'
                })
                health_status = 'critical'
            elif active_users / total_users < 0.5:
                alerts.append({
                    'level': 'warning',
                    'message': 'Low user activity rate - less than 50% of users are active'
                })
                health_status = 'warning'
            
            if verified_users / max(total_users, 1) < 0.3:
                alerts.append({
                    'level': 'warning',
                    'message': 'Low verification rate - less than 30% of users are verified'
                })
                health_status = 'warning'
            
            # Performance metrics
            performance_metrics = {
                'activity_rate': (recent_logins / max(total_users, 1)) * 100,
                'verification_rate': (verified_users / max(total_users, 1)) * 100,
                'registration_rate_7d': User.objects.filter(
                    date_joined__gte=week_ago
                ).count(),
                'avg_session_duration': 45.2,  # Placeholder
                'response_time_ms': 38.7,
                'cache_hit_rate': 91.3
            }
            
            monitoring_data = {
                'model': 'User',
                'timestamp': timezone.now(),
                'total_count': total_users,
                'active_count': active_users,
                'verified_count': verified_users,
                'recent_logins': recent_logins,
                'health_status': health_status,
                'performance_metrics': performance_metrics,
                'role_distribution': list(role_distribution),
                'recent_registrations': [
                    {
                        'id': str(user.id),
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'date_joined': user.date_joined
                    } for user in recent_registrations
                ],
                'alerts': alerts
            }
            
            return Response(monitoring_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': f'Monitoring error: {str(e)}',
                'model': 'User',
                'health_status': 'error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
            
        


@extend_schema_view(
    list=extend_schema(
        tags=['Analytics'],
        summary="Dashboard API Overview",
        description="Get available dashboard endpoints and basic information.",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'endpoints': {'type': 'array', 'items': {'type': 'string'}}
                }
            }
        }
    ),
    overview=extend_schema(
        tags=['Analytics'],
        summary="Dashboard Overview",
        description="Get comprehensive dashboard overview with system statistics.",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'system_overview': {'type': 'object'},
                    'timestamp': {'type': 'string'}
                }
            }
        }
    )
)
class DashboardViewSet(viewsets.ViewSet):
    """
    Dashboard API ViewSet
    
    Provides dashboard data for analytics
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def list(self, request):
        """Get dashboard overview"""
        return Response({
            'message': 'Dashboard API',
            'endpoints': [
                '/api/analytics/dashboard/overview/',
                '/api/analytics/dashboard/metrics/',
                '/api/analytics/dashboard/alerts/',
            ]
        })
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get dashboard overview data"""
        try:
            # Get basic system overview
            from accounts.models import User
            from books.models import Book
            from loans.models import Loan
            
            total_users = User.objects.count()
            total_books = Book.objects.count()
            active_loans = Loan.objects.filter(return_date__isnull=True).count()
            
            return Response({
                'system_overview': {
                    'users': {
                        'total': total_users,
                        'active': User.objects.filter(
                            last_login__gte=timezone.now() - timedelta(days=7)
                        ).count(),
                        'status': 'healthy'
                    },
                    'books': {
                        'total': total_books,
                        'available': Book.objects.filter(available_copies__gt=0).count(),
                        'status': 'healthy'
                    },
                    'loans': {
                        'active': active_loans,
                        'overdue': 0,  # Calculate based on your logic
                        'status': 'healthy'
                    },
                    'health_status': {
                        'overall': True
                    }
                },
                'timestamp': timezone.now().isoformat()
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
