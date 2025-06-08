# 📊 Library Management System - Professional Monitoring

Bu kutubxona boshqaruv tizimi uchun professional monitoring va analytics tizimi hisoblanadi. Django Prometheus va custom metrics bilan qurilgan.

## 🚀 Monitoring Tizimiga Kirish

### 1. Asosiy Monitoring Endpoints

Monitoring tizimiga kirish uchun admin huquqlari kerak. Quyidagi endpoints mavjud:

```bash
# Umumiy tizim monitoring
GET /api/analytics/monitor/system/

# Foydalanuvchi modeli monitoring  
GET /api/analytics/monitor/users/

# Kitob modeli monitoring
GET /api/analytics/monitor/books/

# Qarz modeli monitoring
GET /api/analytics/monitor/loans/

# Analytics modeli monitoring
GET /api/analytics/monitor/analytics/
```

### 2. Prometheus Metrics

Prometheus metrics `/metrics` endpoint orqali mavjud:

```bash
# Prometheus metrics
GET /metrics
```

### 3. Authentication

Barcha monitoring endpoints admin huquqlari talab qiladi:

```python
# Permission classes
permission_classes = [IsAuthenticated, IsAdminUser]
```

## 🔧 Monitoring Tizimini Ishga Tushirish

### 1. Server Ishga Tushirish

```bash
cd backend
python manage.py runserver
```

### 2. Admin User Yaratish

```bash
python manage.py createsuperuser
```

### 3. Monitoring Test Qilish

```bash
# Barcha monitoring testlari
python manage.py test_monitoring --all

# Faqat endpoints test qilish
python manage.py test_monitoring --endpoints

# Faqat metrics test qilish  
python manage.py test_monitoring --metrics

# Faqat alerts test qilish
python manage.py test_monitoring --alerts

# Performance test qilish
python manage.py test_monitoring --performance
```

### 4. Metrics Yig'ish

```bash
# Manual metrics yig'ish
python manage.py collect_metrics

# Kunlik statistika yaratish
python manage.py collect_metrics --daily-stats

# Tizim sog'ligini tekshirish
python manage.py collect_metrics --health-check

# Ogohlantirishlarni tekshirish
python manage.py collect_metrics --alerts
```

## 📈 Monitoring Endpoints Tafsilotlari

### 1. System Overview (`/api/analytics/monitor/system/`)

Umumiy tizim ko'rsatkichlari:

```json
{
  "timestamp": "2025-06-08T15:15:28.123456Z",
  "system_overview": {
    "users": {
      "total": 150,
      "active": 45,
      "activity_rate": 30.0,
      "status": "healthy"
    },
    "books": {
      "total": 1200,
      "available": 800,
      "availability_rate": 66.67,
      "status": "healthy"
    },
    "loans": {
      "active": 400,
      "overdue": 15,
      "overdue_rate": 3.75,
      "status": "healthy"
    }
  },
  "health_status": {
    "database": true,
    "cache": true,
    "overall": true
  },
  "performance_overview": {
    "response_times": {
      "avg_api_response": 0.125,
      "avg_db_query": 0.045,
      "avg_cache_operation": 0.002
    }
  },
  "critical_alerts": [],
  "uptime": "5d 12h 30m"
}
```

### 2. User Model Monitoring (`/api/analytics/monitor/users/`)

Foydalanuvchi modeli metrikalari:

```json
{
  "model": "User",
  "timestamp": "2025-06-08T15:15:28.123456Z",
  "overview": {
    "total_users": 150,
    "active_users": 45,
    "activity_rate": 30.0
  },
  "role_distribution": {
    "student": {
      "count": 120,
      "label": "Student",
      "active_count": 35
    },
    "teacher": {
      "count": 25,
      "label": "Teacher", 
      "active_count": 8
    },
    "librarian": {
      "count": 5,
      "label": "Librarian",
      "active_count": 2
    }
  },
  "verification_stats": {
    "fully_verified": 130,
    "pending_email": 15,
    "pending_identity": 5,
    "pending_professional": 0
  },
  "activity_metrics": {
    "daily_active": 12,
    "weekly_active": 45,
    "monthly_active": 78,
    "never_logged_in": 5
  },
  "alerts": []
}
```

### 3. Book Model Monitoring (`/api/analytics/monitor/books/`)

Kitob modeli metrikalari:

```json
{
  "model": "Book",
  "timestamp": "2025-06-08T15:15:28.123456Z",
  "overview": {
    "total_books": 1200,
    "available_books": 800,
    "borrowed_books": 400,
    "availability_rate": 66.67
  },
  "category_distribution": {
    "Fiction": {
      "total_books": 300,
      "available_books": 200,
      "utilization_rate": 33.33
    },
    "Science": {
      "total_books": 250,
      "available_books": 150,
      "utilization_rate": 40.0
    }
  },
  "inventory_metrics": {
    "low_stock": 25,
    "out_of_stock": 10,
    "high_demand": 5,
    "avg_copies_per_book": 2.5
  },
  "popularity_metrics": {
    "most_viewed": [
      {
        "title": "Python Programming",
        "views": 1250
      }
    ],
    "most_borrowed": [
      {
        "title": "Django for Beginners", 
        "borrows": 85
      }
    ]
  },
  "alerts": []
}
```

## 🔍 Monitoring Qanday Ishlatish

### 1. Browser orqali

1. Admin panel ga kiring: `http://127.0.0.1:8000/admin/`
2. Monitoring endpoints ga to'g'ridan-to'g'ri murojaat qiling:
   - `http://127.0.0.1:8000/api/analytics/monitor/system/`
   - `http://127.0.0.1:8000/api/analytics/monitor/users/`
   - `http://127.0.0.1:8000/api/analytics/monitor/books/`

### 2. cURL orqali

```bash
# Login qiling va session cookie oling
curl -c cookies.txt -b cookies.txt -X POST \
  -d "username=admin&password=your_password" \
  http://127.0.0.1:8000/admin/login/

# Monitoring endpoint ga murojaat qiling
curl -b cookies.txt \
  http://127.0.0.1:8000/api/analytics/monitor/system/
```

### 3. Python requests orqali

```python
import requests

# Login
session = requests.Session()
login_data = {
    'username': 'admin',
    'password': 'your_password'
}

# CSRF token olish
login_page = session.get('http://127.0.0.1:8000/admin/login/')
csrf_token = login_page.cookies['csrftoken']
login_data['csrfmiddlewaretoken'] = csrf_token

# Login qilish
session.post('http://127.0.0.1:8000/admin/login/', data=login_data)

# Monitoring ma'lumotlarini olish
response = session.get('http://127.0.0.1:8000/api/analytics/monitor/system/')
data = response.json()
print(data)
```

### 4. Postman orqali

1. **Authentication Setup:**
   - Method: POST
   - URL: `http://127.0.0.1:8000/admin/login/`
   - Body: form-data
     - username: admin
     - password: your_password

2. **Monitoring Request:**
   - Method: GET
   - URL: `http://127.0.0.1:8000/api/analytics/monitor/system/`
   - Headers: Cookie session dan olingan

## 📊 Prometheus Metrics

### Mavjud Metrics

```bash
# Business metrics
library_book_loans_total
library_book_returns_total
library_user_registrations_total
library_user_logins_total

# Performance metrics  
library_api_request_duration_seconds
library_db_query_duration_seconds
library_cache_operations_total

# System health metrics
library_active_users_total
library_available_books_total
library_system_status
library_error_rate_percent
```

### Prometheus Server Setup

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'django-library'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics/'
    scrape_interval: 30s
```

## 🚨 Alert System

### Alert Turlari

1. **System Health Alerts:**
   - Database connection issues
   - Cache system problems
   - High error rates

2. **Business Logic Alerts:**
   - Low book availability
   - High overdue rates
   - Pending verifications

3. **Performance Alerts:**
   - Slow response times
   - High query counts
   - Cache efficiency issues

### Alert Konfiguratsiyasi

```python
# settings.py da
LIBRARY_SETTINGS = {
    'ALERT_THRESHOLDS': {
        'ERROR_RATE_PERCENT': 5.0,
        'BOOK_AVAILABILITY_PERCENT': 20.0,
        'OVERDUE_RATE_PERCENT': 10.0,
        'RESPONSE_TIME_MS': 1000,
    }
}
```

## 🔧 Troubleshooting

### Umumiy Muammolar

1. **404 Error - Endpoint topilmadi:**
   ```bash
   # URL to'g'ri ekanligini tekshiring
   http://127.0.0.1:8000/api/analytics/monitor/system/
   ```

2. **403 Error - Ruxsat yo'q:**
   ```bash
   # Admin huquqlari borligini tekshiring
   python manage.py createsuperuser
   ```

3. **500 Error - Server xatosi:**
   ```bash
   # Loglarni tekshiring
   tail -f logs/django.log
   ```

### Monitoring Test

```bash
# Monitoring tizimini to'liq test qilish
python manage.py test_monitoring --all

# Natija:
# 🧪 Monitoring tizimini test qilish boshlandi...
# 🔧 Asosiy funksionallikni test qilish...
#    System Health: ✅ Healthy
#    ✅ Metrics Collector: Working
#    ✅ Cache System: Working
# 📊 Metrics collection ni test qilish...
#    ✅ User Login Tracking: Working
#    ✅ Search Query Tracking: Working
#    ✅ Error Rate Tracking: Working
# 🌐 Monitoring endpoints larni test qilish...
#    ✅ /api/analytics/monitor/users/: OK (0.125s)
#    ✅ /api/analytics/monitor/books/: OK (0.098s)
#    ✅ /api/analytics/monitor/loans/: OK (0.156s)
#    ✅ /api/analytics/monitor/analytics/: OK (0.089s)
#    ✅ /api/analytics/monitor/system/: OK (0.234s)
# ✅ Monitoring test muvaffaqiyatli yakunlandi!
```

## 📚 Qo'shimcha Ma'lumotlar

### Monitoring Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Django App    │───▶│  Monitoring      │───▶│   Prometheus    │
│                 │    │  Middleware      │    │   Metrics       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Model         │    │  Custom Views    │    │   Grafana       │
│   Decorators    │    │  & Endpoints     │    │   Dashboard     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Performance Optimization

1. **Cache Strategy:**
   - Metrics cache: 5 minutes
   - Statistics cache: 1 hour
   - Health checks: 1 minute

2. **Query Optimization:**
   - select_related() for ForeignKey
   - prefetch_related() for ManyToMany
   - Database indexes on monitoring fields

3. **Background Tasks:**
   - Celery for heavy computations
   - Scheduled metrics collection
   - Automated report generation

### Security Considerations

1. **Access Control:**
   - Admin-only endpoints
   - IP-based restrictions (optional)
   - Rate limiting

2. **Data Privacy:**
   - No sensitive data in metrics
   - Aggregated statistics only
   - Secure logging practices

## 🎯 Keyingi Qadamlar

1. **Grafana Dashboard Setup**
2. **Alert Manager Integration**
3. **Custom Business Metrics**
4. **Real-time Notifications**
5. **Mobile Monitoring App**

---

**Muallif:** Library Management System Team  
**Versiya:** 1.0.0  
**Oxirgi yangilanish:** 2025-06-08 