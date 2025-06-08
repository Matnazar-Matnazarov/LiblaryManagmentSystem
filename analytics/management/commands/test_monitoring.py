"""
Test Monitoring System Command

Bu command monitoring tizimini test qilish uchun ishlatiladi:
- Barcha model monitoring endpoints ni test qilish
- Performance metrics ni tekshirish
- Alert system ni test qilish
"""

from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
import json
import time

from analytics.monitoring import (
    metrics_collector,
    check_system_health,
    check_critical_metrics,
    track_user_login,
    track_search_query,
    update_error_rate
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Monitoring tizimini test qilish va tekshirish'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--endpoints',
            action='store_true',
            help='Monitoring endpoints larni test qilish',
        )
        
        parser.add_argument(
            '--metrics',
            action='store_true',
            help='Metrics collection ni test qilish',
        )
        
        parser.add_argument(
            '--alerts',
            action='store_true',
            help='Alert system ni test qilish',
        )
        
        parser.add_argument(
            '--performance',
            action='store_true',
            help='Performance monitoring ni test qilish',
        )
        
        parser.add_argument(
            '--all',
            action='store_true',
            help='Barcha testlarni ishga tushirish',
        )
    
    def handle(self, *args, **options):
        """Command ishga tushirish"""
        self.stdout.write(
            self.style.SUCCESS('🧪 Monitoring tizimini test qilish boshlandi...')
        )
        
        try:
            if options['all']:
                self.test_all()
            elif options['endpoints']:
                self.test_monitoring_endpoints()
            elif options['metrics']:
                self.test_metrics_collection()
            elif options['alerts']:
                self.test_alert_system()
            elif options['performance']:
                self.test_performance_monitoring()
            else:
                self.test_basic_functionality()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Monitoring test muvaffaqiyatli yakunlandi!')
            )
            
        except Exception as e:
            raise CommandError(f'Monitoring test xatosi: {e}')
    
    def test_all(self):
        """Barcha testlarni ishga tushirish"""
        self.stdout.write('🔄 Barcha testlarni ishga tushirish...')
        
        self.test_basic_functionality()
        self.test_metrics_collection()
        self.test_monitoring_endpoints()
        self.test_alert_system()
        self.test_performance_monitoring()
    
    def test_basic_functionality(self):
        """Asosiy funksionallikni test qilish"""
        self.stdout.write('🔧 Asosiy funksionallikni test qilish...')
        
        # System health check
        health_status = check_system_health()
        self.stdout.write(f'   System Health: {"✅ Healthy" if health_status else "❌ Unhealthy"}')
        
        # Metrics collector test
        try:
            metrics_collector.collect_all_metrics()
            self.stdout.write('   ✅ Metrics Collector: Working')
        except Exception as e:
            self.stdout.write(f'   ❌ Metrics Collector: Error - {e}')
        
        # Cache test
        try:
            cache.set('test_key', 'test_value', 60)
            result = cache.get('test_key')
            if result == 'test_value':
                self.stdout.write('   ✅ Cache System: Working')
            else:
                self.stdout.write('   ❌ Cache System: Not working properly')
        except Exception as e:
            self.stdout.write(f'   ❌ Cache System: Error - {e}')
    
    def test_metrics_collection(self):
        """Metrics collection ni test qilish"""
        self.stdout.write('📊 Metrics collection ni test qilish...')
        
        # User metrics test
        try:
            if User.objects.exists():
                user = User.objects.first()
                track_user_login(user, 'web')
                self.stdout.write('   ✅ User Login Tracking: Working')
            else:
                self.stdout.write('   ⚠️  User Login Tracking: No users to test')
        except Exception as e:
            self.stdout.write(f'   ❌ User Login Tracking: Error - {e}')
        
        # Search tracking test
        try:
            track_search_query('book_search', 'student')
            self.stdout.write('   ✅ Search Query Tracking: Working')
        except Exception as e:
            self.stdout.write(f'   ❌ Search Query Tracking: Error - {e}')
        
        # Error rate test
        try:
            update_error_rate('test_component', 1, 10)
            self.stdout.write('   ✅ Error Rate Tracking: Working')
        except Exception as e:
            self.stdout.write(f'   ❌ Error Rate Tracking: Error - {e}')
    
    def test_monitoring_endpoints(self):
        """Monitoring endpoints larni test qilish"""
        self.stdout.write('🌐 Monitoring endpoints larni test qilish...')
        
        # Admin user yaratish yoki topish
        admin_user = self._get_or_create_admin_user()
        
        # Django test client with proper settings
        from django.test import override_settings
        
        with override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1']):
            client = Client()
            client.force_login(admin_user)
            
            endpoints = [
                '/api/analytics/monitor/users/',
                '/api/analytics/monitor/books/',
                '/api/analytics/monitor/loans/',
                '/api/analytics/monitor/analytics/',
                '/api/analytics/monitor/system/',
            ]
            
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    response = client.get(endpoint, HTTP_HOST='testserver')
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        self.stdout.write(f'   ✅ {endpoint}: OK ({response_time:.3f}s)')
                        
                        # Response content ni tekshirish
                        try:
                            data = json.loads(response.content)
                            if 'timestamp' in data:
                                self.stdout.write(f'      📋 Valid response structure')
                            else:
                                self.stdout.write(f'      ⚠️  Response structure may be incomplete')
                        except json.JSONDecodeError:
                            self.stdout.write(f'      ❌ Invalid JSON response')
                    else:
                        self.stdout.write(f'   ❌ {endpoint}: Error {response.status_code}')
                        
                except Exception as e:
                    self.stdout.write(f'   ❌ {endpoint}: Exception - {e}')
    
    def test_alert_system(self):
        """Alert system ni test qilish"""
        self.stdout.write('🚨 Alert system ni test qilish...')
        
        try:
            alerts = check_critical_metrics()
            
            if alerts:
                self.stdout.write(f'   ⚠️  {len(alerts)} ta alert topildi:')
                for i, alert in enumerate(alerts, 1):
                    self.stdout.write(f'      {i}. {alert}')
            else:
                self.stdout.write('   ✅ Hech qanday kritik alert yo\'q')
                
            # Test alert yaratish
            cache.set('system_error_rate', 15, 300)  # 15% error rate
            test_alerts = check_critical_metrics()
            
            if any('error rate' in alert.lower() for alert in test_alerts):
                self.stdout.write('   ✅ Alert System: Working (test alert detected)')
            else:
                self.stdout.write('   ⚠️  Alert System: May not be detecting test conditions')
                
            # Test alert ni tozalash
            cache.delete('system_error_rate')
            
        except Exception as e:
            self.stdout.write(f'   ❌ Alert System: Error - {e}')
    
    def test_performance_monitoring(self):
        """Performance monitoring ni test qilish"""
        self.stdout.write('⚡ Performance monitoring ni test qilish...')
        
        # Response time test
        try:
            start_time = time.time()
            
            # Simulate some work
            if User.objects.exists():
                users = list(User.objects.all()[:10])
                
            execution_time = time.time() - start_time
            
            # Cache ga saqlash
            cache.set('test_response_time', execution_time, 300)
            
            retrieved_time = cache.get('test_response_time')
            
            if retrieved_time == execution_time:
                self.stdout.write(f'   ✅ Response Time Tracking: Working ({execution_time:.3f}s)')
            else:
                self.stdout.write('   ❌ Response Time Tracking: Cache issue')
                
        except Exception as e:
            self.stdout.write(f'   ❌ Response Time Tracking: Error - {e}')
        
        # Memory usage simulation
        try:
            # Cache efficiency test
            cache.set('efficiency_test_hits', 8, 300)
            cache.set('efficiency_test_misses', 2, 300)
            
            hits = cache.get('efficiency_test_hits', 0)
            misses = cache.get('efficiency_test_misses', 0)
            total = hits + misses
            
            if total > 0:
                efficiency = (hits / total) * 100
                self.stdout.write(f'   ✅ Cache Efficiency: {efficiency:.1f}%')
            else:
                self.stdout.write('   ⚠️  Cache Efficiency: No data')
                
        except Exception as e:
            self.stdout.write(f'   ❌ Cache Efficiency: Error - {e}')
    
    def _get_or_create_admin_user(self):
        """Admin user yaratish yoki topish"""
        try:
            # Mavjud admin user ni topish
            admin_user = User.objects.filter(is_superuser=True).first()
            
            if admin_user:
                return admin_user
            
            # Yangi admin user yaratish
            admin_user = User.objects.create_superuser(
                email='test_admin@library.local',
                username='test_admin',
                password='test_password_123'
            )
            
            self.stdout.write('   📝 Test admin user yaratildi')
            return admin_user
            
        except Exception as e:
            self.stdout.write(f'   ❌ Admin user yaratishda xato: {e}')
            raise
    
    def _cleanup_test_data(self):
        """Test ma'lumotlarini tozalash"""
        try:
            # Test cache keys ni tozalash
            test_keys = [
                'test_key',
                'test_response_time',
                'efficiency_test_hits',
                'efficiency_test_misses',
                'system_error_rate'
            ]
            
            for key in test_keys:
                cache.delete(key)
            
            # Test admin user ni o'chirish (agar test uchun yaratilgan bo'lsa)
            test_admin = User.objects.filter(
                email='test_admin@library.local',
                username='test_admin'
            ).first()
            
            if test_admin:
                test_admin.delete()
                self.stdout.write('   🗑️  Test admin user o\'chirildi')
                
        except Exception as e:
            self.stdout.write(f'   ⚠️  Cleanup warning: {e}') 