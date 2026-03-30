from django.core.management.base import BaseCommand, CommandError

from users.models import User


class Command(BaseCommand):
    help = "Establece profile_type=developer a un usuario existente por email"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Email del usuario")

    def handle(self, *args, **options):
        email = options["email"].strip()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"No existe ningún usuario con el email '{email}'")

        if user.profile_type == "developer":
            self.stdout.write(
                self.style.WARNING(
                    f"⚠ {email} ya tiene profile_type=developer, sin cambios"
                )
            )
            return

        previous = user.profile_type
        user.profile_type = "developer"
        user.save(update_fields=["profile_type"])

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Usuario actualizado correctamente\n"
                f"  Email       : {user.email}\n"
                f"  Nombre      : {user.get_full_name() or '-'}\n"
                f"  profile_type: {previous} → developer"
            )
        )
