
# core/urls.py
"""Enrutador principal del ERP Django."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework.authtoken.views import obtain_auth_token

from . import views

# Rutas API de las aplicaciones
from productos.api_urls import urlpatterns as productos_api
from clientes.api_urls import urlpatterns as clientes_api
from proveedores.api_urls import urlpatterns as proveedores_api
from ventas.api_urls import urlpatterns as ventas_api

api_urlpatterns = (
    productos_api
    + clientes_api
    + proveedores_api
    + ventas_api
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.bienvenida, name='inicio'),

    # Autenticación
    path('accounts/', include('allauth.urls')),

    # Aplicaciones del ERP
    path('clientes/', include('clientes.urls', namespace='clientes')),
    path('proveedores/', include('proveedores.urls', namespace='proveedores')),
    path('productos/', include('productos.urls', namespace='productos')),
    path('catalogo/', include('catalogo.urls', namespace='catalogo')),
    path('ventas/', include('ventas.urls', namespace='ventas')),
    path('reportes/', include('reportes.urls', namespace='reportes')),

    # API REST
    path('api/', include(api_urlpatterns)),
    path('api/token/', obtain_auth_token, name='api_token'),
]

# Archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
