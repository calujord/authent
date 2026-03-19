import os

from celery import Celery

# Use environment variable for settings module instead of hardcoding
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    f"config.settings.{os.environ.get('ENVIRONMENT', 'development')}",
)

app = Celery("atharixhub")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()
