# core/settings_prod.py
"""ConfiguraciÃ³n de producciÃ³n â€” Render.com (versiÃ³n final W03).

Hereda settings.py y sobreescribe todo lo necesario para producciÃ³n.

Variables de entorno requeridas en Render Dashboard:
    SECRET_KEY              â†’ clave aleatoria de â‰¥ 50 caracteres
    DATABASE_URL            â†’ proporcionada automÃ¡ticamente por Render PostgreSQL
    DJANGO_SETTINGS_MODULE  â†’ core.settings_prod
    ALLOWED_HOSTS           â†’ tu-app.onrender.com (o dejar vacÃ­o para auto)

Uso local con Docker:
    export DJANGO_SETTINGS_MODULE=core.settings_prod
    export SECRET_KEY=dev-clave-temporal
    export DATABASE_URL=postgres://erp_user:erp_pass@db:5432/erp_db
    gunicorn core.wsgi --bind 0.0.0.0:8000
"""
from .settings import *   # hereda toda la configuraciÃ³n base
import os
import dj_database_url

# â”€â”€ SEGURIDAD BÃSICA â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
DEBUG = False
SECRET_KEY = os.environ['SECRET_KEY']   # falla intencionalmente si no existe

# â”€â”€ HOSTS PERMITIDOS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Render inyecta RENDER_EXTERNAL_HOSTNAME automÃ¡ticamente
_render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')
_extra_hosts  = os.environ.get('ALLOWED_HOSTS', '').split(',')

ALLOWED_HOSTS = ['localhost', '127.0.0.1'] + (
    [_render_host] if _render_host else []
) + [h for h in _extra_hosts if h]

# â”€â”€ BASE DE DATOS: PostgreSQL via DATABASE_URL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,          # conexiones persistentes 10 min
        conn_health_checks=True,   # verifica conexiÃ³n antes de usarla
        ssl_require=True,          # Render requiere SSL en PostgreSQL
    )
}

# â”€â”€ CSRF: dominios de confianza â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CSRF_TRUSTED_ORIGINS = []
if _render_host:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_render_host}')

# â”€â”€ HEADERS HTTP SEGUROS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SECURE_SSL_REDIRECT            = True
SECURE_HSTS_SECONDS            = 31536000    # 1 aÃ±o
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD            = True
SESSION_COOKIE_SECURE          = True
CSRF_COOKIE_SECURE             = True
X_FRAME_OPTIONS                = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF    = True
SECURE_REFERRER_POLICY         = 'same-origin'

# â”€â”€ ARCHIVOS ESTÃTICOS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# WhiteNoise ya configurado en settings.py; solo confirmar almacenamiento
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# â”€â”€ LOGGING: solo WARNING y superiores en producciÃ³n â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '[%(levelname)s] %(name)s: %(message)s'},
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

# ============================================================
# PERSONALIZACION SKZ - PANEL DE ADMINISTRACION
# ============================================================

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
