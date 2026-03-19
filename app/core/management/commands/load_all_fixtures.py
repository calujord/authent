"""
Management command para cargar TODOS los fixtures del sistema.
Carpeta unificada: fixtures/
"""

import os

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Carga todos los fixtures del sistema desde fixtures/"

    FIXTURES_ORDER = [
        {"file": "countries.json", "label": "Países", "model": "core.Country"},
        {"file": "groups.json", "label": "Grupos/Permisos", "model": "auth.Group"},
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            nargs="+",
            help="Cargar solo fixtures específicos (ej: --only countries taxes)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Forzar recarga incluso si ya hay datos",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="Listar fixtures disponibles sin cargar",
        )

    def handle(self, *args, **options):
        fixtures_dir = os.path.join(settings.BASE_DIR, "fixtures")

        if options["list"]:
            self._list_fixtures(fixtures_dir)
            return

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("📦 Cargando fixtures del sistema"))
        self.stdout.write(f"   Origen: {fixtures_dir}")
        self.stdout.write("=" * 60)

        only = options.get("only")
        force = options.get("force", False)
        loaded = 0
        skipped = 0
        errors = 0

        for fixture in self.FIXTURES_ORDER:
            filename = fixture["file"]
            label = fixture["label"]
            basename = filename.replace(".json", "")

            # Filter by --only
            if only and basename not in only and filename not in only:
                continue

            filepath = os.path.join(fixtures_dir, filename)

            if not os.path.exists(filepath):
                self.stdout.write(
                    self.style.WARNING(f"  ⚠️  {filename} no encontrado, omitiendo")
                )
                skipped += 1
                continue

            try:
                # Check if data already exists
                model = self._get_model(fixture["model"])
                if model and model.objects.exists() and not force:
                    count = model.objects.count()
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⏭️  {label} ya tiene {count} registros (--force para recargar)"
                        )
                    )
                    skipped += 1
                    continue

                call_command("loaddata", filepath, verbosity=0)
                count = model.objects.count() if model else "?"
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ {label}: {count} registros")
                )

                loaded += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ {label}: {str(e)}"))
                errors += 1

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            f"  Cargados: {loaded} | Omitidos: {skipped} | Errores: {errors}"
        )
        self.stdout.write("=" * 60)

    def _get_model(self, model_path):
        """Obtener modelo Django desde string 'app.Model'"""
        try:
            from django.apps import apps

            app_label, model_name = model_path.split(".")
            return apps.get_model(app_label, model_name)
        except Exception:
            return None

    def _list_fixtures(self, fixtures_dir):
        """Listar fixtures disponibles"""
        self.stdout.write("\n📋 Fixtures disponibles:\n")
        for fixture in self.FIXTURES_ORDER:
            filepath = os.path.join(fixtures_dir, fixture["file"])
            exists = "✅" if os.path.exists(filepath) else "❌"
            model = self._get_model(fixture["model"])
            count = model.objects.count() if model else "?"
            self.stdout.write(
                f"  {exists} {fixture['file']:<40} {fixture['label']:<25} ({count} en BD)"
            )
        self.stdout.write("")
