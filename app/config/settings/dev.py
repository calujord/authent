from .base import *

DEBUG = True

SECRET_KEY = env("SECRET_KEY", default="dev-secret-key-not-for-production")

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "192.168.100.171"]
)

CORS_ALLOW_ALL_ORIGINS = True

# Spectacular settings for development
SPECTACULAR_SETTINGS.update(
    {
        "SERVE_INCLUDE_SCHEMA": True,
        "SWAGGER_UI_SETTINGS": {
            **SPECTACULAR_SETTINGS["SWAGGER_UI_SETTINGS"],
            "tryItOutEnabled": True,
        },
    }
)

# Unfold development settings
UNFOLD.update(
    {
        "ENVIRONMENT": "config.settings.callbacks.environment_callback",
        "DASHBOARD_CALLBACK": "config.settings.callbacks.dashboard_callback",
        "THEME": "light",
    }
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}

# Email Settings
EMAIL_BACKEND_TYPE = env("EMAIL_BACKEND", default="console")
if EMAIL_BACKEND_TYPE == "resend":
    EMAIL_BACKEND = "core.email_backends.resend.ResendEmailBackend"
    RESEND_API_KEY = env("RESEND_API_KEY", default="")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Authent <noreply@authent.app>")
