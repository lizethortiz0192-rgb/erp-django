
# catalogo/checkout_utils.py
"""Funciones auxiliares para el proceso de checkout — W14."""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from clientes.models import Cliente
from configuracion.models import ConfiguracionERP
from ventas.models import Pedido


def calcular_totales(carrito: dict) -> dict:
    """Calcula subtotal, IVA y total del carrito."""

    config = ConfiguracionERP.get_instance()
    iva_pct = config.iva_porcentaje / Decimal('100')

    subtotal = sum(
        Decimal(datos['precio']) * int(datos['cantidad'])
        for datos in carrito.values()
    )

    iva_monto = (subtotal * iva_pct).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )

    total = subtotal + iva_monto

    return {
        'subtotal': subtotal,
        'iva_pct': config.iva_porcentaje,
        'iva_monto': iva_monto,
        'total': total,
    }


def obtener_o_crear_cliente(user) -> Cliente:
    """Obtiene o crea un cliente vinculado al usuario Django."""

    correo = user.email or f"{user.username}@erp.local"

    nombre = user.get_full_name() or user.username

    cliente, _ = Cliente.objects.get_or_create(
        correo=correo,
        defaults={
            'nombre': nombre,
            'activo': True
        }
    )

    if cliente.nombre != nombre and user.get_full_name():
        cliente.nombre = nombre
        cliente.save(update_fields=['nombre'])

    return cliente


def generar_numero_pedido() -> str:
    """
    Genera un número de pedido disponible.

    Formato: PED-YYYY-NNNN

    Comprueba que el número no exista antes de devolverlo.
    """

    anio = date.today().year
    prefijo = f'PED-{anio}-'

    pedidos_existentes = Pedido.objects.filter(
        numero_pedido__startswith=prefijo
    ).values_list('numero_pedido', flat=True)

    numeros_utilizados = set()

    for numero in pedidos_existentes:
        try:
            consecutivo = int(numero.replace(prefijo, '', 1))
            numeros_utilizados.add(consecutivo)
        except (ValueError, TypeError):
            continue

    siguiente = len(numeros_utilizados) + 1

    while siguiente in numeros_utilizados:
        siguiente += 1

    # Comprobación adicional contra la base de datos.
    while True:
        numero_pedido = f'{prefijo}{siguiente:04d}'

        if not Pedido.objects.filter(
            numero_pedido=numero_pedido
        ).exists():
            return numero_pedido

        siguiente += 1
