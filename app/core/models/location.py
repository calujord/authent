"""
Location model for geographic data.

This module contains the Location model for storing geographic points
and location-based data used across the application.
"""

from django.contrib.gis.db import models
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

    point = models.PointField(
        _("Geographic Point"),
        srid=4326,
        help_text=_("Geographic coordinates (latitude, longitude)"),
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
        return f"<Location: {self.name} ({self.point.x:.6f}, {self.point.y:.6f})>"

    @property
    def latitude(self):
        """Get latitude from point."""
        return self.point.y if self.point else None

    @property
    def longitude(self):
        """Get longitude from point."""
        return self.point.x if self.point else None

    @property
    def coordinates(self):
        """Get coordinates as tuple (longitude, latitude)."""
        if self.point:
            return (self.point.x, self.point.y)
        return None

    def get_distance_to(self, other_point):
        """
        Calculate distance to another point.

        Args:
            other_point: Another Point object or Location instance

        Returns:
            Distance object with the distance between points
        """
        from django.contrib.gis.measure import Distance

        if hasattr(other_point, "point"):
            other_point = other_point.point

        return Distance(
            m=self.point.distance(other_point) * 111319.9
        )  # Convert to meters

    @classmethod
    def find_nearby(cls, point, radius_km=10):
        """
        Find locations within a given radius.

        Args:
            point: Point object or tuple (longitude, latitude)
            radius_km: Radius in kilometers (default: 10)

        Returns:
            QuerySet of nearby locations
        """
        from django.contrib.gis.geos import Point
        from django.contrib.gis.measure import D

        if not isinstance(point, Point):
            point = Point(point[0], point[1], srid=4326)

        return (
            cls.objects.filter(
                point__distance_lte=(point, D(km=radius_km)), is_active=True
            )
            .annotate(distance=models.Distance("point", point))
            .order_by("distance")
        )
