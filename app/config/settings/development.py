"""
Django settings for development environment.

This module contains settings specific to the development environment,
including debug configuration, logging, and development-specific tools.
"""

from .base import *  # noqa
import environ

env = environ.Env(DEBUG=(bool, False))

# Development Configuration
DEBUG = True

# Secret Key (should be overridden by environment variable)
SECRET_KEY = env("SECRET_KEY", default="dev-secret-key-not-for-production")

# Allowed Hosts for Development
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "atharixhub_web",
        "nginx",
        "atharixhub_nginx",
        "192.168.100.171",  # Local network IP
        "192.168.100.172",  # Local network IP
        "*",  # Allow all hosts in development
    ],
)

# CSRF Trusted Origins for Development
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:80",
        "http://127.0.0.1:80",
        "http://atharixhub_web",
        "http://nginx",
        "http://atharixhub_nginx",
        "http://192.168.100.171",
        "http://192.168.100.172",
    ],
)

# CORS Settings for Development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Security Settings (relaxed for development)
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Email Settings
EMAIL_BACKEND_TYPE = env("EMAIL_BACKEND", default="console")

if EMAIL_BACKEND_TYPE == "resend":
    EMAIL_BACKEND = "core.email_backends.resend.ResendEmailBackend"
    RESEND_API_KEY = env("RESEND_API_KEY", default="")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@localhost")

# Frontend URL for invitation links
FRONTEND_URL = env("FRONTEND_URL", default="")

# Spectacular settings for development
SPECTACULAR_SETTINGS.update(
    {
        "SERVE_INCLUDE_SCHEMA": True,
        "SWAGGER_UI_SETTINGS": {
            **SPECTACULAR_SETTINGS["SWAGGER_UI_SETTINGS"],
            "tryItOutEnabled": True,
            "persistAuthorization": True,
        },
    }
)

# Unfold development settings
UNFOLD.update(
    {
        "ENVIRONMENT": "config.settings.callbacks.environment_callback",
        "DASHBOARD_CALLBACK": "config.settings.callbacks.dashboard_callback",
        "THEME": "dark",  # Tema oscuro para resaltar el azul
        "SHOW_HISTORY": True,
        "SHOW_VIEW_ON_SITE": True,
    }
)

# Development Logging Configuration
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
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            # "level": "DEBUG",
            "level": "INFO",
            "propagate": False,
        },
        "core": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "users": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Development Cache (dummy cache)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Static files settings for development
STATIC_URL = "/static/"
# No STATICFILES_DIRS needed in development - using apps' static folders only

# Media files settings for development
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Django Debug Toolbar (if needed)
if DEBUG:
    try:
        import debug_toolbar

        INSTALLED_APPS.append("debug_toolbar")
        MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
        INTERNAL_IPS = ["127.0.0.1", "localhost"]
    except ImportError:
        pass

# Development REST Framework settings
REST_FRAMEWORK.update(
    {
        "DEFAULT_RENDERER_CLASSES": [
            "rest_framework.renderers.JSONRenderer",
            "rest_framework.renderers.BrowsableAPIRenderer",  # Enable browsable API in dev
        ],
    }
)

# Additional development tools
SHELL_PLUS_PRINT_SQL = True

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
