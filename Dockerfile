# Dockerfile — ERP Django
FROM python:3.11-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias de sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libcairo-gobject2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    libpq-dev \
    gcc \
 && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente del proyecto
COPY . .

# Recolectar archivos estáticos durante el build (CSS/JS del admin).
# Sin esto el admin se ve sin estilos ("No directory at: /app/staticfiles/").
RUN python manage.py collectstatic --no-input --settings=core.settings \
    || echo "AVISO: collectstatic falló, revisa el log del build"

# Dar permisos de ejecución al entrypoint (y quitar saltos de línea de Windows)
RUN sed -i 's/\r$//' docker-entrypoint.sh \
 && chmod +x docker-entrypoint.sh

EXPOSE 8000

# Punto de entrada obligatorio para ejecutar migraciones al arrancar
ENTRYPOINT ["./docker-entrypoint.sh"]