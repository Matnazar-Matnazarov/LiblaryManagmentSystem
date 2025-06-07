"""
Professional Analytics Models

This module contains models for comprehensive library analytics:
- User activity tracking
- Book popularity metrics
- System usage statistics
- Custom report generation
- Performance monitoring
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
import json


class ActivityType(models.TextChoices):
    """User activity types"""
    LOGIN = 'login', 'Login'
    LOGOUT = 'logout', 'Logout'
    BOOK_SEARCH = 'book_search', 'Book Search'
    BOOK_VIEW = 'book_view', 'Book View'
    BOOK_BORROW = 'book_borrow', 'Book Borrow'
    BOOK_RETURN = 'book_return', 'Book Return'
    BOOK_RENEW = 'book_renew', 'Book Renew'
    RESERVATION_CREATE = 'reservation_create', 'Reservation Create'
    RESERVATION_CANCEL = 'reservation_cancel', 'Reservation Cancel'
    FINE_PAYMENT = 'fine_payment', 'Fine Payment'
    PROFILE_UPDATE = 'profile_update', 'Profile Update'


class ReportType(models.TextChoices):
    """Report types"""
    DAILY = 'daily', 'Daily Report'
    WEEKLY = 'weekly', 'Weekly Report'
    MONTHLY = 'monthly', 'Monthly Report'
    YEARLY = 'yearly', 'Yearly Report'
    CUSTOM = 'custom', 'Custom Report'


class ActivityLogQuerySet(models.QuerySet):
    """Custom queryset for ActivityLog"""
    
    def by_user(self, user):
        """Filter by user"""
        return self.filter(user=user)
    
    def by_activity_type(self, activity_type):
        """Filter by activity type"""
        return self.filter(activity_type=activity_type)
    
    def in_date_range(self, start_date, end_date):
        """Filter by date range"""
        return self.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
    
    def today(self):
        """Filter today's activities"""
        return self.filter(timestamp__date=timezone.now().date())
    
    def this_week(self):
        """Filter this week's activities"""
        start_week = timezone.now().date() - timedelta(days=7)
        return self.filter(timestamp__date__gte=start_week)
    
    def this_month(self):
        """Filter this month's activities"""
        start_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self.filter(timestamp__gte=start_month)


class ActivityLogManager(models.Manager):
    """Custom manager for ActivityLog"""
    
    def get_queryset(self):
        return ActivityLogQuerySet(self.model, using=self._db)
    
    def by_user(self, user):
        return self.get_queryset().by_user(user)
    
    def by_activity_type(self, activity_type):
        return self.get_queryset().by_activity_type(activity_type)
    
    def today(self):
        return self.get_queryset().today()
    
    def this_week(self):
        return self.get_queryset().this_week()
    
    def this_month(self):
        return self.get_queryset().this_month()


class ActivityLog(models.Model):
    """
    Comprehensive user activity tracking
    
    Tracks all user interactions with the system for:
    - Usage analytics
    - User behavior analysis
    - Security monitoring
    - Performance optimization
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activities',
        null=True,
        blank=True,
        help_text="User who performed the activity (null for anonymous)"
    )
    
    activity_type = models.CharField(
        max_length=50,
        choices=ActivityType.choices,
        help_text="Type of activity performed"
    )
    
    # Activity details
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the activity"
    )
    
    # Related objects (polymorphic references)
    object_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of object involved (book, user, etc.)"
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID of the related object"
    )
    
    # Technical details
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the user"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string"
    )
    
    # Additional data (JSON field for flexible storage)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional activity metadata"
    )
    
    # Timestamps
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="When the activity occurred"
    )
    
    objects = ActivityLogManager()
    
    class Meta:
        db_table = 'activity_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['object_type', 'object_id']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonymous'
        return f"{user_str} - {self.get_activity_type_display()} at {self.timestamp}"
    
    @classmethod
    def log_activity(cls, user, activity_type, description='', object_type='', object_id=None, 
                     ip_address=None, user_agent='', metadata=None):
        """Convenience method to log an activity"""
        return cls.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            object_type=object_type,
            object_id=object_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )


class BookPopularityQuerySet(models.QuerySet):
    """Custom queryset for BookPopularity"""
    
    def trending(self):
        """Get trending books (high recent activity)"""
        return self.filter(
            last_updated__gte=timezone.now() - timedelta(days=7)
        ).order_by('-weekly_views', '-monthly_borrows')
    
    def most_viewed(self):
        """Get most viewed books"""
        return self.order_by('-total_views')
    
    def most_borrowed(self):
        """Get most borrowed books"""
        return self.order_by('-total_borrows')


class BookPopularityManager(models.Manager):
    """Custom manager for BookPopularity"""
    
    def get_queryset(self):
        return BookPopularityQuerySet(self.model, using=self._db)
    
    def trending(self):
        return self.get_queryset().trending()
    
    def most_viewed(self):
        return self.get_queryset().most_viewed()
    
    def most_borrowed(self):
        return self.get_queryset().most_borrowed()


class BookPopularity(models.Model):
    """
    Book popularity and engagement metrics
    
    Tracks book popularity based on:
    - View counts
    - Borrow frequency
    - Search appearances
    - User ratings
    """
    
    book = models.OneToOneField(
        'books.Book',
        on_delete=models.CASCADE,
        related_name='popularity',
        help_text="Book being tracked"
    )
    
    # View metrics
    total_views = models.PositiveIntegerField(
        default=0,
        help_text="Total times book was viewed"
    )
    daily_views = models.PositiveIntegerField(
        default=0,
        help_text="Views in the last 24 hours"
    )
    weekly_views = models.PositiveIntegerField(
        default=0,
        help_text="Views in the last 7 days"
    )
    monthly_views = models.PositiveIntegerField(
        default=0,
        help_text="Views in the last 30 days"
    )
    
    # Borrow metrics
    total_borrows = models.PositiveIntegerField(
        default=0,
        help_text="Total times book was borrowed"
    )
    monthly_borrows = models.PositiveIntegerField(
        default=0,
        help_text="Borrows in the last 30 days"
    )
    yearly_borrows = models.PositiveIntegerField(
        default=0,
        help_text="Borrows in the last 365 days"
    )
    
    # Search metrics
    search_appearances = models.PositiveIntegerField(
        default=0,
        help_text="Times book appeared in search results"
    )
    search_clicks = models.PositiveIntegerField(
        default=0,
        help_text="Times book was clicked from search results"
    )
    
    # Engagement metrics
    average_rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Average user rating"
    )
    total_ratings = models.PositiveIntegerField(
        default=0,
        help_text="Total number of ratings"
    )
    
    # Reservation metrics
    total_reservations = models.PositiveIntegerField(
        default=0,
        help_text="Total times book was reserved"
    )
    current_reservations = models.PositiveIntegerField(
        default=0,
        help_text="Current active reservations"
    )
    
    # Calculated metrics
    popularity_score = models.FloatField(
        default=0.0,
        help_text="Calculated popularity score"
    )
    
    # Timestamps
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="When metrics were last updated"
    )
    last_viewed = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When book was last viewed"
    )
    last_borrowed = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When book was last borrowed"
    )
    
    objects = BookPopularityManager()
    
    class Meta:
        db_table = 'book_popularity'
        verbose_name_plural = 'Book Popularity'
        indexes = [
            models.Index(fields=['-popularity_score']),
            models.Index(fields=['-total_views']),
            models.Index(fields=['-total_borrows']),
            models.Index(fields=['-weekly_views']),
            models.Index(fields=['-monthly_borrows']),
        ]
    
    def __str__(self):
        return f"{self.book.title} - Score: {self.popularity_score}"
    
    def calculate_popularity_score(self):
        """Calculate popularity score based on various metrics"""
        # Weighted scoring system
        view_score = min(self.weekly_views * 1, 100)
        borrow_score = min(self.monthly_borrows * 10, 200)
        rating_score = self.average_rating * 20 if self.total_ratings > 0 else 0
        reservation_score = min(self.current_reservations * 15, 75)
        search_score = min((self.search_clicks / max(self.search_appearances, 1)) * 50, 50)
        
        self.popularity_score = view_score + borrow_score + rating_score + reservation_score + search_score
        return self.popularity_score
    
    def increment_views(self):
        """Increment view counters"""
        self.total_views += 1
        self.daily_views += 1
        self.weekly_views += 1
        self.monthly_views += 1
        self.last_viewed = timezone.now()
        self.calculate_popularity_score()
        self.save()
    
    def increment_borrows(self):
        """Increment borrow counters"""
        self.total_borrows += 1
        self.monthly_borrows += 1
        self.yearly_borrows += 1
        self.last_borrowed = timezone.now()
        self.calculate_popularity_score()
        self.save()


class SystemStatistics(models.Model):
    """
    System-wide statistics and metrics
    
    Stores daily aggregated statistics for:
    - System performance monitoring
    - Trend analysis
    - Reporting
    """
    
    date = models.DateField(
        unique=True,
        help_text="Date for which statistics are calculated"
    )
    
    # User statistics
    total_users = models.PositiveIntegerField(
        default=0,
        help_text="Total registered users"
    )
    active_users = models.PositiveIntegerField(
        default=0,
        help_text="Users active today"
    )
    new_users = models.PositiveIntegerField(
        default=0,
        help_text="New users registered today"
    )
    
    # Book statistics
    total_books = models.PositiveIntegerField(
        default=0,
        help_text="Total books in catalog"
    )
    available_books = models.PositiveIntegerField(
        default=0,
        help_text="Available books for borrowing"
    )
    borrowed_books = models.PositiveIntegerField(
        default=0,
        help_text="Books currently borrowed"
    )
    
    # Activity statistics
    total_loans = models.PositiveIntegerField(
        default=0,
        help_text="Total loans created today"
    )
    total_returns = models.PositiveIntegerField(
        default=0,
        help_text="Total books returned today"
    )
    total_reservations = models.PositiveIntegerField(
        default=0,
        help_text="Total reservations created today"
    )
    
    # Search statistics
    total_searches = models.PositiveIntegerField(
        default=0,
        help_text="Total searches performed today"
    )
    unique_search_terms = models.PositiveIntegerField(
        default=0,
        help_text="Unique search terms used today"
    )
    
    # Financial statistics
    total_fines_collected = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Total fines collected today"
    )
    outstanding_fines = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Outstanding fines as of today"
    )
    
    # System performance
    average_response_time = models.FloatField(
        default=0.0,
        help_text="Average API response time in milliseconds"
    )
    error_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Error rate percentage"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_statistics'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date']),
        ]
    
    def __str__(self):
        return f"Statistics for {self.date}"


class CustomReportQuerySet(models.QuerySet):
    """Custom queryset for CustomReport"""
    
    def by_type(self, report_type):
        """Filter by report type"""
        return self.filter(report_type=report_type)
    
    def by_creator(self, user):
        """Filter by creator"""
        return self.filter(created_by=user)
    
    def public(self):
        """Get public reports"""
        return self.filter(is_public=True)


class CustomReportManager(models.Manager):
    """Custom manager for CustomReport"""
    
    def get_queryset(self):
        return CustomReportQuerySet(self.model, using=self._db)
    
    def by_type(self, report_type):
        return self.get_queryset().by_type(report_type)
    
    def public(self):
        return self.get_queryset().public()


class CustomReport(models.Model):
    """
    Custom report generation and storage
    
    Allows users to create and save custom reports with:
    - Flexible parameters
    - Scheduled generation
    - Export capabilities
    """
    
    name = models.CharField(
        max_length=200,
        help_text="Report name"
    )
    description = models.TextField(
        blank=True,
        help_text="Report description"
    )
    
    report_type = models.CharField(
        max_length=20,
        choices=ReportType.choices,
        default=ReportType.CUSTOM,
        help_text="Type of report"
    )
    
    # Report configuration
    parameters = models.JSONField(
        default=dict,
        help_text="Report parameters and filters"
    )
    columns = models.JSONField(
        default=list,
        help_text="Columns to include in report"
    )
    
    # Date range
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Report start date"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Report end date"
    )
    
    # Generated data
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Generated report data"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='custom_reports',
        help_text="User who created the report"
    )
    
    is_public = models.BooleanField(
        default=False,
        help_text="Whether report is visible to other users"
    )
    
    # Scheduling
    is_scheduled = models.BooleanField(
        default=False,
        help_text="Whether report is automatically generated"
    )
    schedule_frequency = models.CharField(
        max_length=20,
        choices=ReportType.choices,
        blank=True,
        help_text="How often to generate report"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_generated = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When report was last generated"
    )
    
    objects = CustomReportManager()
    
    class Meta:
        db_table = 'custom_reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_by', '-created_at']),
            models.Index(fields=['report_type']),
            models.Index(fields=['is_public']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"
    
    def generate_data(self):
        """Generate report data based on parameters"""
        # This method would contain the logic to generate report data
        # Implementation depends on specific requirements
        self.last_generated = timezone.now()
        self.save()
        return self.data
