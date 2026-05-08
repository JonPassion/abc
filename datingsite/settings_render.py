"""
Render-specific production settings for datingsite project.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from .settings import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', os.environ.get('RENDER_EXTERNAL_SECRET_KEY', 'your-very-long-and-random-secret-key-here'))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Render-specific ALLOWED_HOSTS
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '.onrender.com').split(',')

# Database Configuration for Render PostgreSQL
# Render provides DATABASE_URL environment variable
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'datingsite'),
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 60,  # Connection pooling
    }
}

# Support for Render's DATABASE_URL
import dj_database_url
if 'DATABASE_URL' in os.environ:
    DATABASES['default'] = dj_database_url.parse(os.environ.get('DATABASE_URL'))

# Redis Cache Configuration for Render
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'dating_app_',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Session Configuration for Render
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Static files configuration for Render with WhiteNoise
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Add WhiteNoise middleware for static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Media files configuration for Render
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security Settings for Render
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_FRAME_DENY = 'DENY'

# Session Security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# CORS Settings for Render (if needed)
CORS_ALLOWED_ORIGINS = [
    "https://*.onrender.com",
]
CORS_ALLOW_CREDENTIALS = True

# Logging Configuration for Render
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Email Configuration (for production notifications)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Performance Settings for Render
CONN_MAX_AGE = 60
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB

# Render-specific performance optimizations
USE_TZ = True
USE_L10N = True

# Health check endpoint
from django.urls import path
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'database': 'connected' if DATABASES['default'] else 'disconnected',
        'cache': 'connected' if CACHES.get('default') else 'disconnected'
    })

# Add health check to URLs (will be handled in urls.py)
