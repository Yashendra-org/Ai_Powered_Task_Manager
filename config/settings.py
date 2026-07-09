# Stage 1/5: Progressive implementation
import os
from pathlib import Path
from dotenv import load_dotenv

try:
    import dj_database_url
except ImportError:
    dj_database_url = None

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / '.env')

# Render Environment Flag
IS_RENDER = os.getenv('RENDER', 'false').lower() == 'true'

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-my-habbit-tracker-key-default-2026')
DEBUG = os.getenv('DEBUG', 'False' if IS_RENDER else 'True').lower() in ('true', '1', 'yes')

# Allowed Hosts
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost,testserver').split(',') if h.strip()]

RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

if IS_RENDER:
    if '.onrender.com' not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append('.onrender.com')

if DEBUG:
    ALLOWED_HOSTS.extend(['*', 'testserver'])

# CSRF Trusted Origins (Required for Render HTTPS POST requests)
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1,http://localhost').split(',') if o.strip()]
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')
if IS_RENDER:
    CSRF_TRUSTED_ORIGINS.append('https://*.onrender.com')

# Reverse Proxy SSL Header for Render
if IS_RENDER or not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'
