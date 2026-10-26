# core/views.py
"""Vistas principales del ERP Django."""

from django.shortcuts import render
from django.urls import reverse


def bienvenida(request):
    """Página de inicio del ERP con tarjetas de módulos."""

    modulos = [
        {
            'nombre': 'Productos',
            'descripcion': 'Consulta el catálogo de productos.',
            'url': reverse('productos:lista'),
            'icono': '📦',
        },
        {
            'nombre': 'Clientes',
            'descripcion': 'Consulta la información de clientes.',
            'url': reverse('clientes:lista'),
            'icono': '👥',
        },
        {
            'nombre': 'Proveedores',
            'descripcion': 'Consulta el catálogo de proveedores.',
            'url': reverse('proveedores:lista'),
            'icono': '🏢',
        },
        {
            'nombre': 'Ventas',
            'descripcion': 'Consulta las ventas registradas.',
            'url': reverse('ventas:lista'),
            'icono': '🛒',
        },
        {
            'nombre': 'Reportes',
            'descripcion': 'Consulta los reportes del sistema.',
            'url': reverse('reportes:inicio'),
            'icono': '📊',
        },
        {
            'nombre': 'Administración',
            'descripcion': 'Accede al panel administrativo.',
            'url': reverse('admin:index'),
            'icono': '⚙️',
        },
    ]

    return render(
        request,
        'bienvenida.html',
        {'modulos': modulos},
    )