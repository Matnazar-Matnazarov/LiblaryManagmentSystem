"""
Activity Tracking Serializers

Professional serializers for user activity analytics with:
- Activity log tracking
- Activity summaries
- User behavior analysis
- System monitoring
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from ..models import ActivityLog, ActivityType
from accounts.serializers import UserSerializer


class ActivityLogSerializer(serializers.ModelSerializer):
    """
    Basic activity log serializer for list views
    """
    user = UserSerializer(read_only=True)
    activity_type_display = serializers.CharField(
        source='get_activity_type_display',
        read_only=True
    )
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'activity_type', 'activity_type_display',
            'description', 'object_type', 'object_id', 'ip_address',
            'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class ActivityLogDetailSerializer(ActivityLogSerializer):
    """
    Detailed activity log serializer with full information
    """
    metadata = serializers.JSONField(read_only=True)
    user_agent = serializers.CharField(read_only=True)
    
    class Meta(ActivityLogSerializer.Meta):
        fields = ActivityLogSerializer.Meta.fields + [
            'user_agent', 'metadata'
        ]


class ActivityLogCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating activity logs
    """
    user_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = ActivityLog
        fields = [
            'user_id', 'activity_type', 'description', 'object_type',
            'object_id', 'ip_address', 'user_agent', 'metadata'
        ]
    
    def validate_activity_type(self, value):
        """Validate activity type"""
        if value not in [choice[0] for choice in ActivityType.choices]:
            raise serializers.ValidationError("Invalid activity type.")
        return value
    
    def create(self, validated_data):
        """Create activity log"""
        user_id = validated_data.pop('user_id', None)
        
        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                validated_data['user'] = user
            except User.DoesNotExist:
                validated_data['user'] = None
        
        return ActivityLog.objects.create(**validated_data)


class ActivitySummarySerializer(serializers.Serializer):
    """
    Serializer for activity summary statistics
    """
    # Time period
    period = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    
    # Activity counts by type
    total_activities = serializers.IntegerField()
    login_count = serializers.IntegerField()
    book_searches = serializers.IntegerField()
    book_views = serializers.IntegerField()
    book_borrows = serializers.IntegerField()
    book_returns = serializers.IntegerField()
    reservations = serializers.IntegerField()
    
    # User engagement metrics
    unique_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    avg_session_duration = serializers.FloatField()
    
    # Popular activities
    most_active_users = serializers.ListField()
    peak_activity_hours = serializers.ListField()
    activity_trend = serializers.ListField()
    
    # Geographic/technical data
    top_ip_addresses = serializers.ListField()
    browser_stats = serializers.ListField()


class UserActivityStatsSerializer(serializers.Serializer):
    """
    Serializer for individual user activity statistics
    """
    user = UserSerializer(read_only=True)
    
    # Activity counts
    total_activities = serializers.IntegerField()
    activities_today = serializers.IntegerField()
    activities_this_week = serializers.IntegerField()
    activities_this_month = serializers.IntegerField()
    
    # Activity breakdown
    activity_breakdown = serializers.DictField()
    
    # Engagement metrics
    first_activity = serializers.DateTimeField()
    last_activity = serializers.DateTimeField()
    avg_daily_activities = serializers.FloatField()
    
    # Usage patterns
    most_active_hours = serializers.ListField()
    most_active_days = serializers.ListField()
    activity_streak = serializers.IntegerField()


class HourlyActivitySerializer(serializers.Serializer):
    """
    Serializer for hourly activity distribution
    """
    hour = serializers.IntegerField()
    activity_count = serializers.IntegerField()
    unique_users = serializers.IntegerField()


class DailyActivitySerializer(serializers.Serializer):
    """
    Serializer for daily activity trends
    """
    date = serializers.DateField()
    total_activities = serializers.IntegerField()
    unique_users = serializers.IntegerField()
    new_users = serializers.IntegerField()
    
    # Activity breakdown
    logins = serializers.IntegerField()
    book_activities = serializers.IntegerField()
    search_activities = serializers.IntegerField()


class PopularPagesSerializer(serializers.Serializer):
    """
    Serializer for popular pages/endpoints analytics
    """
    page_type = serializers.CharField()
    page_identifier = serializers.CharField()
    view_count = serializers.IntegerField()
    unique_visitors = serializers.IntegerField()
    avg_time_spent = serializers.FloatField()
    bounce_rate = serializers.FloatField()


class SystemUsageSerializer(serializers.Serializer):
    """
    Serializer for system usage analytics
    """
    # Overall metrics
    total_users = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    active_users_week = serializers.IntegerField()
    active_users_month = serializers.IntegerField()
    
    # Growth metrics
    user_growth_rate = serializers.FloatField()
    activity_growth_rate = serializers.FloatField()
    engagement_score = serializers.FloatField()
    
    # Usage patterns
    peak_usage_hour = serializers.IntegerField()
    peak_usage_day = serializers.CharField()
    average_session_length = serializers.FloatField()
    
    # Feature usage
    feature_usage = serializers.DictField()
    most_used_features = serializers.ListField()


class SecurityAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for security-focused analytics
    """
    # Failed login attempts
    failed_logins_today = serializers.IntegerField()
    failed_logins_week = serializers.IntegerField()
    suspicious_ips = serializers.ListField()
    
    # Geographic analysis
    login_locations = serializers.ListField()
    unusual_locations = serializers.ListField()
    
    # Device/browser analysis
    new_devices = serializers.IntegerField()
    unusual_user_agents = serializers.ListField()
    
    # Activity patterns
    after_hours_activity = serializers.IntegerField()
    bulk_operations = serializers.ListField()
    rapid_fire_requests = serializers.ListField()


class RealTimeActivitySerializer(serializers.Serializer):
    """
    Serializer for real-time activity monitoring
    """
    # Current active users
    current_active_users = serializers.IntegerField()
    users_online_now = serializers.ListField()
    
    # Recent activities (last 5 minutes)
    recent_activities = ActivityLogSerializer(many=True)
    
    # Live metrics
    activities_per_minute = serializers.FloatField()
    most_active_feature = serializers.CharField()
    system_load = serializers.FloatField()
    
    # Alerts
    unusual_activity_detected = serializers.BooleanField()
    system_alerts = serializers.ListField() 