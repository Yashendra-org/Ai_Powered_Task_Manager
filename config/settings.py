import os
import sys
import secrets
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

try:
    import dj_database_url
except ImportError:
    dj_database_url = None

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / '.env')

# Render Environment Flag, Deploy Check, or Test Runner
IS_RENDER = os.getenv('RENDER', 'false').lower() == 'true'
IS_DEPLOY_CHECK = '--deploy' in sys.argv
IS_TEST_RUN = 'test' in sys.argv
IS_BUILD_COMMAND = (
    any(cmd in sys.argv for cmd in ('collectstatic', 'makemigrations', 'check'))
    and not IS_DEPLOY_CHECK
)
TRUST_PROXY_HEADERS = os.getenv('TRUST_PROXY_HEADERS', 'False').lower() in ('true', '1', 'yes')


def _resolve_secret_key(env_secret_key: str, *, is_render: bool, is_build_command: bool = False) -> str:
    """Validate and resolve SECRET_KEY, failing closed on Render runtime when insecure or missing."""
    key = (env_secret_key or '').strip()
    if is_render and not is_build_command:
        blocked_markers = ('enterprise_2026', 'django-insecure-', 'replace-with-')
        if not key:
            raise ImproperlyConfigured(
                "SECRET_KEY environment variable is not set on Render. "
                "Add a >=32-char random SECRET_KEY in Render Dashboard -> Environment "
                "(generate with: python -c \"import secrets; print(secrets.token_urlsafe(64))\")."
            )
        if any(marker in key for marker in blocked_markers):
            raise ImproperlyConfigured(
                "SECRET_KEY is using a leaked or placeholder value from .env.example. "
                "Replace SECRET_KEY in Render Dashboard -> Environment with a newly generated key."
            )
        if len(key) < 32:
            raise ImproperlyConfigured(
                f"SECRET_KEY must be at least 32 characters in production (got {len(key)})."
            )
    return key or secrets.token_urlsafe(64)


# Cryptographic SECRET_KEY (Fail closed in production if missing or using leaked dev values)
_ENV_SECRET_KEY = os.getenv('SECRET_KEY', '')
SECRET_KEY = _resolve_secret_key(
    _ENV_SECRET_KEY,
    is_render=IS_RENDER,
    is_build_command=IS_BUILD_COMMAND,
)

if IS_DEPLOY_CHECK:
    DEBUG = False
else:
    DEBUG = os.getenv('DEBUG', 'False' if IS_RENDER else 'True').lower() in ('true', '1', 'yes')

# Allowed Hosts (Never permit wildcard '*' to prevent HTTP Host Header Poisoning)
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost,testserver').split(',') if h.strip() and h.strip() != '*']

RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

if IS_RENDER:
    if '.onrender.com' not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append('.onrender.com')

if DEBUG:
    for dev_host in ('127.0.0.1', 'localhost', 'testserver', '[::1]', '172.16.208.176'):
        if dev_host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(dev_host)

# CSRF Trusted Origins (Required for Render HTTPS POST requests)
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1,http://localhost').split(',') if o.strip()]
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')
if IS_RENDER:
    CSRF_TRUSTED_ORIGINS.append('https://*.onrender.com')
if DEBUG:
    CSRF_TRUSTED_ORIGINS.extend([
        'http://127.0.0.1:8000',
        'http://localhost:8000',
        'http://172.16.208.176:8000',
    ])

# Reverse Proxy SSL Header & SSL Hardening for Production / Render
if IS_RENDER or not DEBUG or IS_DEPLOY_CHECK:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 'yes')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

AUTHENTICATION_BACKENDS = [
    'apps.accounts.backends.EmailOrUsernameModelBackend',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',

    # Local modular apps
    'apps.accounts.apps.AccountsConfig',
    'apps.tasks.apps.TasksConfig',
    'apps.assignments.apps.AssignmentsConfig',
    'apps.habits.apps.HabitsConfig',
    'apps.notes.apps.NotesConfig',
    'apps.reminders.apps.RemindersConfig',
    'apps.analytics.apps.AnalyticsConfig',
    'apps.ml_engine.apps.MlEngineConfig',
    'apps.api.apps.ApiConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'config.middleware.SecurityAndRateLimitMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database Configuration (Primary + Read Replica Splitting + PgBouncer Pooling)
# Priority: 1) DATABASE_URL (PostgreSQL), 2) Individual DB_* vars, 3) SQLite fallback
DATABASE_URL = os.getenv('DATABASE_URL')
DATABASE_READ_REPLICA_URL = os.getenv('DATABASE_READ_REPLICA_URL')
USE_PGBOUNCER = os.getenv('USE_PGBOUNCER', 'False').lower() in ('true', '1', 'yes')
_CONN_MAX_AGE = 0 if USE_PGBOUNCER else int(os.getenv('DB_CONN_MAX_AGE', '600'))

if dj_database_url and DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=_CONN_MAX_AGE,
            conn_health_checks=True,
        )
    }
    if DATABASE_READ_REPLICA_URL:
        DATABASES['read_replica'] = dj_database_url.config(
            default=DATABASE_READ_REPLICA_URL,
            conn_max_age=_CONN_MAX_AGE,
            conn_health_checks=True,
        )
elif 'postgresql' in os.getenv('DB_ENGINE', '') and os.getenv('DB_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': _CONN_MAX_AGE,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

if USE_PGBOUNCER:
    for _db_cfg in DATABASES.values():
        _db_cfg['DISABLE_SERVER_SIDE_CURSORS'] = True

if 'read_replica' in DATABASES:
    DATABASE_ROUTERS = ['config.db_router.PrimaryReplicaRouter']

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization & Timezone
LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Kolkata')
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

USE_S3_STORAGE = os.getenv('USE_S3_STORAGE', 'False').lower() in ('true', '1', 'yes')
_DEFAULT_STORAGE_BACKEND = (
    "storages.backends.s3.S3Storage"
    if USE_S3_STORAGE
    else "django.core.files.storage.FileSystemStorage"
)

STORAGES = {
    "default": {
        "BACKEND": _DEFAULT_STORAGE_BACKEND,
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Django REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '120/minute',
    },
}

# Celery, Distributed Redis Cache & High-Concurrency Session Store
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
USE_REDIS_CACHE = (
    not IS_TEST_RUN
    and (
        os.getenv('USE_REDIS_CACHE', 'False').lower() in ('true', '1', 'yes')
        or (IS_RENDER and bool(os.getenv('REDIS_URL')))
    )
)

if USE_REDIS_CACHE:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'KEY_PREFIX': 'ht_prod',
            'TIMEOUT': 300,
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'habittracker-local-cache',
            'TIMEOUT': 300,
        }
    }

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_TASK_ALWAYS_EAGER', 'False' if not IS_RENDER else 'True').lower() in ('true', '1', 'yes')

# Enterprise Security & HSTS Configuration
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = int(os.getenv('SESSION_COOKIE_AGE', '86400'))
PASSWORD_RESET_TIMEOUT = int(os.getenv('PASSWORD_RESET_TIMEOUT', '900'))
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024



# Email Configuration for Password Reset
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@myhabittracker.com')
