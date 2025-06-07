"""
Custom Report Serializers

Professional serializers for custom report management with:
- Report creation and configuration
- Report generation parameters
- Export functionality
- Scheduled reports
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta, date

from ..models import CustomReport, ReportType
from accounts.serializers import UserSerializer


class CustomReportSerializer(serializers.ModelSerializer):
    """
    Basic custom report serializer for list views
    """
    created_by = UserSerializer(read_only=True)
    report_type_display = serializers.CharField(
        source='get_report_type_display',
        read_only=True
    )
    
    class Meta:
        model = CustomReport
        fields = [
            'id', 'name', 'description', 'report_type', 'report_type_display',
            'start_date', 'end_date', 'created_by', 'is_public', 'is_scheduled',
            'created_at', 'last_generated'
        ]
        read_only_fields = ['id', 'created_at', 'last_generated']


class CustomReportDetailSerializer(CustomReportSerializer):
    """
    Detailed custom report serializer with full configuration
    """
    parameters = serializers.JSONField()
    columns = serializers.JSONField()
    data = serializers.JSONField(read_only=True)
    schedule_frequency_display = serializers.CharField(
        source='get_schedule_frequency_display',
        read_only=True
    )
    
    class Meta(CustomReportSerializer.Meta):
        fields = CustomReportSerializer.Meta.fields + [
            'parameters', 'columns', 'data', 'schedule_frequency',
            'schedule_frequency_display', 'updated_at'
        ]


class CustomReportCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating custom reports
    """
    class Meta:
        model = CustomReport
        fields = [
            'name', 'description', 'report_type', 'parameters', 'columns',
            'start_date', 'end_date', 'is_public', 'is_scheduled',
            'schedule_frequency'
        ]
    
    def validate_parameters(self, value):
        """Validate report parameters"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Parameters must be a valid JSON object.")
        return value
    
    def validate_columns(self, value):
        """Validate report columns"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Columns must be a list.")
        
        if len(value) == 0:
            raise serializers.ValidationError("At least one column must be specified.")
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError("Start date must be before end date.")
            
            # Check reasonable date range
            if (end_date - start_date).days > 365:
                raise serializers.ValidationError("Date range cannot exceed 365 days.")
        
        is_scheduled = attrs.get('is_scheduled', False)
        schedule_frequency = attrs.get('schedule_frequency')
        
        if is_scheduled and not schedule_frequency:
            raise serializers.ValidationError("Schedule frequency is required for scheduled reports.")
        
        return attrs
    
    def create(self, validated_data):
        """Create custom report with proper user assignment"""
        user = self.context['request'].user
        validated_data['created_by'] = user
        return super().create(validated_data)


class ReportGenerationSerializer(serializers.Serializer):
    """
    Serializer for report generation requests
    """
    report_id = serializers.IntegerField()
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    filters = serializers.JSONField(required=False, default=dict)
    format = serializers.ChoiceField(
        choices=[
            ('json', 'JSON'),
            ('csv', 'CSV'),
            ('excel', 'Excel'),
            ('pdf', 'PDF')
        ],
        default='json'
    )
    
    def validate_report_id(self, value):
        """Validate report exists and user has access"""
        try:
            user = self.context['request'].user
            report = CustomReport.objects.get(id=value)
            
            # Check permissions
            if not report.is_public and report.created_by != user:
                if not user.has_perm('analytics.view_all_reports'):
                    raise serializers.ValidationError("Permission denied to access this report.")
            
            return value
        except CustomReport.DoesNotExist:
            raise serializers.ValidationError("Report not found.")
    
    def validate(self, attrs):
        """Cross-field validation"""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date.")
        
        return attrs


class ReportExportSerializer(serializers.Serializer):
    """
    Serializer for report export configuration
    """
    report_id = serializers.IntegerField()
    format = serializers.ChoiceField(choices=[
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
        ('json', 'JSON')
    ])
    include_charts = serializers.BooleanField(default=False)
    include_summary = serializers.BooleanField(default=True)
    custom_filename = serializers.CharField(max_length=100, required=False)
    
    # Email options
    send_email = serializers.BooleanField(default=False)
    email_recipients = serializers.ListField(
        child=serializers.EmailField(),
        required=False
    )
    email_subject = serializers.CharField(max_length=200, required=False)
    email_message = serializers.CharField(required=False)
    
    def validate(self, attrs):
        """Validate export configuration"""
        send_email = attrs.get('send_email', False)
        email_recipients = attrs.get('email_recipients', [])
        
        if send_email and not email_recipients:
            raise serializers.ValidationError("Email recipients are required when sending email.")
        
        format_type = attrs.get('format')
        include_charts = attrs.get('include_charts', False)
        
        if include_charts and format_type not in ['pdf', 'excel']:
            raise serializers.ValidationError("Charts can only be included in PDF or Excel format.")
        
        return attrs


class ReportScheduleSerializer(serializers.Serializer):
    """
    Serializer for managing report schedules
    """
    report_id = serializers.IntegerField()
    is_active = serializers.BooleanField(default=True)
    frequency = serializers.ChoiceField(choices=ReportType.choices)
    
    # Schedule timing
    hour = serializers.IntegerField(min_value=0, max_value=23, default=9)
    day_of_week = serializers.IntegerField(min_value=1, max_value=7, required=False)  # For weekly
    day_of_month = serializers.IntegerField(min_value=1, max_value=31, required=False)  # For monthly
    
    # Delivery options
    email_recipients = serializers.ListField(
        child=serializers.EmailField(),
        required=False
    )
    export_format = serializers.ChoiceField(
        choices=[('pdf', 'PDF'), ('excel', 'Excel'), ('csv', 'CSV')],
        default='pdf'
    )
    
    # Retention
    keep_last_n_reports = serializers.IntegerField(min_value=1, max_value=100, default=10)
    
    def validate(self, attrs):
        """Validate schedule configuration"""
        frequency = attrs.get('frequency')
        
        if frequency == ReportType.WEEKLY and 'day_of_week' not in attrs:
            raise serializers.ValidationError("Day of week is required for weekly reports.")
        
        if frequency == ReportType.MONTHLY and 'day_of_month' not in attrs:
            raise serializers.ValidationError("Day of month is required for monthly reports.")
        
        return attrs


class ReportTemplateSerializer(serializers.Serializer):
    """
    Serializer for report templates
    """
    name = serializers.CharField(max_length=200)
    description = serializers.CharField()
    category = serializers.CharField(max_length=50)
    
    # Template configuration
    default_parameters = serializers.JSONField()
    available_columns = serializers.ListField()
    default_columns = serializers.ListField()
    
    # Template metadata
    author = serializers.CharField(max_length=100)
    version = serializers.CharField(max_length=20)
    requirements = serializers.ListField(required=False)
    
    # Usage info
    usage_count = serializers.IntegerField(read_only=True)
    rating = serializers.FloatField(read_only=True)
    
    def validate_default_parameters(self, value):
        """Validate default parameters"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Default parameters must be a JSON object.")
        return value
    
    def validate_available_columns(self, value):
        """Validate available columns"""
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError("Available columns must be a non-empty list.")
        return value


class ReportAnalyticsSerializer(serializers.Serializer):
    """
    Serializer for report usage analytics
    """
    # Report performance
    total_reports = serializers.IntegerField()
    active_reports = serializers.IntegerField()
    scheduled_reports = serializers.IntegerField()
    public_reports = serializers.IntegerField()
    
    # Usage metrics
    total_generations = serializers.IntegerField()
    generations_this_month = serializers.IntegerField()
    avg_generation_time = serializers.FloatField()
    
    # Popular reports
    most_generated_reports = CustomReportSerializer(many=True)
    most_popular_templates = serializers.ListField()
    trending_report_types = serializers.ListField()
    
    # User behavior
    top_report_creators = serializers.ListField()
    avg_reports_per_user = serializers.FloatField()
    user_adoption_rate = serializers.FloatField()
    
    # Export analytics
    export_format_breakdown = serializers.ListField()
    email_delivery_rate = serializers.FloatField()
    download_vs_email_ratio = serializers.FloatField()
    
    # Performance metrics
    generation_success_rate = serializers.FloatField()
    avg_report_size = serializers.FloatField()
    peak_generation_hours = serializers.ListField()


class ReportInsightsSerializer(serializers.Serializer):
    """
    Serializer for automated report insights
    """
    report = CustomReportSerializer()
    
    # Data insights
    key_findings = serializers.ListField()
    trends_detected = serializers.ListField()
    anomalies = serializers.ListField()
    
    # Recommendations
    optimization_suggestions = serializers.ListField()
    data_quality_issues = serializers.ListField()
    improvement_opportunities = serializers.ListField()
    
    # Comparative analysis
    period_over_period_changes = serializers.ListField()
    benchmark_comparisons = serializers.ListField()
    
    # Action items
    recommended_actions = serializers.ListField()
    alert_conditions = serializers.ListField()
    follow_up_reports = serializers.ListField() 