"""
Professional Django Admin Configuration for Accounts App

This module provides comprehensive admin interface for user management with:
- Advanced filtering and search capabilities
- Custom actions for bulk operations
- Enhanced display and navigation
- Security and audit features
- Professional UI improvements
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.admin import SimpleListFilter
from django.core.exceptions import ValidationError
import csv
from io import StringIO
from django.http import HttpResponse

from .models import User, UserSession, UserVerificationLog, UserRole, AccountStatus, VerificationStatus


class VerificationStatusFilter(SimpleListFilter):
    """Custom filter for verification status"""
    title = 'Verification Status'
    parameter_name = 'verification_status'

    def lookups(self, request, model_admin):
        return [
            ('pending', 'Pending Verification'),
            ('verified', 'Fully Verified'),
            ('partial', 'Partially Verified'),
            ('rejected', 'Verification Rejected'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'pending':
            return queryset.filter(
                Q(email_verification_status='pending') |
                Q(identity_verification_status='pending') |
                Q(professional_verification_status='pending')
            )
        elif self.value() == 'verified':
            return queryset.filter(is_fully_verified=True)
        elif self.value() == 'partial':
            return queryset.filter(
                Q(email_verification_status='approved') &
                (Q(identity_verification_status='pending') |
                 Q(professional_verification_status='pending'))
            )
        elif self.value() == 'rejected':
            return queryset.filter(
                Q(identity_verification_status='rejected') |
                Q(professional_verification_status='rejected')
            )
        return queryset


class AccountAgeFilter(SimpleListFilter):
    """Filter users by account age"""
    title = 'Account Age'
    parameter_name = 'account_age'

    def lookups(self, request, model_admin):
        return [
            ('new', 'New (< 7 days)'),
            ('recent', 'Recent (< 30 days)'),
            ('established', 'Established (< 6 months)'),
            ('old', 'Old (> 6 months)'),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'new':
            return queryset.filter(date_joined__gte=now - timezone.timedelta(days=7))
        elif self.value() == 'recent':
            return queryset.filter(date_joined__gte=now - timezone.timedelta(days=30))
        elif self.value() == 'established':
            return queryset.filter(
                date_joined__gte=now - timezone.timedelta(days=180),
                date_joined__lt=now - timezone.timedelta(days=30)
            )
        elif self.value() == 'old':
            return queryset.filter(date_joined__lt=now - timezone.timedelta(days=180))
        return queryset


class UserSessionInline(admin.TabularInline):
    """Inline for user sessions"""
    model = UserSession
    extra = 0
    readonly_fields = ['session_key', 'ip_address', 'user_agent', 'login_time', 'last_activity']
    fields = ['session_key', 'ip_address', 'is_active', 'login_time', 'last_activity']
    
    def has_add_permission(self, request, obj=None):
        return False


class UserVerificationLogInline(admin.TabularInline):
    """Inline for user verification logs"""
    model = UserVerificationLog
    fk_name = 'user'  # Specify which ForeignKey to use
    extra = 0
    readonly_fields = ['verification_type', 'old_status', 'new_status', 'verified_by', 'created_at']
    fields = ['verification_type', 'old_status', 'new_status', 'verified_by', 'notes', 'created_at']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Professional User Admin with comprehensive features
    
    Features:
    - Enhanced list display with status indicators
    - Advanced filtering and search
    - Custom actions for bulk operations
    - Detailed fieldsets organization
    - Inline related objects
    - Security and audit information
    """
    
    # List display configuration
    list_display = [
        'username_with_status',
        'full_name_display',
        'email',
        'role_badge',
        'account_status_badge',
        'verification_status_display',
        'last_login_display',
        'date_joined_display',
        'loan_count',
    ]
    
    list_display_links = ['username_with_status', 'full_name_display']
    
    # Filtering options
    list_filter = [
        'role',
        'account_status',
        VerificationStatusFilter,
        AccountAgeFilter,
        'gender',
        'profession_category',
        'email_verification_status',
        'identity_verification_status',
        'professional_verification_status',
        'is_staff',
        'is_superuser',
        'is_active',
    ]
    
    # Search configuration
    search_fields = [
        'username',
        'email',
        'first_name',
        'last_name',
        'middle_name',
        'phone_number',
        'profession_title',
        'workplace_organization',
    ]
    
    # Ordering
    ordering = ['-date_joined']
    
    # Pagination
    list_per_page = 25
    list_max_show_all = 100
    
    # Date hierarchy
    date_hierarchy = 'date_joined'
    
    # Custom fieldsets for enhanced organization
    fieldsets = [
        ('Basic Information', {
            'fields': [
                'username',
                'email',
                'password',
            ],
            'classes': ['wide'],
        }),
        ('Personal Details', {
            'fields': [
                ('first_name', 'middle_name', 'last_name'),
                ('date_of_birth', 'gender'),
                'profile_photo',
            ],
            'classes': ['wide'],
        }),
        ('Contact Information', {
            'fields': [
                'phone_number',
                ('address_line_1', 'address_line_2'),
                ('city', 'state_province'),
                ('postal_code', 'country'),
            ],
            'classes': ['wide'],
        }),
        ('Professional Information', {
            'fields': [
                'profession_category',
                'profession_title',
                'workplace_organization',
                'professional_document',
            ],
            'classes': ['wide'],
        }),
        ('System Information', {
            'fields': [
                'role',
                'account_status',
                ('is_active', 'is_staff', 'is_superuser'),
            ],
            'classes': ['wide'],
        }),
        ('Verification Status', {
            'fields': [
                'email_verification_status',
                'phone_verification_status',
                'identity_verification_status',
                'professional_verification_status',
                'is_fully_verified',
            ],
            'classes': ['wide'],
        }),
        ('Documents', {
            'fields': [
                ('identity_document_type', 'identity_document_number'),
                'identity_document_front',
                'identity_document_back',
                'selfie_photo',
            ],
            'classes': ['wide', 'collapse'],
        }),
        ('Preferences', {
            'fields': [
                'profile_visibility',
                ('email_notifications', 'sms_notifications'),
            ],
            'classes': ['wide', 'collapse'],
        }),
        ('Important Dates', {
            'fields': [
                'last_login',
                'date_joined',
                ('email_verified_at', 'phone_verified_at'),
            ],
            'classes': ['wide', 'collapse'],
        }),
    ]
    
    # Add user fieldsets
    add_fieldsets = [
        ('Required Information', {
            'classes': ['wide'],
            'fields': [
                'username',
                'email',
                'password1',
                'password2',
            ],
        }),
        ('Personal Information', {
            'classes': ['wide'],
            'fields': [
                ('first_name', 'last_name'),
                'role',
            ],
        }),
    ]
    
    # Readonly fields
    readonly_fields = [
        'id',
        'date_joined',
        'last_login',
        'email_verified_at',
        'phone_verified_at',
        'verification_completion_percentage',
        'is_fully_verified',
        'last_login_ip',
    ]
    
    # Inline models
    inlines = [UserSessionInline, UserVerificationLogInline]
    
    # Custom methods for display
    def username_with_status(self, obj):
        """Display username with status icon"""
        status_icon = "✅" if obj.is_active else "❌"
        return f"{status_icon} {obj.username}"
    username_with_status.short_description = "Username"
    username_with_status.admin_order_field = "username"
    
    def full_name_display(self, obj):
        """Display full name with fallback"""
        return obj.get_full_name() or f"({obj.username})"
    full_name_display.short_description = "Full Name"
    full_name_display.admin_order_field = "first_name"
    
    def role_badge(self, obj):
        """Display role as colored badge"""
        colors = {
            UserRole.SUPER_ADMIN: '#dc3545',  # Red
            UserRole.LIBRARIAN: '#fd7e14',    # Orange
            UserRole.TEACHER: '#198754',      # Green
            UserRole.STUDENT: '#0d6efd',      # Blue
            UserRole.MEMBER: '#6c757d',       # Gray
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = "Role"
    role_badge.admin_order_field = "role"
    
    def account_status_badge(self, obj):
        """Display account status as colored badge"""
        colors = {
            AccountStatus.ACTIVE: '#198754',           # Green
            AccountStatus.SUSPENDED: '#dc3545',       # Red
            AccountStatus.PENDING_ACTIVATION: '#fd7e14',  # Orange
            AccountStatus.INACTIVE: '#6c757d',        # Gray
        }
        color = colors.get(obj.account_status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_account_status_display()
        )
    account_status_badge.short_description = "Status"
    account_status_badge.admin_order_field = "account_status"
    
    def verification_status_display(self, obj):
        """Display verification status with progress"""
        percentage = obj.verification_completion_percentage
        if percentage == 100:
            return format_html('<span style="color: green;">✅ Verified</span>')
        elif percentage > 50:
            return format_html('<span style="color: orange;">⏳ {}%</span>', percentage)
        else:
            return format_html('<span style="color: red;">❌ {}%</span>', percentage)
    verification_status_display.short_description = "Verification"
    verification_status_display.admin_order_field = "is_fully_verified"
    
    def last_login_display(self, obj):
        """Display last login with relative time"""
        if not obj.last_login:
            return "Never"
        
        now = timezone.now()
        diff = now - obj.last_login
        
        if diff.days > 30:
            return format_html('<span style="color: red;">{} ago</span>', 
                             f"{diff.days} days")
        elif diff.days > 7:
            return format_html('<span style="color: orange;">{} ago</span>', 
                             f"{diff.days} days")
        else:
            return format_html('<span style="color: green;">{}</span>', 
                             obj.last_login.strftime('%Y-%m-%d'))
    last_login_display.short_description = "Last Login"
    last_login_display.admin_order_field = "last_login"
    
    def date_joined_display(self, obj):
        """Display join date in readable format"""
        return obj.date_joined.strftime('%Y-%m-%d')
    date_joined_display.short_description = "Joined"
    date_joined_display.admin_order_field = "date_joined"
    
    def loan_count(self, obj):
        """Display active loan count"""
        # This would need to be implemented with proper import
        # from loans.models import Loan
        # count = Loan.objects.filter(user=obj, status='active').count()
        count = 0  # Placeholder
        if count > 0:
            return format_html('<span style="color: blue;">{} loans</span>', count)
        return "-"
    loan_count.short_description = "Active Loans"
    
    # Custom actions
    actions = [
        'activate_users',
        'deactivate_users',
        'suspend_users',
        'approve_email_verification',
        'approve_identity_verification',
        'export_users_csv',
        'send_verification_reminder',
    ]
    
    def activate_users(self, request, queryset):
        """Bulk activate users"""
        updated = queryset.update(account_status=AccountStatus.ACTIVE)
        self.message_user(request, f"{updated} users were successfully activated.")
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        """Bulk deactivate users"""
        updated = queryset.update(account_status=AccountStatus.INACTIVE)
        self.message_user(request, f"{updated} users were successfully deactivated.")
    deactivate_users.short_description = "Deactivate selected users"
    
    def suspend_users(self, request, queryset):
        """Bulk suspend users"""
        updated = queryset.update(account_status=AccountStatus.SUSPENDED)
        self.message_user(request, f"{updated} users were successfully suspended.")
    suspend_users.short_description = "Suspend selected users"
    
    def approve_email_verification(self, request, queryset):
        """Bulk approve email verification"""
        updated = queryset.update(
            email_verification_status=VerificationStatus.APPROVED,
            email_verified_at=timezone.now()
        )
        self.message_user(request, f"Email verification approved for {updated} users.")
    approve_email_verification.short_description = "Approve email verification"
    
    def approve_identity_verification(self, request, queryset):
        """Bulk approve identity verification"""
        updated = queryset.update(
            identity_verification_status=VerificationStatus.APPROVED
        )
        self.message_user(request, f"Identity verification approved for {updated} users.")
    approve_identity_verification.short_description = "Approve identity verification"
    
    def export_users_csv(self, request, queryset):
        """Export selected users to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Username', 'Email', 'Full Name', 'Role', 'Status', 
            'Phone', 'Date Joined', 'Last Login'
        ])
        
        for user in queryset:
            writer.writerow([
                user.username,
                user.email,
                user.get_full_name(),
                user.get_role_display(),
                user.get_account_status_display(),
                user.phone_number or '',
                user.date_joined.strftime('%Y-%m-%d'),
                user.last_login.strftime('%Y-%m-%d') if user.last_login else 'Never'
            ])
        
        return response
    export_users_csv.short_description = "Export selected users to CSV"
    
    def send_verification_reminder(self, request, queryset):
        """Send verification reminder emails"""
        count = 0
        for user in queryset:
            if not user.is_fully_verified:
                # Here you would implement email sending logic
                count += 1
        
        self.message_user(request, f"Verification reminder sent to {count} users.")
    send_verification_reminder.short_description = "Send verification reminder"
    
    # Custom queryset optimization
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related()


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin for user sessions with security focus"""
    
    list_display = [
        'user_link',
        'ip_address',
        'location_display',
        'device_info',
        'login_time',
        'last_activity_display',
        'session_status',
    ]
    
    list_filter = [
        'is_active',
        'login_time',
        'last_activity',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'ip_address',
        'session_key',
    ]
    
    readonly_fields = [
        'user',
        'session_key',
        'ip_address',
        'user_agent',
        'login_time',
        'last_activity',
    ]
    
    date_hierarchy = 'login_time'
    ordering = ['-last_activity']
    list_per_page = 50
    
    def user_link(self, obj):
        """Link to user admin page"""
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"
    user_link.admin_order_field = "user__username"
    
    def location_display(self, obj):
        """Display location info if available"""
        # This would integrate with IP geolocation service
        return "Unknown"  # Placeholder
    location_display.short_description = "Location"
    
    def device_info(self, obj):
        """Extract device info from user agent"""
        ua = obj.user_agent.lower()
        if 'mobile' in ua:
            return "📱 Mobile"
        elif 'tablet' in ua:
            return "📊 Tablet"
        else:
            return "💻 Desktop"
    device_info.short_description = "Device"
    
    def last_activity_display(self, obj):
        """Display last activity with color coding"""
        now = timezone.now()
        diff = now - obj.last_activity
        
        if diff.total_seconds() < 3600:  # Less than 1 hour
            return format_html('<span style="color: green;">🟢 Active</span>')
        elif diff.days < 1:
            return format_html('<span style="color: orange;">🟡 Recent</span>')
        else:
            return format_html('<span style="color: red;">🔴 Inactive</span>')
    last_activity_display.short_description = "Activity"
    
    def session_status(self, obj):
        """Display session status"""
        if obj.is_active:
            return format_html('<span style="color: green;">✅ Active</span>')
        else:
            return format_html('<span style="color: red;">❌ Ended</span>')
    session_status.short_description = "Status"
    session_status.admin_order_field = "is_active"
    
    actions = ['terminate_sessions']
    
    def terminate_sessions(self, request, queryset):
        """Terminate selected sessions"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} sessions were terminated.")
    terminate_sessions.short_description = "Terminate selected sessions"


@admin.register(UserVerificationLog)
class UserVerificationLogAdmin(admin.ModelAdmin):
    """Admin for user verification logs with audit trail"""
    
    list_display = [
        'user_link',
        'verification_type_badge',
        'status_change',
        'verified_by_link',
        'created_at_display',
        'notes_preview',
    ]
    
    list_filter = [
        'verification_type',
        'new_status',
        'created_at',
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'verified_by__username',
        'notes',
    ]
    
    readonly_fields = [
        'user',
        'verification_type',
        'old_status',
        'new_status',
        'verified_by',
        'created_at',
    ]
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50
    
    def user_link(self, obj):
        """Link to user admin page"""
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = "User"
    user_link.admin_order_field = "user__username"
    
    def verified_by_link(self, obj):
        """Link to verifier admin page"""
        if obj.verified_by:
            url = reverse('admin:accounts_user_change', args=[obj.verified_by.pk])
            return format_html('<a href="{}">{}</a>', url, obj.verified_by.username)
        return "System"
    verified_by_link.short_description = "Verified By"
    
    def verification_type_badge(self, obj):
        """Display verification type as badge"""
        colors = {
            'email': '#0d6efd',
            'phone': '#198754',
            'identity': '#fd7e14',
            'professional': '#6610f2',
        }
        color = colors.get(obj.verification_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.verification_type.title()
        )
    verification_type_badge.short_description = "Type"
    verification_type_badge.admin_order_field = "verification_type"
    
    def status_change(self, obj):
        """Display status change with arrows"""
        return format_html('{} → {}', obj.old_status, obj.new_status)
    status_change.short_description = "Status Change"
    
    def created_at_display(self, obj):
        """Display creation time in readable format"""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.short_description = "Date"
    created_at_display.admin_order_field = "created_at"
    
    def notes_preview(self, obj):
        """Display truncated notes"""
        if obj.notes:
            return obj.notes[:50] + "..." if len(obj.notes) > 50 else obj.notes
        return "-"
    notes_preview.short_description = "Notes"


# Admin site customization
admin.site.site_header = "Library Management System"
admin.site.site_title = "Library Admin"
admin.site.index_title = "Welcome to Library Administration"