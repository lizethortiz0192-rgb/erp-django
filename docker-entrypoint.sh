#!/bin/sh
set -e

echo "==> [entrypoint] Ejecutando migraciones de base de datos..."
python manage.py migrate --noinput

echo "==> [entrypoint] Garantizando objeto Site por defecto (id=1)..."
python manage.py shell -c "from django.contrib.sites.models import Site; Site.objects.get_or_create(id=1, defaults={'domain': 'erp-django-1.onrender.com', 'name': 'ERP Django'})" || true

echo "==> [entrypoint] Creando grupos de permisos..."
python manage.py crear_grupos || true

echo "==> [entrypoint] Creando superusuario automatizado..."
python manage.py createsuperuser --noinput || true

echo "==> [entrypoint] Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "==> [entrypoint] Iniciando Gunicorn..."
exec gunicorn core.wsgi \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --log-file - \
    --access-logfile -