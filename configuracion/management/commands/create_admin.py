import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crea un superusuario usando variables de entorno."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME")
        email = os.environ.get("ADMIN_EMAIL", "")
        password = os.environ.get("ADMIN_PASSWORD")

        if not username or not password:
            raise CommandError(
                "Configura ADMIN_USERNAME y ADMIN_PASSWORD."
            )

        User = get_user_model()

        if User.objects.filter(
            **{User.USERNAME_FIELD: username}
        ).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"El usuario {username} ya existe."
                )
            )
            return

        User.objects.create_superuser(
            **{
                User.USERNAME_FIELD: username,
                "email": email,
                "password": password,
            }
        )

        self.stdout.write(
            self.style.SUCCESS("Superusuario creado correctamente.")
        )
