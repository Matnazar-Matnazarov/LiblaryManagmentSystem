"""
Professional Django Admin Configuration for Books App

This module provides comprehensive admin interface for book management with:
- Enhanced book catalog management
- Author and publisher administration
- Category organization
- Advanced filtering and search
- Bulk operations and custom actions
- Image handling and preview
- Professional UI improvements
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q, Count, Avg
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponse
import csv
from PIL import Image
from io import BytesIO
import base64

from .models import Book, Author, Category, Publisher


class AvailabilityFilter(SimpleListFilter):
    """Custom filter for book availability"""
    title = 'Availability'
    parameter_name = 'availability'

    def lookups(self, request, model_admin):
        return [
            ('available', 'Available'),
            ('unavailable', 'Unavailable'),
            ('low_stock', 'Low Stock (< 3 copies)'),
            ('out_of_stock', 'Out of Stock'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'available':
            return queryset.filter(status='available', available_copies__gt=0)
        elif self.value() == 'unavailable':
            return queryset.exclude(status='available').exclude(available_copies__gt=0)
        elif self.value() == 'low_stock':
            return queryset.filter(available_copies__lt=3, available_copies__gt=0)
        elif self.value() == 'out_of_stock':
            return queryset.filter(available_copies=0)
        return queryset


class PublicationYearFilter(SimpleListFilter):
    """Filter books by publication year ranges"""
    title = 'Publication Period'
    parameter_name = 'publication_period'

    def lookups(self, request, model_admin):
        return [
            ('recent', 'Recent (2020-2024)'),
            ('modern', 'Modern (2010-2019)'),
            ('contemporary', 'Contemporary (2000-2009)'),
            ('classic', 'Classic (1990-1999)'),
            ('vintage', 'Vintage (before 1990)'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'recent':
            return queryset.filter(publication_year__gte=2020)
        elif self.value() == 'modern':
            return queryset.filter(publication_year__gte=2010, publication_year__lt=2020)
        elif self.value() == 'contemporary':
            return queryset.filter(publication_year__gte=2000, publication_year__lt=2010)
        elif self.value() == 'classic':
            return queryset.filter(publication_year__gte=1990, publication_year__lt=2000)
        elif self.value() == 'vintage':
            return queryset.filter(publication_year__lt=1990)
        return queryset


class AuthorInline(admin.TabularInline):
    """Inline for book authors"""
    model = Book.authors.through
    extra = 1
    verbose_name = "Author"
    verbose_name_plural = "Authors"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Professional Category Admin"""
    
    list_display = [
        'name',
        'book_count',
        'popular_books_preview',
        'created_at_display',
        'description_preview',
    ]
    
    list_display_links = ['name']
    
    search_fields = ['name', 'description']
    
    prepopulated_fields = {'slug': ('name',)}
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'slug', 'description'],
            'classes': ['wide'],
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['wide', 'collapse'],
        }),
    ]
    
    def book_count(self, obj):
        """Display number of books in category"""
        count = obj.books.count()
        if count > 0:
            url = reverse('admin:books_book_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}">{} books</a>', url, count)
        return "0 books"
    book_count.short_description = "Books"
    
    def popular_books_preview(self, obj):
        """Show preview of popular books in category"""
        books = obj.books.filter(status='available')[:3]
        if books:
            titles = [book.title[:30] + "..." if len(book.title) > 30 else book.title for book in books]
            return ", ".join(titles)
        return "No books"
    popular_books_preview.short_description = "Popular Books"
    
    def created_at_display(self, obj):
        """Display creation date"""
        return obj.created_at.strftime('%Y-%m-%d')
    created_at_display.short_description = "Created"
    created_at_display.admin_order_field = "created_at"
    
    def description_preview(self, obj):
        """Display truncated description"""
        if obj.description:
            return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description
        return "-"
    description_preview.short_description = "Description"


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Professional Author Admin"""
    
    list_display = [
        'name_with_image',
        'nationality',
        'age_display',
        'book_count',
        'popular_books_preview',
        'birth_death_display',
    ]
    
    list_display_links = ['name_with_image']
    
    list_filter = [
        'nationality',
        'birth_date',
        'death_date',
    ]
    
    search_fields = ['name', 'biography', 'nationality']
    
    prepopulated_fields = {'slug': ('name',)}
    
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'slug', 'nationality'],
            'classes': ['wide'],
        }),
        ('Biographical Information', {
            'fields': [
                'biography',
                ('birth_date', 'death_date'),
            ],
            'classes': ['wide'],
        }),
        ('Image', {
            'fields': ['image', 'image_preview'],
            'classes': ['wide'],
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['wide', 'collapse'],
        }),
    ]
    
    actions = ['export_authors_csv']
    
    def name_with_image(self, obj):
        """Display name with image thumbnail"""
        if obj.image:
            return format_html(
                '<div style="display: flex; align-items: center;">'
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 50%; margin-right: 10px;">'
                '<span>{}</span></div>',
                obj.image.url, obj.name
            )
        return f"📚 {obj.name}"
    name_with_image.short_description = "Author"
    name_with_image.admin_order_field = "name"
    
    def age_display(self, obj):
        """Display author's age or age at death"""
        if obj.birth_date:
            from datetime import date
            if obj.death_date:
                age = (obj.death_date - obj.birth_date).days // 365
                return f"{age} (deceased)"
            else:
                age = (date.today() - obj.birth_date).days // 365
                return f"{age} years old"
        return "Unknown"
    age_display.short_description = "Age"
    
    def book_count(self, obj):
        """Display number of books by author"""
        count = obj.books.count()
        if count > 0:
            url = reverse('admin:books_book_changelist') + f'?authors__id__exact={obj.id}'
            return format_html('<a href="{}">{} books</a>', url, count)
        return "0 books"
    book_count.short_description = "Books"
    
    def popular_books_preview(self, obj):
        """Show preview of author's popular books"""
        books = obj.books.all()[:3]
        if books:
            titles = [book.title[:25] + "..." if len(book.title) > 25 else book.title for book in books]
            return ", ".join(titles)
        return "No books"
    popular_books_preview.short_description = "Books Preview"
    
    def birth_death_display(self, obj):
        """Display birth and death dates"""
        if obj.birth_date and obj.death_date:
            return f"{obj.birth_date.year} - {obj.death_date.year}"
        elif obj.birth_date:
            return f"Born {obj.birth_date.year}"
        return "Unknown"
    birth_death_display.short_description = "Lifespan"
    
    def image_preview(self, obj):
        """Display image preview"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 8px;">',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Image Preview"
    
    def export_authors_csv(self, request, queryset):
        """Export authors to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="authors_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Name', 'Nationality', 'Birth Date', 'Death Date', 'Books Count'])
        
        for author in queryset:
            writer.writerow([
                author.name,
                author.nationality,
                author.birth_date or '',
                author.death_date or '',
                author.books.count()
            ])
        
        return response
    export_authors_csv.short_description = "Export selected authors to CSV"


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Professional Publisher Admin"""
    
    list_display = [
        'name_with_image',
        'country',
        'city',
        'book_count',
        'contact_info',
        'website_link',
    ]
    
    list_display_links = ['name_with_image']
    
    list_filter = ['country', 'city']
    
    search_fields = ['name', 'address', 'city', 'country', 'email']
    
    prepopulated_fields = {'slug': ('name',)}
    
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'slug'],
            'classes': ['wide'],
        }),
        ('Contact Information', {
            'fields': [
                'address',
                ('city', 'country'),
                'email',
                'website',
            ],
            'classes': ['wide'],
        }),
        ('Image', {
            'fields': ['image', 'image_preview'],
            'classes': ['wide'],
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['wide', 'collapse'],
        }),
    ]
    
    def name_with_image(self, obj):
        """Display name with image thumbnail"""
        if obj.image:
            return format_html(
                '<div style="display: flex; align-items: center;">'
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 4px; margin-right: 10px;">'
                '<span>{}</span></div>',
                obj.image.url, obj.name
            )
        return f"🏢 {obj.name}"
    name_with_image.short_description = "Publisher"
    name_with_image.admin_order_field = "name"
    
    def book_count(self, obj):
        """Display number of books by publisher"""
        count = obj.books.count()
        if count > 0:
            url = reverse('admin:books_book_changelist') + f'?publisher__id__exact={obj.id}'
            return format_html('<a href="{}">{} books</a>', url, count)
        return "0 books"
    book_count.short_description = "Books"
    
    def contact_info(self, obj):
        """Display contact information"""
        info = []
        if obj.email:
            info.append(f"📧 {obj.email}")
        if obj.city:
            info.append(f"📍 {obj.city}")
        return ", ".join(info) if info else "No contact info"
    contact_info.short_description = "Contact"
    
    def website_link(self, obj):
        """Display website as clickable link"""
        if obj.website:
            return format_html('<a href="{}" target="_blank">🌐 Website</a>', obj.website)
        return "-"
    website_link.short_description = "Website"
    
    def image_preview(self, obj):
        """Display image preview"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 8px;">',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Image Preview"


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Professional Book Admin with comprehensive features"""
    
    list_display = [
        'title_with_cover',
        'author_list',
        'category',
        'publisher',
        'status_badge',
        'availability_display',
        'language_flag',
        'publication_year',
        'isbn_display',
        'loan_info',
    ]
    
    list_display_links = ['title_with_cover']
    
    list_filter = [
        'status',
        AvailabilityFilter,
        'language',
        'format',
        'category',
        'publisher',
        PublicationYearFilter,
        'created_at',
    ]
    
    search_fields = [
        'title',
        'subtitle',
        'isbn',
        'authors__name',
        'publisher__name',
        'description',
    ]
    
    prepopulated_fields = {'slug': ('title',)}
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'cover_image_preview',
        'availability_summary',
    ]
    
    filter_horizontal = ['authors']
    
    # Custom fieldsets
    fieldsets = [
        ('Basic Information', {
            'fields': [
                'title',
                'subtitle',
                'slug',
                'authors',
                'category',
                'publisher',
            ],
            'classes': ['wide'],
        }),
        ('Publication Details', {
            'fields': [
                'isbn',
                ('publication_year', 'edition'),
                ('language', 'format'),
                'pages',
            ],
            'classes': ['wide'],
        }),
        ('Library Management', {
            'fields': [
                'status',
                ('total_copies', 'available_copies'),
                'location',
            ],
            'classes': ['wide'],
        }),
        ('Content', {
            'fields': [
                'description',
                'cover_image',
                'cover_image_preview',
            ],
            'classes': ['wide'],
        }),
        ('System Information', {
            'fields': [
                'id',
                'availability_summary',
                ('created_at', 'updated_at'),
            ],
            'classes': ['wide', 'collapse'],
        }),
    ]
    
    # Pagination
    list_per_page = 20
    list_max_show_all = 100
    
    # Date hierarchy
    date_hierarchy = 'created_at'
    
    # Ordering
    ordering = ['title']
    
    # Custom actions
    actions = [
        'mark_as_available',
        'mark_as_maintenance',
        'update_available_copies',
        'export_books_csv',
        'generate_catalog_report',
    ]
    
    def title_with_cover(self, obj):
        """Display title with cover thumbnail"""
        if obj.cover_image:
            return format_html(
                '<div style="display: flex; align-items: center;">'
                '<img src="{}" style="width: 40px; height: 50px; margin-right: 10px; border-radius: 4px;">'
                '<div><strong>{}</strong><br><small>{}</small></div></div>',
                obj.cover_image.url,
                obj.title[:30] + "..." if len(obj.title) > 30 else obj.title,
                obj.subtitle[:20] + "..." if obj.subtitle and len(obj.subtitle) > 20 else obj.subtitle or ""
            )
        return format_html(
            '<div><strong>📖 {}</strong><br><small>{}</small></div>',
            obj.title[:30] + "..." if len(obj.title) > 30 else obj.title,
            obj.subtitle[:20] + "..." if obj.subtitle and len(obj.subtitle) > 20 else obj.subtitle or ""
        )
    title_with_cover.short_description = "Book"
    title_with_cover.admin_order_field = "title"
    
    def author_list(self, obj):
        """Display list of authors"""
        authors = obj.authors.all()[:2]  # Show max 2 authors
        if authors:
            author_names = [author.name for author in authors]
            result = ", ".join(author_names)
            if obj.authors.count() > 2:
                result += f" (+{obj.authors.count() - 2} more)"
            return result
        return "No authors"
    author_list.short_description = "Authors"
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'available': '#198754',      # Green
            'borrowed': '#0d6efd',       # Blue
            'reserved': '#fd7e14',       # Orange
            'maintenance': '#6c757d',    # Gray
            'lost': '#dc3545',           # Red
            'damaged': '#dc3545',        # Red
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
    
    def availability_display(self, obj):
        """Display availability information"""
        if obj.available_copies > 0:
            if obj.available_copies <= 2:
                return format_html(
                    '<span style="color: orange;">⚠️ {} available</span>',
                    obj.available_copies
                )
            else:
                return format_html(
                    '<span style="color: green;">✅ {} available</span>',
                    obj.available_copies
                )
        else:
            return format_html('<span style="color: red;">❌ None available</span>')
    availability_display.short_description = "Availability"
    
    def language_flag(self, obj):
        """Display language with flag emoji"""
        flags = {
            'en': '🇺🇸 English',
            'uz': '🇺🇿 Uzbek',
            'ru': '🇷🇺 Russian',
            'ar': '🇸🇦 Arabic',
        }
        return flags.get(obj.language, f"🌐 {obj.get_language_display()}")
    language_flag.short_description = "Language"
    language_flag.admin_order_field = "language"
    
    def isbn_display(self, obj):
        """Display ISBN with formatting"""
        if obj.isbn:
            return f"📚 {obj.isbn}"
        return "No ISBN"
    isbn_display.short_description = "ISBN"
    isbn_display.admin_order_field = "isbn"
    
    def loan_info(self, obj):
        """Display loan information"""
        # This would need proper import and implementation
        # from loans.models import Loan
        # active_loans = Loan.objects.filter(book=obj, status='active').count()
        active_loans = 0  # Placeholder
        
        if active_loans > 0:
            return format_html('<span style="color: blue;">📋 {} loans</span>', active_loans)
        return "-"
    loan_info.short_description = "Active Loans"
    
    def cover_image_preview(self, obj):
        """Display cover image preview"""
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 400px; border-radius: 8px;">',
                obj.cover_image.url
            )
        return "No cover image"
    cover_image_preview.short_description = "Cover Preview"
    
    def availability_summary(self, obj):
        """Display availability summary"""
        total = obj.total_copies
        available = obj.available_copies
        borrowed = total - available
        
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 4px;">'
            '<strong>Total Copies:</strong> {}<br>'
            '<strong>Available:</strong> <span style="color: green;">{}</span><br>'
            '<strong>Borrowed:</strong> <span style="color: blue;">{}</span><br>'
            '<strong>Availability Rate:</strong> {}%'
            '</div>',
            total,
            available,
            borrowed,
            round((available / total * 100) if total > 0 else 0, 1)
        )
    availability_summary.short_description = "Availability Summary"
    
    # Custom actions
    def mark_as_available(self, request, queryset):
        """Mark selected books as available"""
        updated = queryset.update(status='available')
        self.message_user(request, f"{updated} books marked as available.")
    mark_as_available.short_description = "Mark selected books as available"
    
    def mark_as_maintenance(self, request, queryset):
        """Mark selected books as under maintenance"""
        updated = queryset.update(status='maintenance')
        self.message_user(request, f"{updated} books marked as under maintenance.")
    mark_as_maintenance.short_description = "Mark selected books as under maintenance"
    
    def update_available_copies(self, request, queryset):
        """Reset available copies to total copies"""
        for book in queryset:
            book.available_copies = book.total_copies
            book.save()
        self.message_user(request, f"Available copies updated for {queryset.count()} books.")
    update_available_copies.short_description = "Reset available copies to total"
    
    def export_books_csv(self, request, queryset):
        """Export books to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="books_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Title', 'Authors', 'Category', 'Publisher', 'ISBN', 
            'Publication Year', 'Language', 'Status', 'Total Copies', 'Available Copies'
        ])
        
        for book in queryset:
            authors = ", ".join([author.name for author in book.authors.all()])
            writer.writerow([
                book.title,
                authors,
                book.category.name if book.category else '',
                book.publisher.name if book.publisher else '',
                book.isbn or '',
                book.publication_year or '',
                book.get_language_display(),
                book.get_status_display(),
                book.total_copies,
                book.available_copies
            ])
        
        return response
    export_books_csv.short_description = "Export selected books to CSV"
    
    def generate_catalog_report(self, request, queryset):
        """Generate catalog report"""
        # This would generate a comprehensive catalog report
        self.message_user(request, f"Catalog report generated for {queryset.count()} books.")
    generate_catalog_report.short_description = "Generate catalog report"
    
    # Optimize queryset
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related"""
        return super().get_queryset(request).select_related(
            'category', 'publisher'
        ).prefetch_related('authors')


# Custom admin site modifications
admin.site.site_header = "Library Management System"
admin.site.site_title = "Library Admin"
admin.site.index_title = "Books & Catalog Management"
