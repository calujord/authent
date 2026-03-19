"""
Management command to load countries data directly (without fixtures).
"""

import uuid

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Country


class Command(BaseCommand):
    help = "Load countries data into the database"

    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(self.style.SUCCESS("Loading countries..."))

        countries_data = [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "name": "España",
                "code_iso2": "ES",
                "code_iso3": "ESP",
                "numeric_code": "724",
                "name_pt": "Espanha",
                "name_en": "Spain",
                "name_fr": "Espagne",
                "name_it": "Spagna",
                "phone_code": "+34",
                "currency_code": "EUR",
                "is_active": True,
                "sort_order": 1,
            },
            {
                "id": "00000000-0000-0000-0000-000000000002",
                "name": "Portugal",
                "code_iso2": "PT",
                "code_iso3": "PRT",
                "numeric_code": "620",
                "name_pt": "Portugal",
                "name_en": "Portugal",
                "name_fr": "Portugal",
                "name_it": "Portogallo",
                "phone_code": "+351",
                "currency_code": "EUR",
                "is_active": True,
                "sort_order": 2,
            },
            {
                "id": "00000000-0000-0000-0000-000000000003",
                "name": "México",
                "code_iso2": "MX",
                "code_iso3": "MEX",
                "numeric_code": "484",
                "name_pt": "México",
                "name_en": "Mexico",
                "name_fr": "Mexique",
                "name_it": "Messico",
                "phone_code": "+52",
                "currency_code": "MXN",
                "is_active": True,
                "sort_order": 3,
            },
        ]

        created_count = 0
        updated_count = 0

        for country_data in countries_data:
            country_id = uuid.UUID(country_data.pop("id"))

            country, created = Country.objects.update_or_create(
                id=country_id,
                defaults={
                    **country_data,
                    "created_at": timezone.now(),
                    "updated_at": timezone.now(),
                },
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Created: {country.name} ({country.code_iso2})"
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"🔄 Updated: {country.name} ({country.code_iso2})"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Done! Created: {created_count}, Updated: {updated_count}"
            )
        )
