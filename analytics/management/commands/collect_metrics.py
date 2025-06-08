"""
Django Management Command for Metrics Collection

Bu command monitoring metrikalarini yig'ish va yangilash uchun ishlatiladi:
- Cron job orqali avtomatik ishga tushirish mumkin
- Manual metrikalar yig'ish
- System health monitoring
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta
import logging

from analytics.monitoring import (
    metrics_collector,
    check_system_health,
    check_critical_metrics,
    initialize_monitoring
)
from analytics.models import SystemStatistics

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Kutubxona tizimi uchun monitoring metrikalarini yig\'ish va yangilash'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Majburiy ravishda barcha metrikalarni yangilash',
        )
        
        parser.add_argument(
            '--daily-stats',
            action='store_true',
            help='Kunlik statistikalarni yaratish',
        )
        
        parser.add_argument(
            '--health-check',
            action='store_true',
            help='Faqat tizim sog\'ligini tekshirish',
        )
        
        parser.add_argument(
            '--alerts',
            action='store_true',
            help='Kritik ogohlantirishlarni tekshirish',
        )
    
    def handle(self, *args, **options):
        """Command ishga tushirish"""
        self.stdout.write(
            self.style.SUCCESS('📊 Monitoring metrikalarini yig\'ish boshlandi...')
        )
        
        try:
            # Monitoring tizimini boshlang'ich sozlash
            initialize_monitoring()
            
            if options['health_check']:
                self.perform_health_check()
            elif options['daily_stats']:
                self.generate_daily_stats()
            elif options['alerts']:
                self.check_alerts()
            else:
                self.collect_all_metrics(force=options['force'])
            
            self.stdout.write(
                self.style.SUCCESS('✅ Monitoring muvaffaqiyatli yakunlandi!')
            )
            
        except Exception as e:
            logger.error(f"Monitoring command error: {e}")
            raise CommandError(f'Monitoring xatosi: {e}')
    
    def collect_all_metrics(self, force=False):
        """Barcha metrikalarni yig'ish"""
        self.stdout.write('📈 Metrikalarni yig\'ish...')
        
        # Force yangilash
        if force:
            metrics_collector.last_update = None
        
        # Metrikalarni yig'ish
        metrics_collector.collect_all_metrics()
        
        # Cache ga tizim start time ni saqlash
        if not cache.get('system_start_time'):
            cache.set('system_start_time', timezone.now(), None)  # Never expire
        
        self.stdout.write(
            self.style.SUCCESS('✅ Metrikalar muvaffaqiyatli yig\'ildi')
        )
    
    def perform_health_check(self):
        """Tizim sog'ligini tekshirish"""
        self.stdout.write('🏥 Tizim sog\'ligini tekshirish...')
        
        health_status = check_system_health()
        
        if health_status:
            self.stdout.write(
                self.style.SUCCESS('✅ Tizim sog\'lom')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Tizimda muammolar aniqlandi')
            )
            
            # Kritik metrikalarni tekshirish
            alerts = check_critical_metrics()
            if alerts:
                self.stdout.write('⚠️  Ogohlantirishlar:')
                for alert in alerts:
                    self.stdout.write(f'   - {alert}')
    
    def generate_daily_stats(self):
        """Kunlik statistikalarni yaratish"""
        self.stdout.write('📊 Kunlik statistikalarni yaratish...')
        
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Statistika mavjudligini tekshirish
        if SystemStatistics.objects.filter(date=yesterday).exists():
            self.stdout.write(
                self.style.WARNING(f'⚠️  {yesterday} uchun statistika allaqachon mavjud')
            )
            return
        
        try:
            stats = self._calculate_daily_stats(yesterday)
            
            # Statistikani saqlash
            SystemStatistics.objects.create(**stats)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ {yesterday} uchun statistika yaratildi')
            )
            
        except Exception as e:
            logger.error(f"Daily stats generation error: {e}")
            self.stdout.write(
                self.style.ERROR(f'❌ Statistika yaratishda xato: {e}')
            )
    
    def check_alerts(self):
        """Ogohlantirishlarni tekshirish"""
        self.stdout.write('🚨 Ogohlantirishlarni tekshirish...')
        
        alerts = check_critical_metrics()
        
        if not alerts:
            self.stdout.write(
                self.style.SUCCESS('✅ Hech qanday kritik ogohlantirish yo\'q')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  {len(alerts)} ta ogohlantirish topildi:')
            )
            
            for i, alert in enumerate(alerts, 1):
                self.stdout.write(f'   {i}. {alert}')
    
    def _calculate_daily_stats(self, date):
        """Kunlik statistikalarni hisoblash"""
        from accounts.models import User
        from books.models import Book
        from loans.models import Loan, Reservation
        
        # Sana oralig'i
        start_datetime = timezone.make_aware(
            timezone.datetime.combine(date, timezone.datetime.min.time())
        )
        end_datetime = start_datetime + timedelta(days=1)
        
        # Foydalanuvchi statistikalari
        total_users = User.objects.count()
        active_users = User.objects.filter(
            last_login__date=date
        ).count()
        new_users = User.objects.filter(
            date_joined__range=(start_datetime, end_datetime)
        ).count()
        
        # Kitob statistikalari
        total_books = Book.objects.count()
        available_books = Book.objects.filter(available_copies__gt=0).count()
        borrowed_books = total_books - available_books
        
        # Faoliyat statistikalari
        total_loans = Loan.objects.filter(
            loan_date__range=(start_datetime, end_datetime)
        ).count()
        
        total_returns = Loan.objects.filter(
            return_date__range=(start_datetime, end_datetime)
        ).count()
        
        total_reservations = Reservation.objects.filter(
            reserved_at__range=(start_datetime, end_datetime)
        ).count()
        
        return {
            'date': date,
            'total_users': total_users,
            'active_users': active_users,
            'new_users': new_users,
            'total_books': total_books,
            'available_books': available_books,
            'borrowed_books': borrowed_books,
            'total_loans': total_loans,
            'total_returns': total_returns,
            'total_reservations': total_reservations,
            'total_searches': 0,  # Bu yerda qidiruv loglaridan hisoblash kerak
            'unique_search_terms': 0,
            'total_fines_collected': 0,  # Jarima tizimidan hisoblash kerak
            'outstanding_fines': 0,
            'average_response_time': cache.get('avg_response_time', 0),
            'error_rate': cache.get('system_error_rate', 0),
        } 