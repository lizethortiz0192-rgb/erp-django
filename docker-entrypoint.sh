#!/bin/sh
set -e

echo "==> [entrypoint] Ejecutando migraciones de base de datos..."
python manage.py migrate --noinput

echo "==> [entrypoint] Garantizando objeto Site por defecto (id=1)..."
python manage.py shell -c "from django.contrib.sites.models import Site; Site.objects.get_or_create(id=1, defaults={'domain': 'erp-django-1.onrender.com', 'name': 'ERP Django'})" || true

echo "==> [entrypoint] Creando grupos de permisos..."
python manage.py crear_grupos || true

echo "==> [entrypoint] Verificando superusuario automatizado..."
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
    python manage.py shell -c "import os, sys; from django.contrib.auth import get_user_model; U = get_user_model(); sys.exit(0 if U.objects.filter(username=os.environ['DJANGO_SUPERUSER_USERNAME']).exists() else 1)" \
        || python manage.py createsuperuser --noinput \
        || true
fi

PORT="${PORT:-8000}"
echo "==> [entrypoint] Iniciando Gunicorn en puerto ${PORT}..."
exec gunicorn core.wsgi \
    --bind "0.0.0.0:${PORT}" \
    --workers "${WEB_CONCURRENCY:-1}" \
    --threads 2 \
    --timeout 120 \
    --log-file - \
    --access-logfile -