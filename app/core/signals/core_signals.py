"""
Core app signal handlers.

This module contains all signal handlers related to the core app,
including Country and Location models.
"""

import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.models import Country, Location

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Country)
def log_country_changes(sender, instance, created, **kwargs):
    """
    Log country creation and updates.

    This helps track changes to countries for audit purposes.
    """
    if created:
        logger.info(
            f"New Country created: '{instance.name}' (ISO2: {instance.code_iso2})"
        )
    else:
        logger.info(f"Country updated: '{instance.name}' (ISO2: {instance.code_iso2})")


@receiver(post_delete, sender=Country)
def log_country_deletion(sender, instance, **kwargs):
    """
    Log when a country is deleted.

    This is for audit purposes since countries should rarely be deleted.
    """
    logger.warning(
        f"Country '{instance.name}' (ISO2: {instance.code_iso2}) was deleted"
    )


@receiver(post_save, sender=Location)
def log_location_changes(sender, instance, created, **kwargs):
    """
    Log location creation and updates for audit purposes.
    """
    if created:
        logger.info(f"New Location created: '{instance.name}'")
    else:
        logger.info(f"Location updated: '{instance.name}'")
