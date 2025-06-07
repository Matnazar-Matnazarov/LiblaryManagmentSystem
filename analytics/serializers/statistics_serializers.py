"""
System Statistics Serializers

Professional serializers for system-wide analytics with:
- Dashboard statistics
- Performance metrics
- User activity statistics
- Financial analytics
- System health monitoring
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from ..models import SystemStatistics
from loans.serializers import LoanStatisticsSerializer, ReservationStatisticsSerializer


class SystemStatisticsSerializer(serializers.ModelSerializer):
    """
    Basic system statistics serializer
    """
    class Meta:
        model = SystemStatistics
        fields = [
            'id', 'date', 'total_users', 'active_users', 'new_users',
            'total_books', 'available_books', 'borrowed_books',
            'total_loans', 'total_returns', 'total_reservations',
            'total_searches', 'unique_search_terms',
            'total_fines_collected', 'outstanding_fines',
            'average_response_time', 'error_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DashboardStatsSerializer(serializers.Serializer):
    """
    Comprehensive dashboard statistics serializer
    """
    # Date range
    period = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    generated_at = serializers.DateTimeField()
    
    # Key Performance Indicators (KPIs)
    total_users = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    active_users_week = serializers.IntegerField()
    active_users_month = serializers.IntegerField()
    
    total_books = serializers.IntegerField()
    available_books = serializers.IntegerField()
    borrowed_books = serializers.IntegerField()
    reserved_books = serializers.IntegerField()
    
    # Activity metrics
    loans_today = serializers.IntegerField()
    loans_week = serializers.IntegerField()
    loans_month = serializers.IntegerField()
    
    returns_today = serializers.IntegerField()
    returns_week = serializers.IntegerField()
    returns_month = serializers.IntegerField()
    
    overdue_loans = serializers.IntegerField()
    
    # Financial metrics
    fines_collected_today = serializers.DecimalField(max_digits=10, decimal_places=2)
    fines_collected_week = serializers.DecimalField(max_digits=10, decimal_places=2)
    fines_collected_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    outstanding_fines = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    # Growth metrics
    user_growth_rate = serializers.FloatField()
    activity_growth_rate = serializers.FloatField()
    book_utilization_rate = serializers.FloatField()
    
    # System health
    average_response_time = serializers.FloatField()
    error_rate = serializers.FloatField()
    system_uptime = serializers.FloatField()
    
    # Popular content
    most_popular_books = serializers.ListField()
    most_active_users = serializers.ListField()
    trending_categories = serializers.ListField()
    
    # Charts data
    daily_activity_chart = serializers.ListField()
    weekly_trends_chart = serializers.ListField()
    user_engagement_chart = serializers.ListField()
    book_category_chart = serializers.ListField()


class UserActivityStatsSerializer(serializers.Serializer):
    """
    User activity statistics serializer
    """
    # Time period
    period = serializers.CharField()
    total_users = serializers.IntegerField()
    
    # Registration metrics
    new_registrations = serializers.IntegerField()
    registration_growth_rate = serializers.FloatField()
    
    # Activity metrics
    active_users = serializers.IntegerField()
    inactive_users = serializers.IntegerField()
    highly_active_users = serializers.IntegerField()  # users with >10 activities/week
    
    # Engagement metrics
    avg_sessions_per_user = serializers.FloatField()
    avg_session_duration = serializers.FloatField()
    user_retention_rate = serializers.FloatField()
    
    # Activity breakdown
    login_activities = serializers.IntegerField()
    search_activities = serializers.IntegerField()
    book_view_activities = serializers.IntegerField()
    borrow_activities = serializers.IntegerField()
    
    # User segmentation
    student_users = serializers.IntegerField()
    teacher_users = serializers.IntegerField()
    member_users = serializers.IntegerField()
    librarian_users = serializers.IntegerField()
    
    # Geographic data
    user_locations = serializers.ListField()
    most_active_locations = serializers.ListField()
    
    # Behavioral patterns
    peak_activity_hours = serializers.ListField()
    peak_activity_days = serializers.ListField()
    user_journey_patterns = serializers.ListField()


class BookStatsSerializer(serializers.Serializer):
    """
    Book and catalog statistics serializer
    """
    # Catalog overview
    total_books = serializers.IntegerField()
    available_books = serializers.IntegerField()
    borrowed_books = serializers.IntegerField()
    reserved_books = serializers.IntegerField()
    damaged_books = serializers.IntegerField()
    lost_books = serializers.IntegerField()
    
    # Category breakdown
    total_categories = serializers.IntegerField()
    books_per_category = serializers.ListField()
    most_popular_categories = serializers.ListField()
    underperforming_categories = serializers.ListField()
    
    # Author statistics
    total_authors = serializers.IntegerField()
    most_popular_authors = serializers.ListField()
    prolific_authors = serializers.ListField()
    
    # Publisher data
    total_publishers = serializers.IntegerField()
    top_publishers = serializers.ListField()
    
    # Circulation metrics
    total_circulations = serializers.IntegerField()
    circulation_rate = serializers.FloatField()  # percentage of books borrowed
    avg_loans_per_book = serializers.FloatField()
    
    # Collection health
    new_acquisitions = serializers.IntegerField()
    books_due_for_replacement = serializers.IntegerField()
    collection_age_distribution = serializers.ListField()
    
    # Usage patterns
    most_borrowed_books = serializers.ListField()
    least_borrowed_books = serializers.ListField()
    seasonal_trends = serializers.ListField()
    
    # Recommendations
    suggested_new_books = serializers.ListField()
    books_to_retire = serializers.ListField()


class FinancialStatsSerializer(serializers.Serializer):
    """
    Financial statistics serializer
    """
    # Revenue (if any)
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_this_month = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_growth_rate = serializers.FloatField()
    
    # Fines
    total_fines_issued = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_fines_collected = serializers.DecimalField(max_digits=12, decimal_places=2)
    outstanding_fines = serializers.DecimalField(max_digits=12, decimal_places=2)
    fine_collection_rate = serializers.FloatField()
    
    # Fine breakdown
    overdue_fines = serializers.DecimalField(max_digits=12, decimal_places=2)
    damage_fines = serializers.DecimalField(max_digits=12, decimal_places=2)
    lost_book_fines = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Payment methods (if applicable)
    cash_payments = serializers.DecimalField(max_digits=12, decimal_places=2)
    card_payments = serializers.DecimalField(max_digits=12, decimal_places=2)
    online_payments = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Financial trends
    monthly_revenue_trend = serializers.ListField()
    fine_collection_trend = serializers.ListField()
    payment_method_breakdown = serializers.ListField()
    
    # Cost analysis (operational costs)
    estimated_operational_costs = serializers.DecimalField(max_digits=12, decimal_places=2)
    cost_per_user = serializers.DecimalField(max_digits=8, decimal_places=2)
    cost_per_loan = serializers.DecimalField(max_digits=8, decimal_places=2)
    
    # Projections
    projected_monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    projected_annual_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


class SystemHealthSerializer(serializers.Serializer):
    """
    System health and performance metrics
    """
    # Performance metrics
    avg_response_time = serializers.FloatField()
    p95_response_time = serializers.FloatField()
    p99_response_time = serializers.FloatField()
    
    # Error rates
    error_rate = serializers.FloatField()
    critical_errors = serializers.IntegerField()
    warning_errors = serializers.IntegerField()
    info_errors = serializers.IntegerField()
    
    # System uptime
    uptime_percentage = serializers.FloatField()
    last_downtime = serializers.DateTimeField()
    total_downtime_today = serializers.FloatField()  # in minutes
    
    # Resource usage
    cpu_usage = serializers.FloatField()
    memory_usage = serializers.FloatField()
    disk_usage = serializers.FloatField()
    
    # Database metrics
    database_connections = serializers.IntegerField()
    slow_queries = serializers.IntegerField()
    database_size = serializers.FloatField()  # in GB
    
    # API metrics
    total_api_calls = serializers.IntegerField()
    api_calls_per_minute = serializers.FloatField()
    failed_api_calls = serializers.IntegerField()
    
    # Security metrics
    failed_login_attempts = serializers.IntegerField()
    suspicious_activities = serializers.IntegerField()
    blocked_ips = serializers.ListField()
    
    # Health indicators
    overall_health_score = serializers.FloatField()  # 0-100
    health_status = serializers.CharField()  # 'healthy', 'warning', 'critical'
    health_recommendations = serializers.ListField()


class ComparativeStatsSerializer(serializers.Serializer):
    """
    Comparative statistics between time periods
    """
    # Comparison periods
    current_period = serializers.CharField()
    previous_period = serializers.CharField()
    
    # User metrics comparison
    users_current = serializers.IntegerField()
    users_previous = serializers.IntegerField()
    users_change = serializers.FloatField()
    users_change_percentage = serializers.FloatField()
    
    # Activity metrics comparison
    loans_current = serializers.IntegerField()
    loans_previous = serializers.IntegerField()
    loans_change = serializers.FloatField()
    loans_change_percentage = serializers.FloatField()
    
    # Book metrics comparison
    books_added_current = serializers.IntegerField()
    books_added_previous = serializers.IntegerField()
    
    # Financial comparison
    fines_current = serializers.DecimalField(max_digits=12, decimal_places=2)
    fines_previous = serializers.DecimalField(max_digits=12, decimal_places=2)
    fines_change = serializers.DecimalField(max_digits=12, decimal_places=2)
    fines_change_percentage = serializers.FloatField()
    
    # Performance comparison
    response_time_current = serializers.FloatField()
    response_time_previous = serializers.FloatField()
    response_time_change = serializers.FloatField()
    
    # Trend indicators
    overall_trend = serializers.CharField()  # 'improving', 'declining', 'stable'
    key_improvements = serializers.ListField()
    areas_of_concern = serializers.ListField()


class ReportSummarySerializer(serializers.Serializer):
    """
    Executive summary for analytics reports
    """
    # Report metadata
    report_type = serializers.CharField()
    generated_at = serializers.DateTimeField()
    period_covered = serializers.CharField()
    
    # Key highlights
    total_users = serializers.IntegerField()
    total_books = serializers.IntegerField()
    total_loans = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Performance indicators
    user_satisfaction_score = serializers.FloatField()
    system_efficiency_score = serializers.FloatField()
    collection_utilization_rate = serializers.FloatField()
    
    # Growth metrics
    user_growth = serializers.FloatField()
    activity_growth = serializers.FloatField()
    revenue_growth = serializers.FloatField()
    
    # Top achievements
    achievements = serializers.ListField()
    milestones_reached = serializers.ListField()
    
    # Action items
    recommendations = serializers.ListField()
    priority_actions = serializers.ListField()
    improvement_opportunities = serializers.ListField() 