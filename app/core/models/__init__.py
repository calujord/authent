"""
Core models package.

Contains shared models used across the application.
"""

from .base import BaseModel, SoftDeleteManager, SoftDeleteQuerySet
from .country import Country
from .location import Location
from .notification import Notification

__all__ = [
    "BaseModel",
    "SoftDeleteQuerySet",
    "SoftDeleteManager",
    "Country",
    "Location",
    "Notification",
]
