"""
Django settings for Library Management System.

This is a professional configuration with:
- Environment-based settings
- Security best practices
- Comprehensive logging
- Database optimizations
- Caching configuration
- Media and static files handling
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
from typing import List, Dict, Any
from datetime import timedelta
from environs import Env


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = Env()

# Read .env file if it exists
env.read_env(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    # API Framework
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    
    # CORS handling
    'corsheaders',
    
    # API Documentation
    'drf_spectacular',
    
    # Admin enhancements
    'django_extensions',
    
    # Background tasks
    'django_celery_beat',
    'django_celery_results',
    
    # Authentication
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    
    # Filtering
    'django_filters',
    
    # Monitoring
    'django_prometheus',
]

LOCAL_APPS = [
    'accounts',
    'books',
    'loans',
    'analytics',
    'notifications',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env.str('DB_NAME', default='library_db'),
        'USER': env.str('DB_USER', default='postgres'),
        'PASSWORD': env.str('DB_PASSWORD', default='password'),
        'HOST': env.str('DB_HOST', default='localhost'),
        'PORT': env.int('DB_PORT', default=5432),
    },
}



# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('uz', 'Uzbek'),
    ('ru', 'Russian'),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,

    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,

    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",

    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",

    "JTI_CLAIM": "jti",

    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),

    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}
# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Library Management System API',
    'DESCRIPTION': '''
# Library Management System API

Professional library management system built with Django REST Framework.

## Features
- **Book Management**: Complete catalog with search and filtering
- **User Management**: Role-based access control and profiles  
- **Loan System**: Book borrowing and return operations
- **Analytics**: Statistics and reporting dashboard
- **Notifications**: Alert and notification system

## Authentication
This API uses JWT authentication. Include the token in the Authorization header:
`Authorization: Bearer <your_token>`

## Rate Limiting
- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVE_PUBLIC': True,
    
    # UI Configuration
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
        'displayRequestDuration': True,
        'defaultModelsExpandDepth': 2,
        'defaultModelExpandDepth': 2,
        'defaultModelRendering': 'model',
        'docExpansion': 'none',
        'filter': True,
        'showExtensions': True,
        'showCommonExtensions': True,
        'tryItOutEnabled': True,
    },
    
    'REDOC_SETTINGS': {
        'LAZY_RENDERING': True,
        'HIDE_DOWNLOAD_BUTTON': False,
        'EXPAND_RESPONSES': '200,201',
        'PATH_IN_MIDDLE_PANEL': True,
        'NATIVE_SCROLLBARS': True,
    },
    
    # Schema Configuration
    'COMPONENT_SPLIT_REQUEST': False,
    'COMPONENT_SPLIT_PATCH': False,
    'COMPONENT_NO_READ_ONLY_REQUIRED': False,
    'SCHEMA_COERCE_PATH_PK': True,
    'SCHEMA_COERCE_PATH_PK_SUFFIX': True,
    
    # Operation Configuration
    'SORT_OPERATIONS': True,
    'SORT_OPERATION_PARAMETERS': True,
    'OPERATION_ID_METHOD_POSITION': 'POST',
    'CAMELIZE_NAMES': False,
    
    # Tag Configuration - prevent automatic tag generation
    'SCHEMA_PATH_PREFIX': '/api/',
    'SCHEMA_PATH_PREFIX_TRIM': True,
    'SCHEMA_PATH_PREFIX_INSERT': '',
    
    # Disable automatic tag generation from URL patterns
    'GENERIC_ADDITIONAL_PROPERTIES': 'bool',
    'SCHEMA_AUTHENTICATION': [],
    
    # Error Handling
    'DISABLE_ERRORS_AND_WARNINGS': False,
    'ENABLE_DJANGO_DEPLOY_CHECK': True,
    
    # Tags for API organization - only these tags will be used
    'TAGS': [
        {
            'name': 'Authentication',
            'description': 'User authentication and authorization'
        },
        {
            'name': 'Users',
            'description': 'User management and profiles'
        },
        {
            'name': 'Books',
            'description': 'Book catalog and inventory'
        },
        {
            'name': 'Authors',
            'description': 'Author information management'
        },
        {
            'name': 'Categories',
            'description': 'Book category management'
        },
        {
            'name': 'Publishers',
            'description': 'Publisher information'
        },
        {
            'name': 'Loans',
            'description': 'Book borrowing and returns'
        },
        {
            'name': 'Analytics',
            'description': 'System statistics and reports'
        },
        {
            'name': 'Notifications',
            'description': 'Notification management'
        },
    ],
    
    # External Documentation
    'EXTERNAL_DOCS': {
        'description': 'API Documentation',
        'url': 'https://docs.yourdomain.com/api/',
    },
    
    # Contact Information
    'CONTACT': {
        'name': 'API Support Team',
        'email': 'api-support@yourdomain.com',
        'url': 'https://yourdomain.com/support',
    },
    
    # License Information
    'LICENSE': {
        'name': 'MIT License',
        'url': 'https://opensource.org/licenses/MIT',
    },
    
    # Server Information
    'SERVERS': [
        {
            'url': 'http://127.0.0.1:8000/api',
            'description': 'Development Server'
        },
        {
            'url': 'https://api.yourdomain.com/api',
            'description': 'Production Server'
        },
    ],
    
    # Postprocessing - only essential hooks
    'POSTPROCESSING_HOOKS': [
        'config.spectacular_hooks.fix_duplicate_tags',
    ],
    
    # Enhanced Enum Configuration
    'ENUM_NAME_OVERRIDES': {},
    'ENUM_ADD_CHOICES': False,
    'ENUM_GENERATE_CHOICE_SERIALIZER': False,
    
    # Additional OpenAPI Extensions
    'EXTENSIONS_INFO': {
        'x-api-version': '1.0.0',
        'x-api-status': 'stable',
        'x-changelog': 'https://docs.yourdomain.com/changelog',
    },
}

# CORS settings
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=['http://localhost:3000', 'http://127.0.0.1:3000'])

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'library-cache',
        'TIMEOUT': 300,  # 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Alternative Redis configuration (uncomment if Redis is available)
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': env.str('REDIS_URL', default='redis://localhost:6379/0'),
#         'KEY_PREFIX': 'library_cache',
#         'TIMEOUT': 300,  # 5 minutes
#     }
# }

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# SESSION_CACHE_ALIAS = 'default'  # Commented out since we're using DB sessions
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Celery Configuration
CELERY_BROKER_URL = env.str('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env.str('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Celery Beat Settings
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Email Configuration
EMAIL_BACKEND = env.str('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env.str('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL', default='noreply@library.local')

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 3153600 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSRF Settings
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=['http://localhost:3000', 'http://127.0.0.1:3000'])

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'filters': ['require_debug_true'],
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
    },
    'root': {
        'handlers': ['console', 'file'],
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'library': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Ensure logs directory exists
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Application-specific settings
LIBRARY_SETTINGS = {
    'MAX_BOOKS_PER_USER': 5,
    'LOAN_DURATION_DAYS': 14,
    'MAX_RENEWAL_COUNT': 2,
    'FINE_PER_DAY': 1000,  # in som
    'RESERVATION_DURATION_HOURS': 24,
    'NOTIFICATION_DAYS_BEFORE_DUE': 3,
    'AUTO_SUSPEND_AFTER_DAYS': 30,
}


# Monitoring and Error Tracking
if not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=env.str('SENTRY_DSN', default=''),
        integrations=[
            DjangoIntegration(auto_enabling=True),
            CeleryIntegration(monitor_beat_tasks=True),
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment=env.str('ENVIRONMENT', default='production'),
    )


# Testing settings
if 'test' in sys.argv or 'pytest' in sys.modules:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]
    

# Django allauth configuration (Updated for latest version)
ACCOUNT_LOGIN_METHODS = ['email']
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'

# Social account configuration
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_QUERY_EMAIL = True

# Social account providers
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
        'FETCH_USERINFO': True,
    }
}

# Custom adapter for JWT integration
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'

