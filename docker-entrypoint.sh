#!/bin/sh
# docker-entrypoint.sh
set -e

echo "==> [entrypoint] Ejecutando migraciones de base de datos..."
python manage.py migrate --noinput

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