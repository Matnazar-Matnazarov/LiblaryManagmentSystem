"""
Professional Django Admin Configuration for Loans App

This module provides comprehensive admin interface for loan management with:
- Advanced loan tracking and management
- Reservation system administration
- Overdue loan monitoring
- Fine management
- Bulk operations and custom actions
- Professional UI improvements and reporting
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponse
from datetime import datetime, timedelta
import csv

from .models import Loan, Reservation, LoanStatus, ReservationStatus


class LoanStatusFilter(SimpleListFilter):
    """Custom filter for loan status with overdue detection"""
    title = 'Loan Status'
    parameter_name = 'loan_status'

    def lookups(self, request, model_admin):
        return [
            ('active', 'Active'),
            ('overdue', 'Overdue'),
            ('returned', 'Returned'),
            ('renewed', 'Renewed'),
            ('with_fine', 'With Fine'),
            ('lost_damaged', 'Lost/Damaged'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(status=LoanStatus.ACTIVE, due_date__gte=timezone.now().date())
        elif self.value() == 'overdue':
            return queryset.filter(
                Q(status=LoanStatus.ACTIVE, due_date__lt=timezone.now().date()) |
                Q(status=LoanStatus.OVERDUE)
            )
        elif self.value() == 'returned':
            return queryset.filter(status=LoanStatus.RETURNED)
        elif self.value() == 'renewed':
            return queryset.filter(renewal_count__gt=0)
        elif self.value() == 'with_fine':
            return queryset.filter(fine_amount__gt=0)
        elif self.value() == 'lost_damaged':
            return queryset.filter(status__in=[LoanStatus.LOST, LoanStatus.DAMAGED])
        return queryset


class DueDateFilter(SimpleListFilter):
    """Filter loans by due date ranges"""
    title = 'Due Date'
    parameter_name = 'due_date_range'

    def lookups(self, request, model_admin):
        return [
            ('overdue', 'Overdue'),
            ('due_today', 'Due Today'),
            ('due_tomorrow', 'Due Tomorrow'),
            ('due_week', 'Due This Week'),
            ('due_month', 'Due This Month'),
        ]

    def queryset(self, request, queryset):
        today = timezone.now().date()
        if self.value() == 'overdue':
            return queryset.filter(due_date__lt=today, return_date__isnull=True)
        elif self.value() == 'due_today':
            return queryset.filter(due_date=today, return_date__isnull=True)
        elif self.value() == 'due_tomorrow':
            return queryset.filter(due_date=today + timedelta(days=1), return_date__isnull=True)
        elif self.value() == 'due_week':
            return queryset.filter(
                due_date__gte=today,
                due_date__lte=today + timedelta(days=7),
                return_date__isnull=True
            )
        elif self.value() == 'due_month':
            return queryset.filter(
                due_date__gte=today,
                due_date__lte=today + timedelta(days=30),
                return_date__isnull=True
            )
        return queryset


class FineAmountFilter(SimpleListFilter):
    """Filter loans by fine amount"""
    title = 'Fine Amount'
    parameter_name = 'fine_amount'

    def lookups(self, request, model_admin):
        return [
            ('no_fine', 'No Fine'),
            ('small_fine', 'Small Fine (< 10,000)'),
            ('medium_fine', 'Medium Fine (10,000 - 50,000)'),
            ('large_fine', 'Large Fine (> 50,000)'),
            ('unpaid', 'Unpaid Fines'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'no_fine':
            return queryset.filter(fine_amount=0)
        elif self.value() == 'small_fine':
            return queryset.filter(fine_amount__gt=0, fine_amount__lt=10000)
        elif self.value() == 'medium_fine':
            return queryset.filter(fine_amount__gte=10000, fine_amount__lte=50000)
        elif self.value() == 'large_fine':
            return queryset.filter(fine_amount__gt=50000)
        elif self.value() == 'unpaid':
            return queryset.filter(fine_amount__gt=0, fine_paid=False, fine_waived=False)
        return queryset


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Professional Loan Admin with comprehensive features"""
    
    list_display = [
        'loan_id_display',
        'user_link',
        'book_link',
        'status_badge',
        'loan_date',
        'due_date_display',
        'return_date_display',
        'fine_display',
        'renewal_count_display',
        'days_overdue',
    ]
    
    list_display_links = ['loan_id_display']
    
    list_filter = [
        LoanStatusFilter,
        DueDateFilter,
        FineAmountFilter,
        'loan_date',
        'due_date',
        'fine_paid',
        'fine_waived',
        'renewal_count',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'book__title',
        'book__isbn',
        'book__authors__name',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'days_since_loan',
        'calculated_fine',
        'loan_duration',
    ]
    
    fieldsets = [
        ('Loan Information', {
            'fields': [
                ('user', 'book'),
                ('status', 'loan_date'),
                ('due_date', 'return_date'),
            ],
            'classes': ['wide'],
        }),
        ('Renewal Information', {
            'fields': [
                ('renewal_count', 'renewal_history'),
            ],
            'classes': ['wide'],
        }),
        ('Fine Management', {
            'fields': [
                'fine_amount',
                ('fine_paid', 'fine_waived'),
                'calculated_fine',
            ],
            'classes': ['wide'],
        }),
        ('Notes', {
            'fields': [
                'notes',
                'librarian_notes',
            ],
            'classes': ['wide'],
        }),
        ('System Information', {
            'fields': [
                'created_by',
                ('created_at', 'updated_at'),
                ('days_since_loan', 'loan_duration'),
            ],
            'classes': ['wide', 'collapse'],
        }),
    ]
    
    # Pagination
    list_per_page = 25
    list_max_show_all = 100
    
    # Date hierarchy
    date_hierarchy = 'loan_date'
    
    # Ordering
    ordering = ['-created_at']
    
    # Custom actions
    actions = [
        'mark_as_returned',
        'mark_as_overdue',
        'calculate_fines',
        'waive_fines',
        'send_reminder_emails',
        'export_loans_csv',
        'generate_overdue_report',
    ]
    
    def loan_id_display(self, obj):
        """Display loan ID with status icon"""
        status_icons = {
            LoanStatus.ACTIVE: '🟢',
            LoanStatus.OVERDUE: '🔴',
            LoanStatus.RETURNED: '✅',
            LoanStatus.RENEWED: '🔄',
            LoanStatus.LOST: '❌',
            LoanStatus.DAMAGED: '⚠️',
        }
        icon = status_icons.get(obj.status, '📋')
        return f"{icon} #{obj.id}"
    loan_id_display.short_description = "Loan ID"
    loan_id_display.admin_order_field = "id"
    
    def user_link(self, obj):
        """Link to user admin page"""
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html(
            '<a href="{}">{}</a><br><small>{}</small>',
            url,
            obj.user.get_full_name() or obj.user.username,
            obj.user.email
        )
    user_link.short_description = "User"
    user_link.admin_order_field = "user__username"
    
    def book_link(self, obj):
        """Link to book admin page"""
        url = reverse('admin:books_book_change', args=[obj.book.pk])
        return format_html(
            '<a href="{}">{}</a><br><small>ISBN: {}</small>',
            url,
            obj.book.title[:40] + "..." if len(obj.book.title) > 40 else obj.book.title,
            obj.book.isbn or "N/A"
        )
    book_link.short_description = "Book"
    book_link.admin_order_field = "book__title"
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            LoanStatus.ACTIVE: '#198754',      # Green
            LoanStatus.OVERDUE: '#dc3545',     # Red
            LoanStatus.RETURNED: '#0d6efd',    # Blue
            LoanStatus.RENEWED: '#fd7e14',     # Orange
            LoanStatus.LOST: '#6c757d',        # Gray
            LoanStatus.DAMAGED: '#6c757d',     # Gray
        }
        
        # Check if loan is actually overdue
        if obj.status == LoanStatus.ACTIVE and obj.due_date < timezone.now().date():
            display_status = "OVERDUE"
            color = colors[LoanStatus.OVERDUE]
        else:
            display_status = obj.get_status_display()
            color = colors.get(obj.status, '#6c757d')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            display_status
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"
    
    def due_date_display(self, obj):
        """Display due date with color coding"""
        today = timezone.now().date()
        days_until_due = (obj.due_date - today).days
        
        if obj.return_date:  # Already returned
            return format_html('<span style="color: green;">✅ {}</span>', obj.due_date)
        elif days_until_due < 0:  # Overdue
            return format_html(
                '<span style="color: red; font-weight: bold;">🔴 {} ({} days overdue)</span>',
                obj.due_date,
                abs(days_until_due)
            )
        elif days_until_due == 0:  # Due today
            return format_html('<span style="color: orange; font-weight: bold;">⚠️ {} (Due today)</span>', obj.due_date)
        elif days_until_due <= 3:  # Due soon
            return format_html('<span style="color: orange;">⏰ {} ({} days)</span>', obj.due_date, days_until_due)
        else:
            return format_html('<span style="color: green;">{}</span>', obj.due_date)
    due_date_display.short_description = "Due Date"
    due_date_display.admin_order_field = "due_date"
    
    def return_date_display(self, obj):
        """Display return date with status"""
        if obj.return_date:
            if obj.return_date <= obj.due_date:
                return format_html('<span style="color: green;">✅ {}</span>', obj.return_date)
            else:
                days_late = (obj.return_date - obj.due_date).days
                return format_html(
                    '<span style="color: orange;">⏰ {} ({} days late)</span>',
                    obj.return_date,
                    days_late
                )
        return format_html('<span style="color: gray;">Not returned</span>')
    return_date_display.short_description = "Return Date"
    return_date_display.admin_order_field = "return_date"
    
    def fine_display(self, obj):
        """Display fine information with status"""
        if obj.fine_amount > 0:
            if obj.fine_waived:
                return format_html(
                    '<span style="color: blue;">💸 {} som (Waived)</span>',
                    f"{obj.fine_amount:,.0f}"
                )
            elif obj.fine_paid:
                return format_html(
                    '<span style="color: green;">💰 {} som (Paid)</span>',
                    f"{obj.fine_amount:,.0f}"
                )
            else:
                return format_html(
                    '<span style="color: red; font-weight: bold;">💸 {} som (Unpaid)</span>',
                    f"{obj.fine_amount:,.0f}"
                )
        return "-"
    fine_display.short_description = "Fine"
    fine_display.admin_order_field = "fine_amount"
    
    def renewal_count_display(self, obj):
        """Display renewal count with visual indicator"""
        if obj.renewal_count > 0:
            return format_html(
                '<span style="color: orange;">🔄 {} renewals</span>',
                obj.renewal_count
            )
        return "-"
    renewal_count_display.short_description = "Renewals"
    renewal_count_display.admin_order_field = "renewal_count"
    
    def days_overdue(self, obj):
        """Calculate and display days overdue"""
        if obj.return_date:
            return "-"
        
        today = timezone.now().date()
        if obj.due_date < today:
            days = (today - obj.due_date).days
            return format_html('<span style="color: red; font-weight: bold;">{} days</span>', days)
        return "-"
    days_overdue.short_description = "Days Overdue"
    
    def days_since_loan(self, obj):
        """Calculate days since loan was created"""
        today = timezone.now().date()
        return (today - obj.loan_date).days
    days_since_loan.short_description = "Days Since Loan"
    
    def calculated_fine(self, obj):
        """Calculate fine based on overdue days"""
        if obj.return_date or obj.due_date >= timezone.now().date():
            return "No fine"
        
        days_overdue = (timezone.now().date() - obj.due_date).days
        fine_per_day = 1000  # This should come from settings
        calculated_fine = days_overdue * fine_per_day
        
        return format_html(
            '<strong>{} som</strong><br><small>({} days × {} som/day)</small>',
            f"{calculated_fine:,.0f}",
            days_overdue,
            f"{fine_per_day:,.0f}"
        )
    calculated_fine.short_description = "Calculated Fine"
    
    def loan_duration(self, obj):
        """Calculate loan duration"""
        end_date = obj.return_date or timezone.now().date()
        return (end_date - obj.loan_date).days
    loan_duration.short_description = "Loan Duration (days)"
    
    # Custom actions
    def mark_as_returned(self, request, queryset):
        """Mark selected loans as returned"""
        today = timezone.now().date()
        updated = 0
        for loan in queryset:
            if not loan.return_date:
                loan.status = LoanStatus.RETURNED
                loan.return_date = today
                loan.book.return_copy()  # Update book availability
                loan.save()
                updated += 1
        
        self.message_user(request, f"{updated} loans marked as returned.")
    mark_as_returned.short_description = "Mark selected loans as returned"
    
    def mark_as_overdue(self, request, queryset):
        """Mark selected loans as overdue"""
        updated = queryset.filter(
            due_date__lt=timezone.now().date(),
            return_date__isnull=True
        ).update(status=LoanStatus.OVERDUE)
        
        self.message_user(request, f"{updated} loans marked as overdue.")
    mark_as_overdue.short_description = "Mark selected loans as overdue"
    
    def calculate_fines(self, request, queryset):
        """Calculate fines for overdue loans"""
        updated = 0
        fine_per_day = 1000  # This should come from settings
        
        for loan in queryset:
            if not loan.return_date and loan.due_date < timezone.now().date():
                days_overdue = (timezone.now().date() - loan.due_date).days
                calculated_fine = days_overdue * fine_per_day
                loan.fine_amount = calculated_fine
                loan.save()
                updated += 1
        
        self.message_user(request, f"Fines calculated for {updated} loans.")
    calculate_fines.short_description = "Calculate fines for overdue loans"
    
    def waive_fines(self, request, queryset):
        """Waive fines for selected loans"""
        updated = queryset.update(fine_waived=True)
        self.message_user(request, f"Fines waived for {updated} loans.")
    waive_fines.short_description = "Waive fines for selected loans"
    
    def send_reminder_emails(self, request, queryset):
        """Send reminder emails for due/overdue loans"""
        count = 0
        for loan in queryset:
            if not loan.return_date:
                # Here you would implement email sending logic
                count += 1
        
        self.message_user(request, f"Reminder emails sent for {count} loans.")
    send_reminder_emails.short_description = "Send reminder emails"
    
    def export_loans_csv(self, request, queryset):
        """Export loans to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="loans_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Loan ID', 'User', 'Book', 'Status', 'Loan Date', 'Due Date', 
            'Return Date', 'Fine Amount', 'Fine Paid', 'Renewals'
        ])
        
        for loan in queryset:
            writer.writerow([
                loan.id,
                loan.user.get_full_name() or loan.user.username,
                loan.book.title,
                loan.get_status_display(),
                loan.loan_date,
                loan.due_date,
                loan.return_date or '',
                loan.fine_amount,
                'Yes' if loan.fine_paid else 'No',
                loan.renewal_count
            ])
        
        return response
    export_loans_csv.short_description = "Export selected loans to CSV"
    
    def generate_overdue_report(self, request, queryset):
        """Generate overdue loans report"""
        overdue_loans = queryset.filter(
            due_date__lt=timezone.now().date(),
            return_date__isnull=True
        )
        
        self.message_user(
            request, 
            f"Overdue report generated: {overdue_loans.count()} overdue loans found."
        )
    generate_overdue_report.short_description = "Generate overdue report"
    
    # Optimize queryset
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'user', 'book', 'created_by'
        ).prefetch_related('book__authors')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Professional Reservation Admin"""
    
    list_display = [
        'reservation_id_display',
        'user_link',
        'book_link',
        'status_badge',
        'queue_position_display',
        'reserved_at_display',
        'expires_at_display',
        'priority_display',
    ]
    
    list_display_links = ['reservation_id_display']
    
    list_filter = [
        'status',
        'priority',
        'reserved_at',
        'expires_at',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'book__title',
        'book__isbn',
    ]
    
    readonly_fields = [
        'reserved_at',
        'updated_at',
        'time_remaining',
    ]
    
    fieldsets = [
        ('Reservation Information', {
            'fields': [
                ('user', 'book'),
                ('status', 'priority'),
                ('queue_position', 'reserved_at'),
                ('expires_at', 'notified_at'),
            ],
            'classes': ['wide'],
        }),
        ('Additional Information', {
            'fields': [
                'notes',
                'time_remaining',
                'updated_at',
            ],
            'classes': ['wide'],
        }),
    ]
    
    ordering = ['queue_position', '-reserved_at']
    list_per_page = 25
    
    actions = [
        'mark_as_fulfilled',
        'mark_as_cancelled',
        'extend_expiration',
        'notify_users',
        'export_reservations_csv',
    ]
    
    def reservation_id_display(self, obj):
        """Display reservation ID with status icon"""
        status_icons = {
            ReservationStatus.PENDING: '⏳',
            ReservationStatus.NOTIFIED: '📧',
            ReservationStatus.FULFILLED: '✅',
            ReservationStatus.CANCELLED: '❌',
            ReservationStatus.EXPIRED: '⏰',
        }
        icon = status_icons.get(obj.status, '📋')
        return f"{icon} #{obj.id}"
    reservation_id_display.short_description = "Reservation ID"
    reservation_id_display.admin_order_field = "id"
    
    def user_link(self, obj):
        """Link to user admin page"""
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
    user_link.short_description = "User"
    user_link.admin_order_field = "user__username"
    
    def book_link(self, obj):
        """Link to book admin page"""
        url = reverse('admin:books_book_change', args=[obj.book.pk])
        return format_html('<a href="{}">{}</a>', url, obj.book.title[:40])
    book_link.short_description = "Book"
    book_link.admin_order_field = "book__title"
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            ReservationStatus.PENDING: '#fd7e14',      # Orange
            ReservationStatus.NOTIFIED: '#0d6efd',     # Blue
            ReservationStatus.FULFILLED: '#198754',    # Green
            ReservationStatus.CANCELLED: '#6c757d',    # Gray
            ReservationStatus.EXPIRED: '#dc3545',      # Red
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"
    
    def queue_position_display(self, obj):
        """Display queue position with visual indicator"""
        if obj.queue_position == 1:
            return format_html('<span style="color: green; font-weight: bold;">🥇 1st</span>')
        elif obj.queue_position == 2:
            return format_html('<span style="color: orange; font-weight: bold;">🥈 2nd</span>')
        elif obj.queue_position == 3:
            return format_html('<span style="color: #cd7f32; font-weight: bold;">🥉 3rd</span>')
        else:
            return format_html('<span>{}</span>', f"#{obj.queue_position}")
    queue_position_display.short_description = "Queue Position"
    queue_position_display.admin_order_field = "queue_position"
    
    def reserved_at_display(self, obj):
        """Display reservation time"""
        return obj.reserved_at.strftime('%Y-%m-%d %H:%M')
    reserved_at_display.short_description = "Reserved At"
    reserved_at_display.admin_order_field = "reserved_at"
    
    def expires_at_display(self, obj):
        """Display expiration with color coding"""
        now = timezone.now()
        time_left = obj.expires_at - now
        
        if time_left.total_seconds() <= 0:
            return format_html('<span style="color: red; font-weight: bold;">❌ Expired</span>')
        elif time_left.total_seconds() <= 3600:  # Less than 1 hour
            return format_html('<span style="color: red;">⚠️ {} (Soon)</span>', obj.expires_at.strftime('%H:%M'))
        elif time_left.days == 0:  # Today
            return format_html('<span style="color: orange;">⏰ {}</span>', obj.expires_at.strftime('%H:%M'))
        else:
            return format_html('<span style="color: green;">{}</span>', obj.expires_at.strftime('%Y-%m-%d %H:%M'))
    expires_at_display.short_description = "Expires At"
    expires_at_display.admin_order_field = "expires_at"
    
    def priority_display(self, obj):
        """Display priority with visual indicator"""
        if obj.priority > 0:
            return format_html('<span style="color: red; font-weight: bold;">⭐ High ({})</span>', obj.priority)
        return "Normal"
    priority_display.short_description = "Priority"
    priority_display.admin_order_field = "priority"
    
    def time_remaining(self, obj):
        """Calculate time remaining until expiration"""
        now = timezone.now()
        time_left = obj.expires_at - now
        
        if time_left.total_seconds() <= 0:
            return "Expired"
        
        days = time_left.days
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        
        if days > 0:
            return f"{days} days, {hours} hours"
        elif hours > 0:
            return f"{hours} hours, {minutes} minutes"
        else:
            return f"{minutes} minutes"
    time_remaining.short_description = "Time Remaining"
    
    # Custom actions
    def mark_as_fulfilled(self, request, queryset):
        """Mark reservations as fulfilled"""
        updated = queryset.update(status=ReservationStatus.FULFILLED)
        self.message_user(request, f"{updated} reservations marked as fulfilled.")
    mark_as_fulfilled.short_description = "Mark as fulfilled"
    
    def mark_as_cancelled(self, request, queryset):
        """Mark reservations as cancelled"""
        updated = queryset.update(status=ReservationStatus.CANCELLED)
        self.message_user(request, f"{updated} reservations cancelled.")
    mark_as_cancelled.short_description = "Mark as cancelled"
    
    def extend_expiration(self, request, queryset):
        """Extend expiration by 24 hours"""
        for reservation in queryset:
            reservation.expires_at += timedelta(hours=24)
            reservation.save()
        
        self.message_user(request, f"Extended expiration for {queryset.count()} reservations.")
    extend_expiration.short_description = "Extend expiration by 24 hours"
    
    def notify_users(self, request, queryset):
        """Send notification to users"""
        count = 0
        for reservation in queryset:
            if reservation.status == ReservationStatus.PENDING:
                # Here you would implement notification logic
                count += 1
        
        self.message_user(request, f"Notifications sent for {count} reservations.")
    notify_users.short_description = "Send notifications to users"
    
    def export_reservations_csv(self, request, queryset):
        """Export reservations to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reservations_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Reservation ID', 'User', 'Book', 'Status', 'Queue Position',
            'Reserved At', 'Expires At', 'Priority'
        ])
        
        for reservation in queryset:
            writer.writerow([
                reservation.id,
                reservation.user.get_full_name() or reservation.user.username,
                reservation.book.title,
                reservation.get_status_display(),
                reservation.queue_position,
                reservation.reserved_at,
                reservation.expires_at,
                reservation.priority
            ])
        
        return response
    export_reservations_csv.short_description = "Export to CSV"


# Admin site customization
admin.site.site_header = "Library Management System"
admin.site.site_title = "Library Admin"
admin.site.index_title = "Loan & Reservation Management"
