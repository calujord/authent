"""
Django settings for Admin/Production environment.

This configuration is specifically designed for administrative tasks
and production deployment of the Atharix Hub platform.
"""

from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

# Database
# Using PostGIS for geographic data
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 600,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "config" / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "config" / "static"]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "config" / "media"

# Security settings for production
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", default=False)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE", default=False)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# CORS settings
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", default=["http://localhost:3000", "http://127.0.0.1:3000"]
)
CORS_ALLOW_CREDENTIALS = True

# Admin-specific configurations
ADMIN_URL = env("ADMIN_URL", default="admin/")

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "config" / "logs" / "django.log",
            "maxBytes": 1024 * 1024 * 15,  # 15MB
            "backupCount": 10,
            "formatter": "verbose",
        },
        "hub": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "config" / "logs" / "hub.log",
            "maxBytes": 1024 * 1024 * 15,  # 15MB
            "backupCount": 10,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file"],
            "level": "ERROR",
            "propagate": False,
        },
        "hub": {
            "handlers": ["console", "hub"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Celery configuration for admin
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")

# Cache configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "atharixhub_admin",
        "TIMEOUT": 300,
    }
}

# Email configuration for admin notifications
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = env("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@atharix.com")
ADMIN_EMAIL = env("ADMIN_EMAIL", default="admin@atharix.com")

# AWS S3 Configuration (if using cloud storage)
if env("USE_S3", default=False):
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="eu-north-1")
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default="")
    AWS_DEFAULT_ACL = env(
        "AWS_DEFAULT_ACL", default="public-read"
    )  # Para avatares públicos
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    AWS_S3_FILE_OVERWRITE = env("AWS_S3_FILE_OVERWRITE", default=False, cast=bool)

    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    STATICFILES_STORAGE = "storages.backends.s3boto3.StaticS3Boto3Storage"

    AWS_MEDIA_LOCATION = "media"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN or f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'}/{AWS_MEDIA_LOCATION}/"

    AWS_STATIC_LOCATION = "static"
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN or f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'}/{AWS_STATIC_LOCATION}/"
