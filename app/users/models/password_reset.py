"""PasswordReset model for auth service."""

import secrets
import string

from django.conf import settings
from django.db import models
from django.utils import timezone


class PasswordReset(models.Model):
    """Model to track password reset requests via PIN."""

    EXPIRY_MINUTES = 15

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_resets",
    )
    hash_token = models.CharField("Hash token", max_length=64)
    pin = models.CharField("PIN", max_length=4)
    is_active = models.BooleanField("Active", default=True)
    created_at = models.DateTimeField("Created at", auto_now_add=True)
    expires_at = models.DateTimeField("Expires at")
    used_at = models.DateTimeField("Used at", null=True, blank=True)

    class Meta:
        verbose_name = "Password Reset"
        verbose_name_plural = "Password Resets"
        ordering = ["-created_at"]

    def __str__(self):
        return f"PasswordReset({self.user.email})"

    @staticmethod
    def generate_hash():
        """Generate a secure random hash token."""
        return secrets.token_hex(32)

    @staticmethod
    def generate_pin():
        """Generate a 4-digit numeric PIN."""
        return "".join(secrets.choice(string.digits) for _ in range(4))

    @property
    def is_used(self):
        return self.used_at is not None

    def is_valid(self):
        """Return True if the reset is still active and not expired."""
        return self.is_active and not self.is_used and self.expires_at > timezone.now()

    def mark_as_used(self):
        """Mark the reset as used."""
        self.is_active = False
        self.used_at = timezone.now()
        self.save(update_fields=["is_active", "used_at"])

    def save(self, *args, **kwargs):
        if not self.pk and not self.expires_at:
            from datetime import timedelta

            self.expires_at = timezone.now() + timedelta(minutes=self.EXPIRY_MINUTES)
        super().save(*args, **kwargs)
