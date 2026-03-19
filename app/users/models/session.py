"""User session tracking model."""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class UserSession(models.Model):
    """Track active user sessions for device management."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    api_key = models.ForeignKey(
        "apps.APIKey",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
        verbose_name="API Key",
        help_text="API key used to create this session",
    )

    # JWT identification
    jti = models.CharField(
        "JWT ID",
        max_length=255,
        unique=True,
        help_text="Unique JWT token identifier",
    )
    refresh_token_hash = models.CharField(
        max_length=255,
        help_text="Hash of refresh token for revocation",
    )

    # Device information
    device_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="User-friendly device name",
    )
    device_type = models.CharField(
        max_length=20,
        choices=[
            ("mobile", "Mobile"),
            ("tablet", "Tablet"),
            ("desktop", "Desktop"),
            ("other", "Other"),
        ],
        default="other",
    )
    os_name = models.CharField("OS Name", max_length=50, blank=True)
    os_version = models.CharField("OS Version", max_length=50, blank=True)
    browser = models.CharField(max_length=50, blank=True)
    browser_version = models.CharField(max_length=50, blank=True)
    user_agent = models.TextField(help_text="Full User-Agent string")

    # Network information
    ip_address = models.GenericIPAddressField()
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)

    # Activity tracking
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(help_text="When the access token expires")

    # Session status
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    # Push notifications (deshabilitado - no se usa Firebase)
    # fcm_token conservado nullable para compatibilidad en caso de reactivarse
    fcm_token = models.CharField(
        "FCM Token",
        max_length=500,
        blank=True,
        null=True,
    )
    fcm_token_updated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "user_sessions"
        verbose_name = "User Session"
        verbose_name_plural = "User Sessions"
        ordering = ["-last_activity"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["jti"]),
            models.Index(fields=["last_activity"]),
        ]

    def __str__(self):
        device_info = self.device_name or f"{self.device_type} - {self.os_name}"
        return f"{self.user.email} - {device_info}"

    def revoke(self):
        """Revoke this session."""
        self.is_active = False
        self.revoked_at = timezone.now()
        self.save(update_fields=["is_active", "revoked_at"])

    @property
    def is_current_device(self):
        """Check if this is the current device (most recent activity)."""
        latest_session = (
            self.user.sessions.filter(is_active=True).order_by("-last_activity").first()
        )
        return latest_session and latest_session.id == self.id

    @property
    def is_expired(self):
        """Check if the session has expired."""
        return timezone.now() > self.expires_at

    def update_fcm_token(self, token):
        """Update the FCM token for push notifications."""
        self.fcm_token = token
        self.fcm_token_updated_at = timezone.now()
        self.save(update_fields=["fcm_token", "fcm_token_updated_at"])

    def clear_fcm_token(self):
        """Clear the FCM token (e.g., on logout)."""
        self.fcm_token = None
        self.fcm_token_updated_at = None
        self.save(update_fields=["fcm_token", "fcm_token_updated_at"])
