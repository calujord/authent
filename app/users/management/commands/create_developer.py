import getpass

from django.core.management.base import BaseCommand, CommandError

from users.models import User


class Command(BaseCommand):
    help = "Crea un nuevo usuario con profile_type=developer"

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, help="Email del usuario")
        parser.add_argument("--first-name", type=str, help="Nombre")
        parser.add_argument("--last-name", type=str, help="Apellido")
        parser.add_argument(
            "--password",
            type=str,
            help="Contraseña (si no se indica, se solicita de forma interactiva)",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Sin interacción. Requiere --email y --password.",
        )

    def handle(self, *args, **options):
        no_input = options["no_input"]

        # ── Email ──────────────────────────────────────────────────────────
        email = options.get("email")
        if not email:
            if no_input:
                raise CommandError("Se requiere --email cuando se usa --no-input")
            email = input("Email: ").strip()
        if not email:
            raise CommandError("El email es obligatorio")

        if User.objects.filter(email=email).exists():
            raise CommandError(f"Ya existe un usuario con el email '{email}'")

        # ── Nombre ─────────────────────────────────────────────────────────
        first_name = options.get("first_name") or ""
        last_name = options.get("last_name") or ""
        if not no_input:
            if not first_name:
                first_name = input("Nombre: ").strip()
            if not last_name:
                last_name = input("Apellido: ").strip()

        # ── Contraseña ─────────────────────────────────────────────────────
        password = options.get("password")
        if not password:
            if no_input:
                raise CommandError("Se requiere --password cuando se usa --no-input")
            password = getpass.getpass("Contraseña: ")
            password_confirm = getpass.getpass("Confirmar contraseña: ")
            if password != password_confirm:
                raise CommandError("Las contraseñas no coinciden")
        if not password:
            raise CommandError("La contraseña es obligatoria")

        # ── Crear usuario ──────────────────────────────────────────────────
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            profile_type="developer",
            email_verified=True,
            is_active=True,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Usuario developer creado correctamente\n"
                f"  Email       : {user.email}\n"
                f"  Nombre      : {user.get_full_name() or '-'}\n"
                f"  profile_type: {user.profile_type}\n"
                f"  UUID        : {user.id}"
            )
        )
