"""
Management command to load initial data for the application.
This includes countries with multi-language support.
"""

import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Load initial data including countries"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force load even if data already exists",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(self.style.SUCCESS("Starting initial data load..."))

        try:
            with transaction.atomic():
                self._load_countries(options["force"])

            self.stdout.write(
                self.style.SUCCESS("✅ Initial data loaded successfully!")
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error loading initial data: {str(e)}")
            )
            raise CommandError(f"Failed to load initial data: {str(e)}")

    def _load_countries(self, force=False):
        """Load countries fixture."""
        from core.models import Country

        if not force and Country.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    "Countries already exist, skipping. Use --force to override."
                )
            )
            return

        fixture_path = os.path.join(settings.BASE_DIR, "fixtures", "countries.json")

        if not os.path.exists(fixture_path):
            raise CommandError(f"Countries fixture not found at: {fixture_path}")

        self.stdout.write("Loading countries...")
        call_command("loaddata", fixture_path, verbosity=0)

        count = Country.objects.count()
        self.stdout.write(self.style.SUCCESS(f"✅ Loaded {count} countries"))
