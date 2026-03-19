import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """Custom QuerySet with soft delete support."""

    def delete(self):
        """Soft delete all objects in the queryset."""
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        """Permanently delete all objects in the queryset."""
        return super().delete()

    def active(self):
        """Filter only active (non-deleted) objects."""
        return self.filter(is_deleted=False)

    def deleted(self):
        """Filter only deleted objects."""
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Manager with soft delete support."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

    def active(self):
        """Get only active (non-deleted) objects."""
        return self.get_queryset().active()

    def deleted(self):
        """Get only deleted objects."""
        return self.get_queryset().deleted()

    def with_deleted(self):
        """Get all objects including deleted ones."""
        return self.get_queryset()


class BaseModel(models.Model):
    """
    Base model with complete audit trail functionality and UUID primary key.

    Tracks creation, modification, and soft deletion with user attribution.
    Uses UUID as primary key for security and scalability.
    """

    # UUID primary key for security
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this record",
    )

    # Creation fields
    created_at = models.DateTimeField("Created at", auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_created",
        verbose_name="Created by",
        null=True,
        blank=True,
        help_text="User who created this record",
    )

    # Modification fields
    updated_at = models.DateTimeField("Updated at", auto_now=True, db_index=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_updated",
        verbose_name="Updated by",
        null=True,
        blank=True,
        help_text="User who last updated this record",
    )

    # Soft deletion fields
    is_deleted = models.BooleanField("Is deleted", default=False, db_index=True)
    deleted_at = models.DateTimeField(
        "Deleted at", null=True, blank=True, db_index=True
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_deleted",
        verbose_name="Deleted by",
        null=True,
        blank=True,
        help_text="User who deleted this record",
    )

    # Additional metadata
    version = models.PositiveIntegerField(
        "Version", default=1, help_text="Record version for optimistic locking"
    )
    notes = models.TextField(
        "Notes", blank=True, help_text="Optional notes about changes"
    )

    # Managers
    objects = SoftDeleteManager()  # Default manager with soft delete support

    class Meta:
        abstract = True
        ordering = ["-created_at"]
        get_latest_by = "created_at"

    def save(self, *args, **kwargs):
        """Override save to handle version control and user tracking."""
        user = kwargs.pop("user", None)

        if self.pk is None:  # New record
            if user:
                self.created_by = user
        else:  # Existing record
            if user:
                self.updated_by = user
            self.version += 1

        super().save(*args, **kwargs)

    def delete(self, user=None, hard=False):
        """Soft delete by default, hard delete if specified."""
        if hard:
            super().delete()
        else:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            if user:
                self.deleted_by = user
            self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

    def restore(self, user=None):
        """Restore soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        if user:
            self.updated_by = user
        self.save(
            update_fields=[
                "is_deleted",
                "deleted_at",
                "deleted_by",
                "updated_by",
                "updated_at",
            ]
        )

    def get_audit_trail(self):
        """Return audit trail information."""
        return {
            "created": {
                "date": self.created_at,
                "user": (
                    self.created_by.get_full_name() if self.created_by else "System"
                ),
            },
            "updated": (
                {
                    "date": self.updated_at,
                    "user": (
                        self.updated_by.get_full_name() if self.updated_by else "System"
                    ),
                }
                if self.updated_at != self.created_at
                else None
            ),
            "deleted": (
                {
                    "date": self.deleted_at,
                    "user": (
                        self.deleted_by.get_full_name() if self.deleted_by else "System"
                    ),
                }
                if self.is_deleted
                else None
            ),
            "version": self.version,
        }

    @property
    def is_active(self):
        """Check if record is active (not deleted)."""
        return not self.is_deleted

    def __str__(self):
        return f"{self.__class__.__name__} #{str(self.pk)[:8]} (v{self.version})"
