
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crea o actualiza el administrador usando variables de entorno."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME", "admin")
        password = os.environ.get("ADMIN_PASSWORD")
        email = os.environ.get("ADMIN_EMAIL", "")

        if not password:
            raise CommandError(
                "Falta configurar la variable ADMIN_PASSWORD en Render."
            )

        User = get_user_model()
        user, created = User.objects.get_or_create(
            **{User.USERNAME_FIELD: username},
            defaults={"email": email},
        )

        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)

        if email and hasattr(user, "email"):
            user.email = email

        user.save()

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Administrador {username} creado correctamente."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Administrador {username} actualizado correctamente."
                )
            )
