"""
Professional Monitoring System for Library Management

Bu modul Django Prometheus bilan professional monitoring tizimini taqdim etadi:
- Custom business metrics
- Performance monitoring
- User activity tracking
- System health monitoring
- Real-time alerts
- Dashboard metrics
"""

from prometheus_client import Counter, Histogram, Gauge, Info, Enum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from django.core.cache import cache
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# =============================================================================
# BUSINESS METRICS - Kutubxona biznes ko'rsatkichlari
# =============================================================================

# Kitob qarz berish metrikalari
book_loans_total = Counter(
    'library_book_loans_total',
    'Jami kitob qarz berish soni',
    ['book_category', 'user_role', 'loan_status']
)

book_returns_total = Counter(
    'library_book_returns_total', 
    'Jami kitob qaytarish soni',
    ['book_category', 'return_status', 'is_late']
)

book_reservations_total = Counter(
    'library_book_reservations_total',
    'Jami kitob rezervatsiya soni', 
    ['book_category', 'user_role']
)

# Foydalanuvchi faoliyati metrikalari
user_registrations_total = Counter(
    'library_user_registrations_total',
    'Jami foydalanuvchi ro\'yxatdan o\'tish soni',
    ['user_role', 'registration_source']
)

user_logins_total = Counter(
    'library_user_logins_total',
    'Jami foydalanuvchi kirish soni',
    ['user_role', 'login_method']
)

user_searches_total = Counter(
    'library_user_searches_total',
    'Jami qidiruv so\'rovlari soni',
    ['search_type', 'user_role']
)

# Jarima metrikalari
fines_collected_total = Counter(
    'library_fines_collected_total',
    'Jami yig\'ilgan jarimalar',
    ['fine_type', 'payment_method']
)

fines_amount_total = Gauge(
    'library_fines_amount_total',
    'Jami jarima miqdori (so\'m)'
)

# =============================================================================
# PERFORMANCE METRICS - Tizim ishlash ko'rsatkichlari
# =============================================================================

# API response time
api_request_duration = Histogram(
    'library_api_request_duration_seconds',
    'API so\'rovlar davomiyligi (soniya)',
    ['method', 'endpoint', 'status_code'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Database query performance
db_query_duration = Histogram(
    'library_db_query_duration_seconds',
    'Ma\'lumotlar bazasi so\'rovlari davomiyligi',
    ['model', 'operation'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
)

# Cache performance
cache_operations_total = Counter(
    'library_cache_operations_total',
    'Kesh operatsiyalari soni',
    ['operation', 'cache_name', 'hit_miss']
)

# =============================================================================
# SYSTEM HEALTH METRICS - Tizim salomatligi ko'rsatkichlari
# =============================================================================

# Active users
active_users_gauge = Gauge(
    'library_active_users_total',
    'Hozirda faol foydalanuvchilar soni'
)

# Available books
available_books_gauge = Gauge(
    'library_available_books_total',
    'Mavjud kitoblar soni',
    ['category']
)

# System status
system_status = Enum(
    'library_system_status',
    'Tizim holati',
    states=['healthy', 'degraded', 'down']
)

# Error rates
error_rate_gauge = Gauge(
    'library_error_rate_percent',
    'Xatolik darajasi (foiz)',
    ['error_type']
)

# =============================================================================
# BUSINESS INTELLIGENCE METRICS - Biznes tahlil ko'rsatkichlari
# =============================================================================

# Popular books
popular_books_gauge = Gauge(
    'library_popular_books_score',
    'Mashhur kitoblar reytingi',
    ['book_id', 'book_title', 'category']
)

# User engagement
user_engagement_gauge = Gauge(
    'library_user_engagement_score',
    'Foydalanuvchi faollik darajasi',
    ['user_role', 'engagement_type']
)

# Library utilization
library_utilization_gauge = Gauge(
    'library_utilization_percent',
    'Kutubxona foydalanish darajasi (foiz)',
    ['resource_type']
)

# =============================================================================
# MONITORING FUNCTIONS - Monitoring funksiyalari
# =============================================================================

class LibraryMetricsCollector:
    """Professional metrics collector for library system"""
    
    def __init__(self):
        self.last_update = None
        self.update_interval = 300  # 5 daqiqa
    
    def should_update(self):
        """Yangilash kerakligini tekshirish"""
        if not self.last_update:
            return True
        return (timezone.now() - self.last_update).seconds >= self.update_interval
    
    def collect_all_metrics(self):
        """Barcha metrikallarni yig'ish"""
        if not self.should_update():
            return
        
        try:
            self.collect_user_metrics()
            self.collect_book_metrics()
            self.collect_system_metrics()
            self.collect_business_metrics()
            self.last_update = timezone.now()
            logger.info("Metrics successfully collected")
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
    
    def collect_user_metrics(self):
        """Foydalanuvchi metrikalari"""
        from accounts.models import User, UserRole
        
        # Faol foydalanuvchilar
        active_count = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(hours=24)
        ).count()
        active_users_gauge.set(active_count)
        
        # Rol bo'yicha foydalanuvchilar
        for role in UserRole.choices:
            role_count = User.objects.filter(role=role[0]).count()
            user_engagement_gauge.labels(
                user_role=role[0],
                engagement_type='total_users'
            ).set(role_count)
    
    def collect_book_metrics(self):
        """Kitob metrikalari"""
        from books.models import Book, Category
        
        # Kategoriya bo'yicha mavjud kitoblar
        for category in Category.objects.all():
            available_count = Book.objects.filter(
                category=category,
                available_copies__gt=0
            ).count()
            available_books_gauge.labels(category=category.name).set(available_count)
        
        # Kutubxona foydalanish darajasi
        total_books = Book.objects.count()
        borrowed_books = Book.objects.filter(available_copies=0).count()
        if total_books > 0:
            utilization = (borrowed_books / total_books) * 100
            library_utilization_gauge.labels(resource_type='books').set(utilization)
    
    def collect_system_metrics(self):
        """Tizim metrikalari"""
        try:
            # Tizim holati
            system_status.state('healthy')
            
            # Xatolik darajasi (cache dan olish)
            error_rate = cache.get('system_error_rate', 0)
            error_rate_gauge.labels(error_type='general').set(error_rate)
            
        except Exception as e:
            system_status.state('degraded')
            logger.error(f"System metrics collection error: {e}")
    
    def collect_business_metrics(self):
        """Biznes metrikalari"""
        from analytics.models import BookPopularity
        
        # Mashhur kitoblar
        popular_books = BookPopularity.objects.filter(
            popularity_score__gt=5.0
        ).select_related('book')[:10]
        
        for book_pop in popular_books:
            popular_books_gauge.labels(
                book_id=str(book_pop.book.id),
                book_title=book_pop.book.title[:50],
                category=book_pop.book.category.name if book_pop.book.category else 'Unknown'
            ).set(book_pop.popularity_score)


# Global metrics collector instance
metrics_collector = LibraryMetricsCollector()


# =============================================================================
# DECORATORS - Monitoring dekoratorlari
# =============================================================================

def monitor_api_performance(endpoint_name):
    """API performance monitoring decorator"""
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            start_time = time.time()
            method = request.method
            
            try:
                response = func(request, *args, **kwargs)
                status_code = response.status_code
                return response
            except Exception as e:
                status_code = 500
                raise
            finally:
                duration = time.time() - start_time
                api_request_duration.labels(
                    method=method,
                    endpoint=endpoint_name,
                    status_code=status_code
                ).observe(duration)
        
        return wrapper
    return decorator


def monitor_db_query(model_name, operation):
    """Database query monitoring decorator"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                db_query_duration.labels(
                    model=model_name,
                    operation=operation
                ).observe(duration)
        
        return wrapper
    return decorator


def monitor_cache_operation(cache_name):
    """Cache operation monitoring decorator"""
    def decorator(func):
        def wrapper(key, *args, **kwargs):
            operation = func.__name__
            
            try:
                result = func(key, *args, **kwargs)
                hit_miss = 'hit' if result is not None else 'miss'
                return result
            except Exception as e:
                hit_miss = 'error'
                raise
            finally:
                cache_operations_total.labels(
                    operation=operation,
                    cache_name=cache_name,
                    hit_miss=hit_miss
                ).inc()
        
        return wrapper
    return decorator


# =============================================================================
# SIGNAL HANDLERS - Signal ishlovchilari
# =============================================================================

@receiver(post_save, sender='loans.Loan')
def track_loan_creation(sender, instance, created, **kwargs):
    """Qarz berish yaratilishini kuzatish"""
    if created:
        book_loans_total.labels(
            book_category=instance.book.category.name if instance.book.category else 'Unknown',
            user_role=instance.user.role,
            loan_status=instance.status
        ).inc()


@receiver(post_save, sender='loans.Reservation')
def track_reservation_creation(sender, instance, created, **kwargs):
    """Rezervatsiya yaratilishini kuzatish"""
    if created:
        book_reservations_total.labels(
            book_category=instance.book.category.name if instance.book.category else 'Unknown',
            user_role=instance.user.role
        ).inc()


@receiver(post_save, sender='accounts.User')
def track_user_registration(sender, instance, created, **kwargs):
    """Foydalanuvchi ro'yxatdan o'tishini kuzatish"""
    if created:
        user_registrations_total.labels(
            user_role=instance.role,
            registration_source='web'
        ).inc()


# =============================================================================
# MIDDLEWARE INTEGRATION - Middleware integratsiyasi
# =============================================================================

class LibraryMonitoringMiddleware:
    """Custom monitoring middleware for library system"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Request boshlanishi
        start_time = time.time()
        
        # Metrics yig'ish
        metrics_collector.collect_all_metrics()
        
        response = self.get_response(request)
        
        # Response tugashi
        duration = time.time() - start_time
        
        # API metrics
        if request.path.startswith('/api/'):
            api_request_duration.labels(
                method=request.method,
                endpoint=request.path,
                status_code=response.status_code
            ).observe(duration)
        
        return response


# =============================================================================
# HEALTH CHECK FUNCTIONS - Sog'liqni tekshirish funksiyalari
# =============================================================================

def check_database_health():
    """Ma'lumotlar bazasi sog'ligini tekshirish"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def check_cache_health():
    """Kesh sog'ligini tekshirish"""
    try:
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        return result == 'ok'
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return False


def check_system_health():
    """Umumiy tizim sog'ligini tekshirish"""
    db_healthy = check_database_health()
    cache_healthy = check_cache_health()
    
    if db_healthy and cache_healthy:
        system_status.state('healthy')
        return True
    elif db_healthy or cache_healthy:
        system_status.state('degraded')
        return False
    else:
        system_status.state('down')
        return False


# =============================================================================
# CUSTOM METRICS FUNCTIONS - Maxsus metrikalar funksiyalari
# =============================================================================

def track_user_login(user, login_method='web'):
    """Foydalanuvchi kirishini kuzatish"""
    user_logins_total.labels(
        user_role=user.role,
        login_method=login_method
    ).inc()


def track_search_query(search_type, user_role):
    """Qidiruv so'rovini kuzatish"""
    user_searches_total.labels(
        search_type=search_type,
        user_role=user_role
    ).inc()


def track_fine_payment(fine_amount, fine_type, payment_method):
    """Jarima to'lovini kuzatish"""
    fines_collected_total.labels(
        fine_type=fine_type,
        payment_method=payment_method
    ).inc()
    
    # Jami jarima miqdorini yangilash
    current_total = fines_amount_total._value._value
    fines_amount_total.set(current_total + fine_amount)


def update_error_rate(error_type, error_count, total_requests):
    """Xatolik darajasini yangilash"""
    if total_requests > 0:
        error_percentage = (error_count / total_requests) * 100
        error_rate_gauge.labels(error_type=error_type).set(error_percentage)
        
        # Cache ga saqlash
        cache.set(f'error_rate_{error_type}', error_percentage, 300)


# =============================================================================
# ALERTING FUNCTIONS - Ogohlantirish funksiyalari
# =============================================================================

def check_critical_metrics():
    """Kritik metrikallarni tekshirish va ogohlantirish"""
    alerts = []
    
    # Xatolik darajasi yuqori bo'lsa
    error_rate = cache.get('system_error_rate', 0)
    if error_rate > 5:  # 5% dan yuqori
        alerts.append(f"High error rate detected: {error_rate}%")
    
    # Mavjud kitoblar kam bo'lsa
    total_books = cache.get('total_books_count', 0)
    available_books = cache.get('available_books_count', 0)
    if total_books > 0 and (available_books / total_books) < 0.1:  # 10% dan kam
        alerts.append("Low book availability: less than 10% books available")
    
    # Faol foydalanuvchilar kam bo'lsa
    active_users = cache.get('active_users_count', 0)
    if active_users < 10:
        alerts.append(f"Low user activity: only {active_users} active users")
    
    return alerts


# =============================================================================
# INITIALIZATION - Boshlang'ich sozlash
# =============================================================================

def initialize_monitoring():
    """Monitoring tizimini boshlang'ich sozlash"""
    logger.info("Initializing Library Monitoring System...")
    
    # Boshlang'ich metrikalarni yig'ish
    metrics_collector.collect_all_metrics()
    
    # Tizim sog'ligini tekshirish
    check_system_health()
    
    logger.info("Library Monitoring System initialized successfully")


# Auto-initialize when module is imported
initialize_monitoring() 