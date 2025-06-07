# 📚 Library Management System - Backend

![Django](https://img.shields.io/badge/Django-5.1+-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17+-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7+-DC382D?style=for-the-badge&logo=redis&logoColor=white)

> Professional Django REST API backend for a comprehensive library management system with modern architecture and best practices.

## 🎯 Features

### Core Functionality
- **📖 Book Management** - Complete catalog with metadata, categories, and inventory tracking
- **👥 User Management** - Role-based access control with comprehensive verification system
- **🔄 Loan System** - Book borrowing, returns, renewals, and reservations
- **💰 Fine Management** - Automated fine calculation and payment tracking
- **📊 Analytics** - Comprehensive reporting and insights
- **🔔 Notifications** - Email, SMS, and in-app notifications

### Technical Features
- **🔐 JWT Authentication** - Secure token-based authentication
- **📋 API Documentation** - Auto-generated Swagger/OpenAPI documentation
- **🚀 Performance** - Redis caching and database optimization
- **🔍 Search** - Advanced search capabilities with filtering
- **📱 Mobile-Ready** - RESTful API designed for mobile apps
- **🌐 Multi-language** - i18n support (English, Uzbek, Russian)

## 🏗️ Architecture

### Clean Architecture Pattern
```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│             (REST API Views & Serializers)                 │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                        │
│            (Business Logic & Use Cases)                    │
├─────────────────────────────────────────────────────────────┤
│                    Domain Layer                             │
│               (Models & Entities)                          │
├─────────────────────────────────────────────────────────────┤
│                 Infrastructure Layer                        │
│         (Database, Cache, External APIs)                   │
└─────────────────────────────────────────────────────────────┘
```

### Apps Structure
```
backend/
├── accounts/          # User management and authentication
├── books/            # Book catalog and inventory
├── loans/            # Borrowing and return system
├── analytics/        # Reports and statistics
├── notifications/    # Messaging system
├── config/           # Django settings and configuration
└── manage.py         # Django management script
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 17+ (or SQLite for development)
- Redis 7+ (for caching and background tasks)

### Installation

1. **Clone and setup virtual environment**
   ```bash
   git clone <repository-url>
   cd backend
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or venv\Scripts\activate  # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment configuration**
   ```bash
   cp env.txt .env
   # Edit .env with your settings
   ```

4. **Database setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Run development server**
   ```bash
   python manage.py runserver
   ```

6. **Start background services** (optional)
   ```bash
   # In separate terminals
   celery -A config worker -l info
   celery -A config beat -l info
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file from `env.txt` and configure:

```env
# Core Settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=library_management_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

See `env.txt` for complete configuration options.

### Database Configuration

#### PostgreSQL (Recommended)
```bash
# Install PostgreSQL client
sudo apt-get install postgresql-client  # Ubuntu/Debian
brew install postgresql                  # macOS

# Create database
createdb library_management_db
```

#### SQLite (Development)
For quick development setup, SQLite is pre-configured.

## 📋 API Documentation

### Access Points
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### Main Endpoints

#### Authentication
```
POST /api/v1/auth/register/       # User registration
POST /api/v1/auth/login/          # User login
POST /api/v1/auth/refresh/        # Token refresh
POST /api/v1/auth/logout/         # User logout
```

#### Users
```
GET    /api/v1/auth/users/        # List users
POST   /api/v1/auth/users/        # Create user
GET    /api/v1/auth/users/{id}/   # User details
PUT    /api/v1/auth/users/{id}/   # Update user
DELETE /api/v1/auth/users/{id}/   # Delete user
```

#### Books
```
GET    /api/v1/books/             # List books
POST   /api/v1/books/             # Create book
GET    /api/v1/books/{id}/        # Book details
PUT    /api/v1/books/{id}/        # Update book
DELETE /api/v1/books/{id}/        # Delete book
```

#### Loans
```
GET    /api/v1/loans/             # List loans
POST   /api/v1/loans/             # Create loan
PUT    /api/v1/loans/{id}/return/ # Return book
PUT    /api/v1/loans/{id}/extend/ # Extend loan
```

## 🗃️ Database Schema

### Core Models

#### User Model
```python
class User(AbstractUser):
    # Core fields
    email = models.EmailField(unique=True)
    role = models.CharField(choices=UserRole.choices)
    account_status = models.CharField(choices=AccountStatus.choices)
    
    # Personal information
    first_name, last_name, middle_name
    date_of_birth, gender, phone_number
    
    # Address information
    address_line_1, city, country, postal_code
    
    # Professional information
    profession_category, profession_title
    workplace_organization
    
    # Verification system
    email_verification_status
    phone_verification_status
    identity_verification_status
    professional_verification_status
```

#### Book Model
```python
class Book(models.Model):
    # Basic information
    title, subtitle, author, isbn
    publication_year, edition, language
    
    # Classification
    category, tags, dewey_decimal
    
    # Physical properties
    pages, format, dimensions, weight
    
    # Inventory
    total_copies, available_copies
    location, shelf_number
    
    # Status and metadata
    status, condition, acquisition_date
    created_at, updated_at
```

#### Loan Model
```python
class Loan(models.Model):
    # Relationships
    user = ForeignKey(User)
    book = ForeignKey(Book)
    
    # Dates
    loan_date, due_date, return_date
    
    # Status and tracking
    status, renewal_count
    fine_amount, fine_paid
    
    # Notes
    librarian_notes, return_notes
```

## 🔒 Security Features

### Authentication & Authorization
- **JWT Tokens** - Secure stateless authentication
- **Role-based Access** - Granular permissions by user role
- **Rate Limiting** - API abuse prevention
- **CORS Configuration** - Cross-origin request handling

### Data Protection
- **Input Validation** - Comprehensive data sanitization
- **SQL Injection Prevention** - Django ORM protection
- **XSS Protection** - Content security policies
- **CSRF Protection** - Cross-site request forgery prevention

### User Verification
- **Email Verification** - Email address confirmation
- **Phone Verification** - SMS-based verification
- **Identity Verification** - Document upload and validation
- **Professional Verification** - Work/academic credential verification

## 🚀 Performance Optimization

### Caching Strategy
- **Redis Caching** - Frequently accessed data
- **Query Optimization** - Database query optimization
- **API Response Caching** - Endpoint-level caching
- **Static File Optimization** - Compressed and versioned assets

### Database Optimization
- **Connection Pooling** - Efficient database connections
- **Query Profiling** - Performance monitoring
- **Index Optimization** - Strategic database indexing
- **Read Replicas** - Scalable read operations

## 🧪 Testing

### Run Tests
```bash
# All tests
python manage.py test

# Specific app
python manage.py test accounts

# With coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Test Structure
```
tests/
├── test_models.py      # Model tests
├── test_views.py       # API endpoint tests
├── test_serializers.py # Serializer tests
├── test_permissions.py # Permission tests
└── factories.py        # Test data factories
```

## 📊 Monitoring & Logging

### Application Monitoring
- **Structured Logging** - JSON-formatted logs
- **Error Tracking** - Sentry integration
- **Performance Metrics** - Prometheus monitoring
- **Health Checks** - System health endpoints

### Logging Configuration
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/django.log',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
    },
}
```

## 🔄 Background Tasks

### Celery Configuration
```bash
# Start worker
celery -A config worker -l info

# Start scheduler
celery -A config beat -l info

# Monitor tasks
celery -A config flower
```

### Task Examples
- **Email Notifications** - Overdue book reminders
- **Fine Calculations** - Daily fine processing
- **Report Generation** - Scheduled analytics reports
- **Data Cleanup** - Expired reservation cleanup

## 🌐 Internationalization

### Supported Languages
- **English (en)** - Default language
- **Uzbek (uz)** - Local language support
- **Russian (ru)** - Additional language support

### Translation Management
```bash
# Create translation files
python manage.py makemessages -l uz

# Compile translations
python manage.py compilemessages

# Update translations
python manage.py makemessages -a
```

## 📦 Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure production database
- [ ] Set up Redis for production
- [ ] Configure email backend
- [ ] Set secure SECRET_KEY
- [ ] Configure static file serving
- [ ] Set up SSL certificates
- [ ] Configure monitoring
- [ ] Set up backup strategy

### Docker Deployment
```bash
# Build image
docker build -t library-backend .

# Run container
docker run -p 8000:8000 library-backend

# With docker-compose
docker-compose up -d
```

### Environment-specific Settings
- **Development** - Debug enabled, console email, SQLite
- **Staging** - Production-like, test data, monitoring
- **Production** - Optimized, secure, full monitoring

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Run tests and linting
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

### Code Standards
- **PEP 8** - Python code style
- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **Type Hints** - Type annotations
- **Docstrings** - Comprehensive documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Matnazar Matnazarov**
- Email: matnazarmatnazarov3@gmail.com
- GitHub: [@matnazar](https://github.com/matnazar)

## 🙏 Acknowledgments

- Django community for the excellent framework
- DRF team for the powerful API framework
- Contributors and beta testers
- Library science professionals for domain expertise

---

## 📞 Support

For support, email matnazarmatnazarov3@gmail.com or create an issue in the repository.

**Built with ❤️ using Django and modern Python practices** 