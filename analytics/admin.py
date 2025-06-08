import json
from django.contrib import admin, messages
from django.db.models import Count, Avg, Q, F, Sum
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import JsonResponse
from django.contrib.admin import SimpleListFilter
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from django.utils.translation import gettext_lazy as _
from import_export import resources
from import_export.admin import ExportMixin
from rangefilter.filters import DateRangeFilter

from .models import ActivityLog, BookPopularity, CustomReport, SystemStatistics, ActivityType, ReportType

class ActivityTypeFilter(SimpleListFilter):
    title = _('Activity Type')
    parameter_name = 'activity_type'

    def lookups(self, request, model_admin):
        return ActivityType.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(activity_type=self.value())
        return queryset


class ActivityLogResource(resources.ModelResource):
    class Meta:
        model = ActivityLog
        fields = ('id', 'user__username', 'activity_type', 'details', 'ip_address', 'timestamp')
        export_order = fields


@admin.register(ActivityLog)
class ActivityLogAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = ActivityLogResource
    list_display = ('user', 'activity_type_display', 'timestamp', 'ip_address', 'details_short')
    list_filter = (
        ActivityTypeFilter,
        ('timestamp', DateRangeFilter),
        'ip_address',
    )
    search_fields = (
        'user__username',
        'user__email',
        'ip_address',
        'details',
    )
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp', 'details_formatted')
    ordering = ('-timestamp',)
    list_per_page = 50
    list_select_related = ('user',)
    actions = ['export_as_csv', 'export_as_json']
    fieldsets = (
        (None, {
            'fields': ('user', 'activity_type', 'timestamp')
        }),
        ('Details', {
            'fields': ('details_formatted', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )

    def activity_type_display(self, obj):
        return dict(ActivityType.choices).get(obj.activity_type, obj.activity_type)
    activity_type_display.short_description = 'Activity Type'
    activity_type_display.admin_order_field = 'activity_type'

    def details_short(self, obj):
        if obj.details:
            return str(obj.details)[:50] + '...' if len(str(obj.details)) > 50 else str(obj.details)
        return ''
    details_short.short_description = 'Details'

    def details_formatted(self, obj):
        if not obj.details:
            return '-'
        if isinstance(obj.details, dict):
            return format_html('<pre>{}</pre>', json.dumps(obj.details, indent=2, ensure_ascii=False))
        return str(obj.details)
    details_formatted.short_description = 'Details (Formatted)'

class BookPopularityResource(resources.ModelResource):
    class Meta:
        model = BookPopularity
        fields = (
            'book__title', 'book__authors__name', 'popularity_score', 
            'total_views', 'total_borrows', 'average_rating',
            'search_appearances', 'search_clicks', 'total_ratings',
            'total_reservations', 'current_reservations'
        )
        export_order = fields


class PopularityScoreFilter(SimpleListFilter):
    title = _('Popularity Score')
    parameter_name = 'popularity_score'

    def lookups(self, request, model_admin):
        return (
            ('high', _('High (≥ 8.0)')),
            ('medium', _('Medium (4.0 - 7.9)')),
            ('low', _('Low (≤ 3.9)')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'high':
            return queryset.filter(popularity_score__gte=8.0)
        if self.value() == 'medium':
            return queryset.filter(popularity_score__gte=4.0, popularity_score__lt=8.0)
        if self.value() == 'low':
            return queryset.filter(popularity_score__lt=4.0)
        return queryset


@admin.register(BookPopularity)
class BookPopularityAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = BookPopularityResource
    list_display = (
        'book_title', 'author', 'popularity_score_bar', 'total_views', 
        'total_borrows', 'average_rating_display', 'last_updated_short'
    )
    list_filter = (
        PopularityScoreFilter,
        ('last_updated', DateRangeFilter),
        ('last_viewed', DateRangeFilter),
        ('last_borrowed', DateRangeFilter),
    )
    search_fields = (
        'book__title',
        'book__authors__name',
        'book__isbn',
    )
    readonly_fields = (
        'popularity_score', 'total_views', 'total_borrows', 'average_rating',
        'last_updated', 'last_viewed', 'last_borrowed', 'popularity_details'
    )
    ordering = ('-popularity_score',)
    list_per_page = 30
    actions = ['update_popularity_scores', 'export_as_csv', 'export_as_json']
    
    fieldsets = (
        (None, {
            'fields': ('book', 'popularity_score', 'popularity_details')
        }),
        ('Views', {
            'fields': ('total_views', 'daily_views', 'weekly_views', 'monthly_views'),
            'classes': ('collapse',)
        }),
        ('Borrows', {
            'fields': ('total_borrows', 'monthly_borrows', 'yearly_borrows'),
            'classes': ('collapse',)
        }),
        ('Search & Ratings', {
            'fields': ('search_appearances', 'search_clicks', 'average_rating', 'total_ratings'),
            'classes': ('collapse',)
        }),
        ('Reservations', {
            'fields': ('total_reservations', 'current_reservations'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('last_updated', 'last_viewed', 'last_borrowed'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with prefetch_related for ManyToMany fields"""
        return super().get_queryset(request).select_related('book').prefetch_related('book__authors')

    def book_title(self, obj):
        return obj.book.title
    book_title.short_description = 'Book Title'
    book_title.admin_order_field = 'book__title'

    def author(self, obj):
        authors = obj.book.authors.all()
        if authors:
            return ", ".join([author.name for author in authors])
        return "No authors"
    author.short_description = 'Author'
    author.admin_order_field = 'book__authors__name'

    def average_rating_display(self, obj):
        if obj.average_rating:
            return f"{obj.average_rating:.1f} ({obj.total_ratings} ratings)"
        return 'No ratings'
    average_rating_display.short_description = 'Rating'
    average_rating_display.admin_order_field = 'average_rating'

    def last_updated_short(self, obj):
        if obj.last_updated:
            return obj.last_updated.strftime('%Y-%m-%d')
        return 'Never'
    last_updated_short.short_description = 'Last Updated'
    last_updated_short.admin_order_field = 'last_updated'

    def popularity_score_bar(self, obj):
        if obj.popularity_score is None:
            return 'N/A'
        
        # Convert to float to ensure proper formatting
        score = float(obj.popularity_score)
        width = min(100, int(score * 10))
        
        color = (
            '#4CAF50' if score >= 7.0
            else '#FFC107' if score >= 4.0
            else '#F44336'
        )
        
        # Format score as string to avoid format issues
        score_str = f"{score:.1f}"
        
        return format_html(
            '<div style="background: #eee; width: 100px; height: 20px; border-radius: 3px;">'
            '<div style="background: {}; width: {}%; height: 100%; border-radius: 3px; '
            'display: flex; align-items: center; justify-content: center; color: white; '
            'font-weight: bold; font-size: 12px;">{}</div></div>',
            color, width, score_str
        )
    popularity_score_bar.short_description = 'Popularity'
    popularity_score_bar.admin_order_field = 'popularity_score'

    def popularity_details(self, obj):
        details = []
        if obj.popularity_score >= 8.0:
            details.append("This book is very popular with our users.")
        elif obj.popularity_score >= 5.0:
            details.append("This book has average popularity.")
        else:
            details.append("This book has below average popularity.")

        if obj.total_views > 1000:
            details.append(f"It has been viewed {obj.total_views:,} times.")
        if obj.total_borrows > 100:
            details.append(f"It has been borrowed {obj.total_borrows:,} times.")
        if obj.average_rating and obj.average_rating >= 4.0:
            details.append(f"Users have given it a high average rating of {obj.average_rating:.1f}.")
        
        return format_html('<br>'.join(details)) if details else 'No details available.'
    popularity_details.short_description = 'Popularity Analysis'

    @admin.action(description='Update popularity scores for selected books')
    def update_popularity_scores(self, request, queryset):
        updated = 0
        for book_pop in queryset:
            book_pop.calculate_popularity_score()
            book_pop.save()
            updated += 1
        self.message_user(
            request,
            f'Successfully updated popularity scores for {updated} books.',
            messages.SUCCESS
        )

class ReportTypeFilter(SimpleListFilter):
    title = _('Report Type')
    parameter_name = 'report_type'

    def lookups(self, request, model_admin):
        return ReportType.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(report_type=self.value())
        return queryset


class CustomReportResource(resources.ModelResource):
    class Meta:
        model = CustomReport
        fields = (
            'name', 'report_type', 'created_by__username', 'created_at', 
            'is_public', 'is_scheduled', 'schedule_frequency', 'last_generated'
        )
        export_order = fields


@admin.register(CustomReport)
class CustomReportAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = CustomReportResource
    list_display = (
        'name', 'report_type_display', 'created_by_link', 'created_at_short',
        'is_public_display', 'is_scheduled_display', 'actions_column'
    )
    list_filter = (
        ReportTypeFilter,
        'is_public',
        'is_scheduled',
        ('created_at', DateRangeFilter),
        ('last_generated', DateRangeFilter),
    )
    search_fields = (
        'name',
        'description',
        'created_by__username',
        'created_by__email',
    )
    readonly_fields = (
        'created_at', 'updated_at', 'last_generated', 'created_by',
        'parameters_formatted', 'columns_formatted', 'data_preview'
    )
    ordering = ('-created_at',)
    list_per_page = 25
    list_select_related = ('created_by',)
    actions = ['generate_reports', 'toggle_public', 'toggle_scheduled', 'export_as_csv', 'export_as_json']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'report_type', 'created_by', 'is_public')
        }),
        ('Schedule', {
            'fields': ('is_scheduled', 'schedule_frequency', 'start_date', 'end_date'),
            'classes': ('collapse',)
        }),
        ('Content', {
            'fields': ('parameters_formatted', 'columns_formatted', 'data_preview'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'last_generated'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(Q(created_by=request.user) | Q(is_public=True))
        return qs

    def get_list_display_links(self, request, list_display):
        return ['name']

    def report_type_display(self, obj):
        return dict(ReportType.choices).get(obj.report_type, obj.report_type)
    report_type_display.short_description = 'Type'
    report_type_display.admin_order_field = 'report_type'

    def created_by_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.created_by.id])
        return format_html('<a href="{}">{}</a>', url, obj.created_by.username)
    created_by_link.short_description = 'Created By'
    created_by_link.admin_order_field = 'created_by__username'

    def created_at_short(self, obj):
        return obj.created_at.strftime('%Y-%m-%d')
    created_at_short.short_description = 'Created'
    created_at_short.admin_order_field = 'created_at'

    def is_public_display(self, obj):
        return '✅' if obj.is_public else '❌'
    is_public_display.short_description = 'Public'
    is_public_display.boolean = True

    def is_scheduled_display(self, obj):
        return '✅' if obj.is_scheduled else '❌'
    is_scheduled_display.short_description = 'Scheduled'
    is_scheduled_display.boolean = True

    def actions_column(self, obj):
        buttons = []
        url = reverse('admin:analytics_customreport_change', args=[obj.id])
        buttons.append(f'<a href="{url}" class="button">Edit</a>')
        
        generate_url = reverse('admin:analytics_customreport_generate', args=[obj.id])
        buttons.append(f'<a href="{generate_url}" class="button">Generate</a>')
        
        if obj.is_scheduled:
            toggle_url = reverse('admin:analytics_customreport_toggle_schedule', args=[obj.id])
            buttons.append(f'<a href="{toggle_url}" class="button">Disable Schedule</a>')
        else:
            toggle_url = reverse('admin:analytics_customreport_toggle_schedule', args=[obj.id])
            buttons.append(f'<a href="{toggle_url}" class="button">Enable Schedule</a>')
        
        return format_html(' '.join(buttons))
    actions_column.short_description = 'Actions'
    actions_column.allow_tags = True

    def parameters_formatted(self, obj):
        if not obj.parameters:
            return 'No parameters'
        return format_html('<pre>{}</pre>', json.dumps(obj.parameters, indent=2, ensure_ascii=False))
    parameters_formatted.short_description = 'Parameters'

    def columns_formatted(self, obj):
        if not obj.columns:
            return 'No columns defined'
        return format_html('<pre>{}</pre>', json.dumps(obj.columns, indent=2, ensure_ascii=False))
    columns_formatted.short_description = 'Columns'

    def data_preview(self, obj):
        if not obj.data:
            return 'No data available. Generate the report first.'
        
        # Show a preview of the data (first 5 rows)
        preview = {}
        for key in list(obj.data.keys())[:5]:
            preview[key] = obj.data[key]
        
        return format_html('<pre>{}</pre>', json.dumps(preview, indent=2, ensure_ascii=False))
    data_preview.short_description = 'Data Preview (First 5 Rows)'

    @admin.action(description='Generate selected reports')
    def generate_reports(self, request, queryset):
        generated = 0
        for report in queryset:
            try:
                report.generate_data()
                report.save()
                generated += 1
            except Exception as e:
                self.message_user(
                    request,
                    f'Error generating report "{report.name}": {str(e)}',
                    messages.ERROR
                )
        
        if generated > 0:
            self.message_user(
                request,
                f'Successfully generated {generated} reports.',
                messages.SUCCESS
            )

    @admin.action(description='Toggle public status of selected reports')
    def toggle_public(self, request, queryset):
        for report in queryset:
            report.is_public = not report.is_public
            report.save()
        
        self.message_user(
            request,
            f'Toggled public status for {queryset.count()} reports.',
            messages.SUCCESS
        )

    @admin.action(description='Toggle schedule status of selected reports')
    def toggle_scheduled(self, request, queryset):
        for report in queryset:
            report.is_scheduled = not report.is_scheduled
            report.save()
        
        self.message_user(
            request,
            f'Toggled schedule status for {queryset.count()} reports.',
            messages.SUCCESS
        )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:report_id>/generate/',
                self.admin_site.admin_view(self.generate_report_view),
                name='analytics_customreport_generate',
            ),
            path(
                '<int:report_id>/toggle-schedule/',
                self.admin_site.admin_view(self.toggle_schedule_view),
                name='analytics_customreport_toggle_schedule',
            ),
        ]
        return custom_urls + urls
    
    def generate_report_view(self, request, report_id, *args, **kwargs):
        from django.shortcuts import redirect
        from django.contrib import messages
        
        try:
            report = CustomReport.objects.get(id=report_id)
            report.generate_data()
            report.save()
            messages.success(request, f'Successfully generated report: {report.name}')
        except CustomReport.DoesNotExist:
            messages.error(request, 'Report not found')
        except Exception as e:
            messages.error(request, f'Error generating report: {str(e)}')
        
        return redirect('admin:analytics_customreport_changelist')
    
    def toggle_schedule_view(self, request, report_id, *args, **kwargs):
        from django.shortcuts import redirect
        from django.contrib import messages
        
        try:
            report = CustomReport.objects.get(id=report_id)
            report.is_scheduled = not report.is_scheduled
            report.save()
            
            status = 'enabled' if report.is_scheduled else 'disabled'
            messages.success(request, f'Successfully {status} scheduling for report: {report.name}')
        except CustomReport.DoesNotExist:
            messages.error(request, 'Report not found')
        except Exception as e:
            messages.error(request, f'Error toggling schedule: {str(e)}')
        
        return redirect('admin:analytics_customreport_changelist')

class SystemStatisticsResource(resources.ModelResource):
    class Meta:
        model = SystemStatistics
        fields = (
            'date', 'total_users', 'active_users', 'new_users',
            'total_books', 'available_books', 'borrowed_books',
            'total_loans', 'total_returns', 'total_reservations',
            'total_searches', 'unique_search_terms', 'total_fines_collected',
            'outstanding_fines', 'average_response_time', 'error_rate'
        )
        export_order = fields


class CustomDateRangeFilter(admin.SimpleListFilter):
    title = _('Date Range')
    parameter_name = 'date_range'

    def lookups(self, request, model_admin):
        return (
            ('today', _('Today')),
            ('yesterday', _('Yesterday')),
            ('this_week', _('This Week')),
            ('last_week', _('Last Week')),
            ('this_month', _('This Month')),
            ('last_month', _('Last Month')),
            ('this_year', _('This Year')),
            ('last_year', _('Last Year')),
        )

    def queryset(self, request, queryset):
        today = timezone.now().date()
        
        if self.value() == 'today':
            return queryset.filter(date=today)
        if self.value() == 'yesterday':
            return queryset.filter(date=today - timezone.timedelta(days=1))
        if self.value() == 'this_week':
            start_week = today - timezone.timedelta(days=today.weekday())
            return queryset.filter(date__range=[start_week, today])
        if self.value() == 'last_week':
            end_last_week = today - timezone.timedelta(days=today.weekday() + 1)
            start_last_week = end_last_week - timezone.timedelta(days=6)
            return queryset.filter(date__range=[start_last_week, end_last_week])
        if self.value() == 'this_month':
            return queryset.filter(date__year=today.year, date__month=today.month)
        if self.value() == 'last_month':
            last_month = today.month - 1 if today.month > 1 else 12
            year = today.year if today.month > 1 else today.year - 1
            return queryset.filter(date__year=year, date__month=last_month)
        if self.value() == 'this_year':
            return queryset.filter(date__year=today.year)
        if self.value() == 'last_year':
            return queryset.filter(date__year=today.year - 1)
        return queryset


@admin.register(SystemStatistics)
class SystemStatisticsAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = SystemStatisticsResource
    list_display = (
        'date', 'users_summary', 'books_summary', 
        'activity_summary', 'performance_summary'
    )
    list_filter = (
        CustomDateRangeFilter,
        ('date', DateRangeFilter),
    )
    search_fields = ('date',)
    readonly_fields = (
        'date', 'total_users', 'active_users', 'new_users',
        'total_books', 'available_books', 'borrowed_books',
        'total_loans', 'total_returns', 'total_reservations',
        'total_searches', 'unique_search_terms', 'total_fines_collected',
        'outstanding_fines', 'average_response_time', 'error_rate',
        'created_at', 'updated_at', 'stats_summary'
    )
    ordering = ('-date',)
    list_per_page = 30
    actions = ['generate_daily_stats', 'export_as_csv', 'export_as_json']
    
    fieldsets = (
        (None, {
            'fields': ('date', 'stats_summary')
        }),
        ('Users', {
            'fields': (
                'total_users', 'active_users', 'new_users',
            ),
            'classes': ('collapse',)
        }),
        ('Books', {
            'fields': (
                'total_books', 'available_books', 'borrowed_books',
            ),
            'classes': ('collapse',)
        }),
        ('Activity', {
            'fields': (
                'total_loans', 'total_returns', 'total_reservations',
                'total_searches', 'unique_search_terms',
            ),
            'classes': ('collapse',)
        }),
        ('Financials', {
            'fields': (
                'total_fines_collected', 'outstanding_fines',
            ),
            'classes': ('collapse',)
        }),
        ('Performance', {
            'fields': (
                'average_response_time', 'error_rate',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def users_summary(self, obj):
        return format_html(
            '👥 <strong>{}</strong> total, <strong>{}</strong> active, <strong>{}</strong> new',
            obj.total_users, obj.active_users, obj.new_users
        )
    users_summary.short_description = 'Users'
    users_summary.admin_order_field = 'total_users'

    def books_summary(self, obj):
        return format_html(
            '📚 <strong>{}</strong> total, <strong>{}</strong> available, <strong>{}</strong> borrowed',
            obj.total_books, obj.available_books, obj.borrowed_books
        )
    books_summary.short_description = 'Books'
    books_summary.admin_order_field = 'total_books'

    def activity_summary(self, obj):
        return format_html(
            '📊 <strong>{}</strong> loans, <strong>{}</strong> returns, <strong>{}</strong> reservations',
            obj.total_loans, obj.total_returns, obj.total_reservations
        )
    activity_summary.short_description = 'Activity'
    activity_summary.admin_order_field = 'total_loans'

    def performance_summary(self, obj):
        response_color = (
            '#4CAF50' if obj.average_response_time < 500
            else '#FFC107' if obj.average_response_time < 1000
            else '#F44336'
        )
        error_color = (
            '#4CAF50' if obj.error_rate < 1
            else '#FFC107' if obj.error_rate < 5
            else '#F44336'
        )
        
        # Convert values to proper types to avoid format issues
        response_time = float(obj.average_response_time or 0)
        error_rate = float(obj.error_rate or 0)
        fines_collected = float(obj.total_fines_collected or 0)
        
        return format_html(
            '⚡ <span style="color: {};">{:.0f}ms</span> • '
            '⚠️ <span style="color: {};">{:.1f}%</span> • '
            '💰 ${:.2f} collected',
            response_color, response_time,
            error_color, error_rate,
            fines_collected
        )
    performance_summary.short_description = 'Performance'
    performance_summary.admin_order_field = 'average_response_time'

    def stats_summary(self, obj):
        summary = []
        
        # User growth
        prev_day = SystemStatistics.objects.filter(date__lt=obj.date).order_by('-date').first()
        if prev_day:
            user_growth = obj.total_users - prev_day.total_users
            if user_growth > 0:
                summary.append(f"📈 User growth: +{user_growth} from previous day")
            elif user_growth < 0:
                summary.append(f"📉 User decline: {user_growth} from previous day")
        
        # Book availability
        if obj.available_books == 0:
            summary.append("⚠️ No books available for borrowing!")
        elif obj.available_books / obj.total_books < 0.1:
            summary.append("⚠️ Low book availability (less than 10% in stock)")
        
        # Fines
        if obj.outstanding_fines and obj.outstanding_fines > 1000:
            summary.append(f"💰 High outstanding fines: ${obj.outstanding_fines:.2f}")
        
        # Performance
        if obj.average_response_time > 1000:
            summary.append(f"🐌 Slow response time: {obj.average_response_time:.0f}ms")
        if obj.error_rate > 5:
            summary.append(f"❌ High error rate: {obj.error_rate:.1f}%")
        
        if not summary:
            return "✅ No significant issues detected for this period."
        
        return format_html('<br>'.join(summary))
    stats_summary.short_description = 'Summary'

    @admin.action(description='Generate daily statistics for yesterday')
    def generate_daily_stats(self, request, queryset):
        from datetime import date, timedelta
        from django.db.models import Count, Sum, Avg, Q, F
        from django.utils import timezone
        
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Check if stats already exist for yesterday
        if SystemStatistics.objects.filter(date=yesterday).exists():
            self.message_user(
                request,
                f'Statistics for {yesterday} already exist. Skipping...',
                messages.WARNING
            )
            return
        
        try:
            from books.models import Book
            from accounts.models import User
            from loans.models import Loan, Reservation
            
            # Get user statistics
            total_users = User.objects.count()
            yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))
            yesterday_end = yesterday_start + timedelta(days=1)
            active_users = User.objects.filter(
                last_login__date=yesterday
            ).count()
            new_users = User.objects.filter(
                date_joined__range=(yesterday_start, yesterday_end)
            ).count()
            
            # Get book statistics
            total_books = Book.objects.count()
            available_books = Book.objects.filter(available_copies__gt=0).count()
            borrowed_books = Loan.objects.filter(
                returned_date__isnull=True
            ).count()
            
            # Get activity statistics
            loans_yesterday = Loan.objects.filter(
                borrowed_date__date=yesterday
            ).count()
            returns_yesterday = Loan.objects.filter(
                returned_date__date=yesterday
            ).count()
            reservations_yesterday = Reservation.objects.filter(
                reserved_date__date=yesterday
            ).count()
            
            # Create the statistics record
            stats = SystemStatistics.objects.create(
                date=yesterday,
                total_users=total_users,
                active_users=active_users,
                new_users=new_users,
                total_books=total_books,
                available_books=available_books,
                borrowed_books=borrowed_books,
                total_loans=loans_yesterday,
                total_returns=returns_yesterday,
                total_reservations=reservations_yesterday,
                # These would be calculated based on your tracking
                total_searches=0,
                unique_search_terms=0,
                total_fines_collected=0,
                outstanding_fines=0,
                average_response_time=0,
                error_rate=0,
            )
            
            self.message_user(
                request,
                f'Successfully generated statistics for {yesterday}.',
                messages.SUCCESS
            )
            
        except Exception as e:
            self.message_user(
                request,
                f'Error generating statistics: {str(e)}',
                messages.ERROR
            )

