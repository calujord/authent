from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User


class Command(BaseCommand):
    help = "Create sample user fixtures for testing"

    def handle(self, *args, **options):
        users_data = [
            {
                "email": "user1@atharix.com",
                "first_name": "Carlos",
                "last_name": "García",
                "birth_date": "1985-03-15",
                "phone_number": "+34666123456",
                "gender": "M",
                "password": "TestPassword123!",
                "email_verified": True,
                "is_staff": True,  # ← Make staff so they can be business admin
            },
            {
                "email": "user2@atharix.com",
                "first_name": "María",
                "last_name": "López",
                "birth_date": "1990-07-22",
                "phone_number": "+34666789012",
                "gender": "F",
                "password": "TestPassword123!",
                "email_verified": True,
                "is_staff": False,
            },
            {
                "email": "assistant@atharix.com",
                "first_name": "Juan",
                "last_name": "Martínez",
                "birth_date": "1995-11-30",
                "phone_number": "+34666345678",
                "gender": "M",
                "password": "TestPassword123!",
                "email_verified": False,
                "is_staff": False,
            },
        ]

        for user_data in users_data:
            email = user_data.pop("email")
            password = user_data.pop("password")

            # Check if user already exists
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f"⚠ User {email} already exists, skipping...")
                )
                continue

            # Create user with password
            user = User.objects.create_user(email=email, password=password, **user_data)

            # Update last_login to current time
            user.last_login = timezone.now()
            user.save(update_fields=["last_login"])

            staff_badge = " (STAFF)" if user.is_staff else ""
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Created user: {user.email} (Name: {user.get_full_name()}){staff_badge}"
                )
            )

        self.stdout.write(self.style.SUCCESS("\n✓ All fixtures loaded successfully!"))
