# 🚀 Monitoring Tizimiga Tez Kirish

## 1. Server Ishga Tushirish

```bash
cd backend
python manage.py runserver
```

## 2. Admin User Yaratish (agar yo'q bo'lsa)

```bash
python manage.py createsuperuser
```

## 3. Monitoring Interfayslari

### 🌐 HTML Dashboard Interfayslari:

1. **Public Dashboard:** http://127.0.0.1:8000/api/analytics/public-dashboard/
   - Hamma uchun ochiq
   - Asosiy statistikalar
   - Monitoring xususiyatlari haqida ma'lumot

2. **Admin Dashboard:** http://127.0.0.1:8000/api/analytics/dashboard/
   - Admin huquqlari kerak
   - To'liq monitoring interface
   - Real-time ma'lumotlar

### 📊 API Endpoints:

1. **Model-specific monitoring:**
   - **Foydalanuvchilar:** http://127.0.0.1:8000/api/analytics/monitor/users/
   - **Kitoblar:** http://127.0.0.1:8000/api/analytics/monitor/books/
   - **Qarzlar:** http://127.0.0.1:8000/api/analytics/monitor/loans/
   - **Analytics:** http://127.0.0.1:8000/api/analytics/monitor/analytics/

2. **System overview:** http://127.0.0.1:8000/api/analytics/monitor/system/

### 🔧 cURL orqali test qilish:

```bash
# 1. Login qiling
curl -c cookies.txt -b cookies.txt -X POST \
  -d "username=admin&password=yourpassword" \
  http://127.0.0.1:8000/admin/login/

# 2. Monitoring ma'lumotlarini oling
curl -b cookies.txt http://127.0.0.1:8000/api/analytics/monitor/system/
```

## 4. Test Command

```bash
# Barcha monitoring endpoints ni test qilish
python manage.py test_monitoring --endpoints

# To'liq test
python manage.py test_monitoring --all
```

## 5. Prometheus Metrics

```bash
# Prometheus metrics (to'g'ri URL)
http://127.0.0.1:8000/metrics
```

## 6. API Documentation

```bash
# Swagger UI
http://127.0.0.1:8000/api/docs/

# ReDoc
http://127.0.0.1:8000/api/redoc/
```

---

**Batafsil ma'lumot:** `backend/analytics/MONITORING_README.md` faylida

## ✅ Monitoring Xususiyatlari:

- ✅ **Real-time monitoring** - Tizim ko'rsatkichlarini jonli kuzatish
- ✅ **Model-specific analytics** - Har bir model uchun alohida monitoring
- ✅ **Professional HTML interface** - Chiroyli va zamonaviy dashboard
- ✅ **Prometheus metrics** - Professional metrikalar yig'ish
- ✅ **Swagger documentation** - To'liq API hujjatlari
- ✅ **Alert system** - Avtomatik ogohlantirishlar
- ✅ **Performance tracking** - Tizim unumdorligini kuzatish
- ✅ **Cache optimization** - Tez ishlash uchun kesh tizimi 