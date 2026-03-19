"""
Location model for geographic data.

This module contains the Location model for storing geographic points
and location-based data used across the application.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import BaseModel


class Location(BaseModel):
    """
    Location model for storing geographic points.

    This model represents a geographic location with coordinates
    and additional metadata. Used for storing points of interest,
    business locations, or any geographic reference.
    """

    name = models.CharField(
        _("Name"), max_length=200, help_text=_("Name or description of this location")
    )

    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Optional description of the location"),
    )

    latitude = models.DecimalField(
        _("Latitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text=_("Latitude coordinate"),
    )

    longitude = models.DecimalField(
        _("Longitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text=_("Longitude coordinate"),
    )

    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether this location is active and available"),
    )

    class Meta:
        db_table = "core_location"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"]),
        ]
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")

    def __str__(self):
        """Return string representation."""
        return f"{self.name}"

    def __repr__(self):
        """Return detailed representation."""
        return f"<Location: {self.name} ({self.longitude}, {self.latitude})>"

    @property
    def coordinates(self):
        """Get coordinates as tuple (longitude, latitude)."""
        if self.latitude is not None and self.longitude is not None:
            return (float(self.longitude), float(self.latitude))
        return None
