"""Notification model for user notifications."""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class Notification(BaseModel):
    """
    Model for user notifications.

    Stores notifications for users with read/unread status.
    """

    NOTIFICATION_TYPES = [
        ("info", _("Information")),
        ("success", _("Success")),
        ("warning", _("Warning")),
        ("error", _("Error")),
        ("reminder", _("Reminder")),
        ("message", _("Message")),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("User"),
        help_text=_("User who will receive this notification"),
    )

    title = models.CharField(
        _("Title"),
        max_length=200,
        help_text=_("Notification title"),
    )

    message = models.TextField(
        _("Message"),
        help_text=_("Notification message content"),
    )

    notification_type = models.CharField(
        _("Notification Type"),
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default="info",
        help_text=_("Type of notification"),
    )

    is_read = models.BooleanField(
        _("Is Read"),
        default=False,
        help_text=_("Whether the notification has been read"),
    )

    read_at = models.DateTimeField(
        _("Read At"),
        null=True,
        blank=True,
        help_text=_("When the notification was marked as read"),
    )

    url = models.CharField(
        _("URL"),
        max_length=500,
        blank=True,
        help_text=_("Optional URL to redirect when clicking the notification"),
    )

    metadata = models.JSONField(
        _("Metadata"),
        default=dict,
        blank=True,
        help_text=_("Additional metadata as JSON"),
    )

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["is_read", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            from django.utils import timezone

            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])

    def mark_as_unread(self):
        """Mark notification as unread."""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=["is_read", "read_at"])
