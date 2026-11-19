
# core/settings_prod.py
"""Configuración de producción para Render.com."""

from .settings import *
import os
import dj_database_url

# SEGURIDAD
DEBUG = False

SECRET_KEY = os.environ['SECRET_KEY']

# HOSTS PERMITIDOS
_render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')
_extra_hosts = os.environ.get('ALLOWED_HOSTS', '').split(',')

ALLOWED_HOSTS = ['localhost', '127.0.0.1'] + (
    [_render_host] if _render_host else []
) + [host.strip() for host in _extra_hosts if host.strip()]

# BASE DE DATOS: PostgreSQL
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )
}

# CSRF
CSRF_TRUSTED_ORIGINS = []

if _render_host:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_render_host}')

for host in _extra_hosts:
    host = host.strip()
    if host and host not in ('localhost', '127.0.0.1'):
        CSRF_TRUSTED_ORIGINS.append(f'https://{host}')

# SEGURIDAD HTTPS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'

# ALMACENAMIENTO OPCIONAL EN AMAZON S3
_bucket = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')

if _bucket:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    AWS_STORAGE_BUCKET_NAME = _bucket
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = False
    MEDIA_URL = f'https://{_bucket}.s3.amazonaws.com/'

# ARCHIVOS ESTÁTICOS
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# LOGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(levelname)s] %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django.security': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# PERSONALIZACIÓN SKZ - PANEL DE ADMINISTRACIÓN
JAZZMIN_SETTINGS = {
    'site_title': 'LIZ SYSTEM',
    'site_header': 'LIZ SYSTEM',
    'site_brand': 'LIZ SYSTEM',
    'welcome_sign': 'Bienvenido a LIZ SYSTEM',
    'copyright': 'LIZ SYSTEM',
    'search_model': [
        'clientes.Cliente',
        'productos.Producto',
        'proveedores.Proveedor',
        'ventas.Venta',
    ],
    'topmenu_links': [
        {'name': 'Inicio', 'url': '/', 'new_window': False},
        {'name': 'Ver sitio', 'url': '/', 'new_window': True},
    ],
    'show_sidebar': True,
    'navigation_expanded': True,
    'hide_apps': [],
    'hide_models': [],
    'order_with_respect_to': [
        'clientes',
        'productos',
        'proveedores',
        'ventas',
        'reportes',
    ],
}

JAZZMIN_UI_TWEAKS = {
    'navbar_small_text': False,
    'footer_small_text': False,
    'body_small_text': False,
    'brand_small_text': False,
    'brand_colour': 'navbar-dark',
    'accent': 'accent-danger',
    'navbar': 'navbar-dark',
    'navbar_fixed': True,
    'sidebar': 'sidebar-dark-danger',
    'sidebar_nav_small_text': False,
    'sidebar_nav_legacy_style': True,
    'sidebar_nav_compact_style': False,
    'sidebar_nav_flat_style': True,
    'theme': 'darkly',
    'dark_mode_theme': 'darkly',
    'button_classes': {
        'primary': 'btn-danger',
        'secondary': 'btn-secondary',
        'info': 'btn-info',
        'warning': 'btn-warning',
        'danger': 'btn-danger',
        'success': 'btn-success',
    },
}

# En producción, Celery utiliza Redis
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_TASK_STORE_EAGER_RESULT = True