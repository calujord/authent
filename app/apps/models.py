import secrets
import string

from django.db import models


def generate_api_key():
    """Genera una API key segura con prefijo 'ak_' + 48 caracteres aleatorios."""
    alphabet = string.ascii_letters + string.digits
    return "ak_" + "".join(secrets.choice(alphabet) for _ in range(48))


class Application(models.Model):
    """
    Representa una aplicación cliente autorizada a usar el servicio de autenticación.
    Cada aplicación debe tener al menos una APIKey activa para poder realizar peticiones.
    """

    name = models.CharField(max_length=255, unique=True, verbose_name="Name")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        db_table = "auth_application"
        verbose_name = "Application"
        verbose_name_plural = "Applications"
        ordering = ["name"]

    def __str__(self):
        return self.name


class APIKey(models.Model):
    """
    API key asociada a una Application.
    Todas las requests a la API deben incluir una API key válida en el header X-API-Key.
    """

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="api_keys",
        verbose_name="Application",
    )
    key = models.CharField(
        max_length=64,
        unique=True,
        default=generate_api_key,
        editable=False,
        verbose_name="Key",
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Name",
        help_text="Descriptive name for this key (e.g. 'iOS App Production')",
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expires at",
        help_text="Leave empty for no expiration",
    )
    last_used_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Last used at"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    class Meta:
        db_table = "auth_api_key"
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.application.name} — {self.name}"

    @property
    def is_valid(self):
        from django.utils import timezone

        if not self.is_active or not self.application.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    def mark_used(self):
        from django.utils import timezone

        APIKey.objects.filter(pk=self.pk).update(last_used_at=timezone.now())
