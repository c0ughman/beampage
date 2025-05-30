import os
import dj_database_url
from decouple import config
from .settings import *

# Heroku-specific settings
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY', default=os.environ.get('SECRET_KEY', 'change-me-in-production'))

# Allowed hosts for Heroku - get from environment variable
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Database configuration for Heroku (PostgreSQL)
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='sqlite:///db.sqlite3')
    )
}

# Static files configuration for Heroku
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Add WhiteNoise middleware
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Logging configuration for Heroku
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
            'formatter': 'verbose'
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True 