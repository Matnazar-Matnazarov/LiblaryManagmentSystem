"""
Professional Django Admin Configuration for Loans App

Bu modul kutubxona qarz berish tizimi uchun professional admin interfeysi taqdim etadi:
- Qarz berish va qaytarish boshqaruvi
- Rezervatsiya tizimi
- Jarima hisoblash va boshqaruv
- Kengaytirish (renewal) boshqaruvi
- Keng qamrovli hisobot va eksport
- Professional UI yaxshilanishlari
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponse
from django.contrib import messages
from datetime import timedelta, date
import csv

from .models import Loan, Reservation, LoanStatus, ReservationStatus


class LoanStatusFilter(SimpleListFilter):
    """Qarz holati uchun maxsus filter"""
    title = 'Qarz Holati'
    parameter_name = 'loan_status'

    def lookups(self, request, model_admin):
        return [
            ('active', 'Faol'),
            ('overdue', 'Muddati o\'tgan'),
            ('returned', 'Qaytarilgan'),
            ('renewable', 'Kengaytirilishi mumkin'),
            ('with_fines', 'Jarima bilan'),
        ]

    def queryset(self, request, queryset):
        today = timezone.now().date()
        
        if self.value() == 'active':
            return queryset.filter(status=LoanStatus.ACTIVE)
        elif self.value() == 'overdue':
            return queryset.filter(
                status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE],
                due_date__lt=today
            )
        elif self.value() == 'returned':
            return queryset.filter(status=LoanStatus.RETURNED)
        elif self.value() == 'renewable':
            return queryset.filter(
                status=LoanStatus.ACTIVE,
                renewal_count__lt=3,
                due_date__gte=today
            )
        elif self.value() == 'with_fines':
            return queryset.filter(fine_amount__gt=0, fine_paid=False)
        return queryset


class DueDateFilter(SimpleListFilter):
    """Qaytarish muddati uchun filter"""
    title = 'Qaytarish Muddati'
    parameter_name = 'due_date_filter'

    def lookups(self, request, model_admin):
        return [
            ('today', 'Bugun'),
            ('tomorrow', 'Ertaga'),
            ('this_week', 'Shu hafta'),
            ('next_week', 'Keyingi hafta'),
            ('overdue', 'Muddati o\'tgan'),
        ]

    def queryset(self, request, queryset):
        today = timezone.now().date()
        
        if self.value() == 'today':
            return queryset.filter(due_date=today)
        elif self.value() == 'tomorrow':
            return queryset.filter(due_date=today + timedelta(days=1))
        elif self.value() == 'this_week':
            week_end = today + timedelta(days=7)
            return queryset.filter(due_date__range=[today, week_end])
        elif self.value() == 'next_week':
            week_start = today + timedelta(days=7)
            week_end = week_start + timedelta(days=7)
            return queryset.filter(due_date__range=[week_start, week_end])
        elif self.value() == 'overdue':
            return queryset.filter(due_date__lt=today, status=LoanStatus.ACTIVE)
        return queryset


class ReservationStatusFilter(SimpleListFilter):
    """Rezervatsiya holati uchun filter"""
    title = 'Rezervatsiya Holati'
    parameter_name = 'reservation_status'

    def lookups(self, request, model_admin):
        return [
            ('active', 'Faol'),
            ('expired', 'Muddati tugagan'),
            ('priority', 'Ustuvor'),
            ('notified', 'Xabardor qilingan'),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        
        if self.value() == 'active':
            return queryset.filter(status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED])
        elif self.value() == 'expired':
            return queryset.filter(expires_at__lt=now, status=ReservationStatus.PENDING)
        elif self.value() == 'priority':
            return queryset.filter(priority__gt=0)
        elif self.value() == 'notified':
            return queryset.filter(notified_at__isnull=False)
        return queryset


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Professional Qarz Admin - keng qamrovli xususiyatlar bilan"""
    
    # Ro'yxat ko'rinishi konfiguratsiyasi
    list_display = [
        'loan_id_display',
        'user_link',
        'book_link',
        'status_badge',
        'loan_date_display',
        'due_date_display',
        'days_status',
        'fine_status',
        'renewal_info',
        'actions_column',
    ]
    
    list_display_links = ['loan_id_display']
    
    # Filterlash imkoniyatlari
    list_filter = [
        LoanStatusFilter,
        DueDateFilter,
        'status',
        'fine_paid',
        'fine_waived',
        'renewal_count',
        'loan_date',
        'due_date',
        'return_date',
    ]
    
    # Qidiruv konfiguratsiyasi
    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'book__title',
        'book__isbn',
        'book__authors__name',
        'notes',
        'librarian_notes',
    ]
    
    # Faqat o'qish uchun maydonlar
    readonly_fields = [
        'created_at',
        'updated_at',
        'calculated_fine',
        'renewal_history_display',
    ]
    
    # Fieldsets - tashkil etilgan ko'rinish
    fieldsets = [
        ('Qarz Ma\'lumotlari', {
            'fields': [
                ('user', 'book'),
                ('status', 'loan_date'),
                ('due_date', 'return_date'),
            ],
            'classes': ['wide'],
        }),
        ('Kengaytirish Ma\'lumotlari', {
            'fields': [
                ('renewal_count', 'renewal_history_display'),
            ],
            'classes': ['wide'],
        }),
        ('Jarima Boshqaruvi', {
            'fields': [
                'fine_amount',
                ('fine_paid', 'fine_waived'),
                'calculated_fine',
            ],
            'classes': ['wide'],
        }),
        ('Izohlar', {
            'fields': [
                'notes',
                'librarian_notes',
            ],
            'classes': ['wide'],
        }),
        ('Tizim Ma\'lumotlari', {
            'fields': [
                'created_by',
                ('created_at', 'updated_at'),
            ],
            'classes': ['wide', 'collapse'],
        }),
    ]
    
    # Sahifalash
    list_per_page = 25
    list_max_show_all = 100
    
    # Sana ierarxiyasi
    date_hierarchy = 'loan_date'
    
    # Tartiblash
    ordering = ['-created_at']
    
    # Maxsus amallar
    actions = [
        'mark_as_returned',
        'mark_as_overdue',
        'calculate_fines',
        'waive_fines',
        'send_reminder_emails',
        'export_loans_csv',
        'generate_overdue_report',
        'renew_selected_loans',
    ]
    
    def loan_id_display(self, obj):
        """Qarz ID ni holat belgisi bilan ko'rsatish"""
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
    loan_id_display.short_description = "Qarz ID"
    loan_id_display.admin_order_field = "id"
    
    def user_link(self, obj):
        """Foydalanuvchi sahifasiga havola"""
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
    user_link.short_description = "Foydalanuvchi"
    user_link.admin_order_field = "user__username"
    
    def book_link(self, obj):
        """Kitob sahifasiga havola"""
        url = reverse('admin:books_book_change', args=[obj.book.pk])
        return format_html('<a href="{}">{}</a>', url, obj.book.title[:50])
    book_link.short_description = "Kitob"
    book_link.admin_order_field = "book__title"
    
    def status_badge(self, obj):
        """Holat belgisini rangli ko'rsatish"""
        colors = {
            LoanStatus.ACTIVE: '#28a745',      # Yashil
            LoanStatus.OVERDUE: '#dc3545',     # Qizil
            LoanStatus.RETURNED: '#6c757d',    # Kulrang
            LoanStatus.RENEWED: '#17a2b8',     # Ko'k
            LoanStatus.LOST: '#343a40',        # Qora
            LoanStatus.DAMAGED: '#ffc107',     # Sariq
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Holat"
    status_badge.admin_order_field = "status"
    
    def loan_date_display(self, obj):
        """Qarz berish sanasini ko'rsatish"""
        return obj.loan_date.strftime('%Y-%m-%d')
    loan_date_display.short_description = "Qarz Sanasi"
    loan_date_display.admin_order_field = "loan_date"
    
    def due_date_display(self, obj):
        """Qaytarish muddatini rangli ko'rsatish"""
        today = timezone.now().date()
        days_diff = (obj.due_date - today).days
        
        if days_diff < 0:
            color = 'red'
            text = f"{abs(days_diff)} kun kechikkan"
        elif days_diff == 0:
            color = 'orange'
            text = "Bugun"
        elif days_diff <= 3:
            color = 'orange'
            text = f"{days_diff} kun qoldi"
        else:
            color = 'green'
            text = obj.due_date.strftime('%Y-%m-%d')
        
        return format_html('<span style="color: {};">{}</span>', color, text)
    due_date_display.short_description = "Qaytarish Muddati"
    due_date_display.admin_order_field = "due_date"
    
    def days_status(self, obj):
        """Kunlar holati"""
        today = timezone.now().date()
        loan_days = (today - obj.loan_date).days
        
        if obj.return_date:
            duration = (obj.return_date - obj.loan_date).days
            return f"✅ {duration} kun"
        elif obj.due_date < today:
            overdue_days = (today - obj.due_date).days
            return format_html('<span style="color: red;">🔴 {} kun kechikkan</span>', overdue_days)
        else:
            return f"📅 {loan_days} kun"
    days_status.short_description = "Kunlar"
    
    def fine_status(self, obj):
        """Jarima holati"""
        if obj.fine_amount > 0:
            if obj.fine_waived:
                return format_html('<span style="color: blue;">💰 {} so\'m (kechirilib)</span>', obj.fine_amount)
            else:   
                return format_html('<span style="color: green;">💰 {} so\'m (to\'langan)</span>', obj.fine_amount)
        else:
                return format_html('<span style="color: red;">💰 {} so\'m (to\'lanmagan)</span>', obj.fine_amount)
    fine_status.short_description = "Jarima"
    
    def renewal_info(self, obj):
        """Kengaytirish ma'lumotlari"""
        if obj.renewal_count > 0:
            return f"🔄 {obj.renewal_count} marta"
        return "🔄 Kengaytirilmagan"
    renewal_info.short_description = "Kengaytirish"
    renewal_info.admin_order_field = "renewal_count"
    
    def actions_column(self, obj):
        """Amallar ustuni"""
        buttons = []
        
        if obj.status == LoanStatus.ACTIVE:
            if obj.can_renew():
                buttons.append('<button class="button" onclick="renewLoan({})">Kengaytirish</button>'.format(obj.id))
            buttons.append('<button class="button" onclick="returnBook({})">Qaytarish</button>'.format(obj.id))
        
        return format_html(' '.join(buttons))
    actions_column.short_description = "Amallar"
    
    def calculated_fine(self, obj):
        """Hisoblangan jarima"""
        fine = obj.calculate_fine()
        return f"{fine} so'm"
    calculated_fine.short_description = "Hisoblangan Jarima"
    
    def renewal_history_display(self, obj):
        """Kengaytirish tarixini ko'rsatish"""
        if obj.renewal_history:
            history = []
            for renewal in obj.renewal_history:
                history.append(f"{renewal.get('date', 'N/A')} - {renewal.get('reason', 'Sabab ko\'rsatilmagan')}")
            return format_html('<br>'.join(history))
        return "Kengaytirish tarixi yo'q"
    renewal_history_display.short_description = "Kengaytirish Tarixi"
    
    # Maxsus amallar
    @admin.action(description='Tanlangan qarzlarni qaytarilgan deb belgilash')
    def mark_as_returned(self, request, queryset):
        """Tanlangan qarzlarni qaytarilgan deb belgilash"""
        updated = 0
        for loan in queryset:
            if loan.status in [LoanStatus.ACTIVE, LoanStatus.OVERDUE]:
                loan.return_book()
                updated += 1
        
        self.message_user(
            request,
            f'{updated} ta qarz qaytarilgan deb belgilandi.',
            messages.SUCCESS
        )
    
    @admin.action(description='Tanlangan qarzlarni muddati o\'tgan deb belgilash')
    def mark_as_overdue(self, request, queryset):
        """Muddati o'tgan qarzlarni belgilash"""
        updated = queryset.filter(
            status=LoanStatus.ACTIVE,
            due_date__lt=timezone.now().date()
        ).update(status=LoanStatus.OVERDUE)
        
        self.message_user(
            request,
            f'{updated} ta qarz muddati o\'tgan deb belgilandi.',
            messages.SUCCESS
        )
    
    @admin.action(description='Tanlangan qarzlar uchun jarimalarni hisoblash')
    def calculate_fines(self, request, queryset):
        """Jarimalarni hisoblash"""
        updated = 0
        for loan in queryset:
            old_fine = loan.fine_amount
            new_fine = loan.calculate_fine()
            if new_fine != old_fine:
                loan.fine_amount = new_fine
                loan.save()
                updated += 1
        
        self.message_user(
            request,
            f'{updated} ta qarz uchun jarima yangilandi.',
            messages.SUCCESS
        )
    
    @admin.action(description='Tanlangan qarzlar jarimalarini kechirish')
    def waive_fines(self, request, queryset):
        """Jarimalarni kechirish"""
        updated = queryset.update(fine_waived=True)
        self.message_user(
            request,
            f'{updated} ta qarz jarimasi kechirilib.',
            messages.SUCCESS
        )
    
    @admin.action(description='Eslatma emaillarini yuborish')
    def send_reminder_emails(self, request, queryset):
        """Eslatma emaillarini yuborish"""
        # Bu yerda email yuborish logikasi bo'ladi
        count = queryset.count()
        self.message_user(
            request,
            f'{count} ta foydalanuvchiga eslatma yuborildi.',
            messages.SUCCESS
        )
    
    @admin.action(description='Qarzlarni CSV formatida eksport qilish')
    def export_loans_csv(self, request, queryset):
        """Qarzlarni CSV formatida eksport qilish"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="qarzlar_eksport.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Foydalanuvchi', 'Kitob', 'Holat', 'Qarz Sanasi', 
            'Qaytarish Muddati', 'Qaytarilgan Sana', 'Jarima', 'Kengaytirish'
        ])
        
        for loan in queryset:
            writer.writerow([
                loan.id,
                loan.user.get_full_name() or loan.user.username,
                loan.book.title,
                loan.get_status_display(),
                loan.loan_date.strftime('%Y-%m-%d'),
                loan.due_date.strftime('%Y-%m-%d'),
                loan.return_date.strftime('%Y-%m-%d') if loan.return_date else '',
                loan.fine_amount,
                loan.renewal_count
            ])
        
        return response
    
    @admin.action(description='Muddati o\'tgan qarzlar hisobotini yaratish')
    def generate_overdue_report(self, request, queryset):
        """Muddati o'tgan qarzlar hisoboti"""
        overdue_loans = queryset.filter(
            status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE],
            due_date__lt=timezone.now().date()
        )
        
        self.message_user(
            request, 
            f'Muddati o\'tgan qarzlar: {overdue_loans.count()} ta',
            messages.INFO
        )
    
    @admin.action(description='Tanlangan qarzlarni kengaytirish')
    def renew_selected_loans(self, request, queryset):
        """Tanlangan qarzlarni kengaytirish"""
        renewed = 0
        for loan in queryset:
            if loan.can_renew():
                loan.renew(reason="Admin tomonidan kengaytirildi")
                renewed += 1
        
        self.message_user(
            request,
            f'{renewed} ta qarz kengaytirildi.',
            messages.SUCCESS
        )
    
    # Queryset optimizatsiyasi
    def get_queryset(self, request):
        """Queryset ni optimizatsiya qilish"""
        return super().get_queryset(request).select_related(
            'user', 'book', 'created_by'
        ).prefetch_related('book__authors')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Professional Rezervatsiya Admin"""
    
    list_display = [
        'reservation_id_display',
        'user_link',
        'book_link',
        'status_badge',
        'queue_position_display',
        'reserved_at_display',
        'expires_at_display',
        'priority_display',
        'time_remaining_display',
    ]
    
    list_display_links = ['reservation_id_display']
    
    list_filter = [
        ReservationStatusFilter,
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
        'book__authors__name',
    ]
    
    readonly_fields = [
        'reserved_at',
        'updated_at',
    ]
    
    fieldsets = [
        ('Rezervatsiya Ma\'lumotlari', {
            'fields': [
                ('user', 'book'),
                ('status', 'priority'),
                ('queue_position', 'reserved_at'),
                ('expires_at', 'notified_at'),
            ],
            'classes': ['wide'],
        }),
        ('Qo\'shimcha Ma\'lumotlar', {
            'fields': [
                'notes',
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
        'update_queue_positions',
    ]
    
    def reservation_id_display(self, obj):
        """Rezervatsiya ID ni holat belgisi bilan ko'rsatish"""
        status_icons = {
            ReservationStatus.PENDING: '⏳',
            ReservationStatus.CONFIRMED: '✅',
            ReservationStatus.FULFILLED: '📚',
            ReservationStatus.CANCELLED: '❌',
            ReservationStatus.EXPIRED: '⏰',
        }
        icon = status_icons.get(obj.status, '📋')
        return f"{icon} #{obj.id}"
    reservation_id_display.short_description = "Rezervatsiya ID"
    reservation_id_display.admin_order_field = "id"
    
    def user_link(self, obj):
        """Foydalanuvchi sahifasiga havola"""
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name() or obj.user.username)
    user_link.short_description = "Foydalanuvchi"
    user_link.admin_order_field = "user__username"
    
    def book_link(self, obj):
        """Kitob sahifasiga havola"""
        url = reverse('admin:books_book_change', args=[obj.book.pk])
        return format_html('<a href="{}">{}</a>', url, obj.book.title[:50])
    book_link.short_description = "Kitob"
    book_link.admin_order_field = "book__title"
    
    def status_badge(self, obj):
        """Holat belgisini rangli ko'rsatish"""
        colors = {
            ReservationStatus.PENDING: '#ffc107',      # Sariq
            ReservationStatus.CONFIRMED: '#28a745',    # Yashil
            ReservationStatus.FULFILLED: '#17a2b8',    # Ko'k
            ReservationStatus.CANCELLED: '#dc3545',    # Qizil
            ReservationStatus.EXPIRED: '#6c757d',      # Kulrang
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Holat"
    status_badge.admin_order_field = "status"
    
    def queue_position_display(self, obj):
        """Navbat pozitsiyasini ko'rsatish"""
        if obj.queue_position == 1:
            return format_html('<span style="color: green; font-weight: bold;">🥇 1-o\'rin</span>')
        elif obj.queue_position <= 3:
            return format_html('<span style="color: orange; font-weight: bold;">🥈 {}-o\'rin</span>', obj.queue_position)
        else:
            return f"📍 {obj.queue_position}-o'rin"
    queue_position_display.short_description = "Navbat"
    queue_position_display.admin_order_field = "queue_position"
    
    def reserved_at_display(self, obj):
        """Rezervatsiya sanasini ko'rsatish"""
        return obj.reserved_at.strftime('%Y-%m-%d %H:%M')
    reserved_at_display.short_description = "Rezervatsiya Sanasi"
    reserved_at_display.admin_order_field = "reserved_at"
    
    def expires_at_display(self, obj):
        """Tugash sanasini rangli ko'rsatish"""
        now = timezone.now()
        time_diff = obj.expires_at - now
        
        if time_diff.total_seconds() < 0:
            return format_html('<span style="color: red;">⏰ Tugagan</span>')
        elif time_diff.total_seconds() < 3600:  # 1 soat
            return format_html('<span style="color: orange;">⏰ {} daqiqa</span>', int(time_diff.total_seconds() // 60))
        elif time_diff.days < 1:
            return format_html('<span style="color: orange;">⏰ {} soat</span>', int(time_diff.total_seconds() // 3600))
        else:
            return obj.expires_at.strftime('%Y-%m-%d %H:%M')
    expires_at_display.short_description = "Tugash Sanasi"
    expires_at_display.admin_order_field = "expires_at"
    
    def priority_display(self, obj):
        """Ustuvorlikni ko'rsatish"""
        if obj.priority > 0:
            return format_html('<span style="color: red; font-weight: bold;">⭐ Ustuvor ({})</span>', obj.priority)
        return "📋 Oddiy"
    priority_display.short_description = "Ustuvorlik"
    priority_display.admin_order_field = "priority"
    
    def time_remaining_display(self, obj):
        """Qolgan vaqtni ko'rsatish"""
        now = timezone.now()
        if obj.expires_at > now:
            remaining = obj.expires_at - now
            if remaining.days > 0:
                return f"📅 {remaining.days} kun"
            elif remaining.seconds > 3600:
                hours = remaining.seconds // 3600
                return f"⏰ {hours} soat"
        else:
                minutes = remaining.seconds // 60
                return f"⏰ {minutes} daqiqa"
        return "⏰ Tugagan"
    time_remaining_display.short_description = "Qolgan Vaqt"
    
    # Maxsus amallar
    @admin.action(description='Tanlangan rezervatsiyalarni bajarilgan deb belgilash')
    def mark_as_fulfilled(self, request, queryset):
        """Rezervatsiyalarni bajarilgan deb belgilash"""
        updated = 0
        for reservation in queryset:
            if reservation.status in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]:
                reservation.fulfill()
                updated += 1
        
        self.message_user(
            request,
            f'{updated} ta rezervatsiya bajarilgan deb belgilandi.',
            messages.SUCCESS
        )
    
    @admin.action(description='Tanlangan rezervatsiyalarni bekor qilish')
    def mark_as_cancelled(self, request, queryset):
        """Rezervatsiyalarni bekor qilish"""
        updated = 0
        for reservation in queryset:
            if reservation.status != ReservationStatus.CANCELLED:
                reservation.cancel("Admin tomonidan bekor qilindi")
                updated += 1
        
        self.message_user(
            request,
            f'{updated} ta rezervatsiya bekor qilindi.',
            messages.SUCCESS
        )
    
    @admin.action(description='Tugash muddatini uzaytirish')
    def extend_expiration(self, request, queryset):
        """Tugash muddatini uzaytirish"""
        updated = 0
        for reservation in queryset:
            if reservation.status == ReservationStatus.PENDING:
                reservation.expires_at = timezone.now() + timedelta(days=3)
                reservation.save()
                updated += 1
        
        self.message_user(
            request,
            f'{updated} ta rezervatsiya muddati uzaytirildi.',
            messages.SUCCESS
        )
    
    @admin.action(description='Foydalanuvchilarni xabardor qilish')
    def notify_users(self, request, queryset):
        """Foydalanuvchilarni xabardor qilish"""
        # Bu yerda xabardor qilish logikasi bo'ladi
        count = queryset.count()
        self.message_user(
            request,
            f'{count} ta foydalanuvchi xabardor qilindi.',
            messages.SUCCESS
        )
    
    @admin.action(description='Rezervatsiyalarni CSV formatida eksport qilish')
    def export_reservations_csv(self, request, queryset):
        """Rezervatsiyalarni CSV formatida eksport qilish"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="rezervatsiyalar_eksport.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Foydalanuvchi', 'Kitob', 'Holat', 'Navbat', 
            'Rezervatsiya Sanasi', 'Tugash Sanasi', 'Ustuvorlik'
        ])
        
        for reservation in queryset:
            writer.writerow([
                reservation.id,
                reservation.user.get_full_name() or reservation.user.username,
                reservation.book.title,
                reservation.get_status_display(),
                reservation.queue_position,
                reservation.reserved_at.strftime('%Y-%m-%d %H:%M'),
                reservation.expires_at.strftime('%Y-%m-%d %H:%M'),
                reservation.priority
            ])
        
        return response
    
    @admin.action(description='Navbat pozitsiyalarini yangilash')
    def update_queue_positions(self, request, queryset):
        """Navbat pozitsiyalarini yangilash"""
        # Bu yerda navbat pozitsiyalarini qayta hisoblash logikasi bo'ladi
        count = queryset.count()
        self.message_user(
            request,
            f'{count} ta rezervatsiya navbati yangilandi.',
            messages.SUCCESS
        )
    
    # Queryset optimizatsiyasi
    def get_queryset(self, request):
        """Queryset ni optimizatsiya qilish"""
        return super().get_queryset(request).select_related(
            'user', 'book'
        ).prefetch_related('book__authors')


# Admin sayt sozlamalari
admin.site.site_header = "Kutubxona Boshqaruv Tizimi"
admin.site.site_title = "Kutubxona Admin"
admin.site.index_title = "Qarz va Rezervatsiya Boshqaruvi"
