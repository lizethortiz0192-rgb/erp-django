
"""
Vistas del módulo de catálogo y carrito — W13/W14/W16.

Incluye:
- Catálogo público y filtros.
- Administración del carrito mediante sesiones.
- Integración de pagos con Stripe.
- Confirmación de pedidos.
- Descuento seguro del inventario.
- Envío asíncrono de correos mediante Celery.
"""

import logging
from decimal import Decimal, InvalidOperation

import stripe

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView

from productos.models import Producto
from ventas.models import Pedido
from ventas.tasks import enviar_confirmacion_pedido

from .filters import ProductoFilter
from .checkout_utils import (
    calcular_totales,
    generar_numero_pedido,
    obtener_o_crear_cliente,
)


logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


# ============================================================
# CATÁLOGO
# ============================================================

class CatalogoView(ListView):
    """Catálogo público de productos con filtros."""

    model = Producto
    template_name = 'catalogo/catalogo.html'
    context_object_name = 'productos'
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Producto.objects
            .select_related('categoria', 'proveedor')
            .filter(activo=True)
            .order_by('nombre')
        )

        self.filtro = ProductoFilter(
            self.request.GET,
            queryset=qs
        )

        return self.filtro.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filtro'] = self.filtro
        ctx['categorias'] = (
            self.filtro.form.fields['categoria'].queryset
        )
        return ctx


# ============================================================
# CARRITO
# ============================================================

def _obtener_carrito(request):
    """Obtiene el carrito de la sesión."""

    return request.session.get('carrito', {})


def _guardar_carrito(request, carrito):
    """Guarda los cambios del carrito en la sesión."""

    request.session['carrito'] = carrito
    request.session.modified = True


def ver_carrito(request):
    """Muestra los productos y el total del carrito."""

    carrito = _obtener_carrito(request)

    items = []
    total = Decimal('0.00')

    for prod_id, datos in carrito.items():
        precio = Decimal(str(datos['precio']))
        cantidad = int(datos['cantidad'])

        subtotal = precio * cantidad
        total += subtotal

        items.append({
            'prod_id': prod_id,
            'nombre': datos['nombre'],
            'precio': precio,
            'cantidad': cantidad,
            'subtotal': subtotal,
            'imagen': datos.get('imagen'),
        })

    return render(
        request,
        'catalogo/carrito.html',
        {
            'items': items,
            'total': total,
        }
    )


def agregar_al_carrito(request, producto_id: int):
    """Agrega un producto al carrito."""

    if request.method != 'POST':
        return redirect('catalogo:catalogo')

    producto = get_object_or_404(
        Producto,
        pk=producto_id,
        activo=True
    )

    carrito = _obtener_carrito(request)
    clave = str(producto_id)

    try:
        cantidad = int(request.POST.get('cantidad', 1))
    except (TypeError, ValueError):
        messages.error(request, 'Cantidad inválida.')
        return redirect('catalogo:catalogo')

    if cantidad <= 0:
        messages.warning(
            request,
            'La cantidad debe ser mayor que cero.'
        )
        return redirect('catalogo:catalogo')

    if clave in carrito:
        carrito[clave]['cantidad'] += cantidad
    else:
        carrito[clave] = {
            'nombre': producto.nombre,
            'precio': str(producto.precio),
            'cantidad': cantidad,
            'imagen': (
                producto.imagen.name
                if producto.imagen else None
            ),
        }

    _guardar_carrito(request, carrito)

    messages.success(
        request,
        f'"{producto.nombre}" agregado al carrito.'
    )

    next_url = (
        request.POST.get('next')
        or request.META.get('HTTP_REFERER')
    )

    return redirect(next_url or 'catalogo:catalogo')


def remover_del_carrito(request, producto_id: int):
    """Elimina un producto del carrito."""

    if request.method != 'POST':
        return redirect('catalogo:carrito')

    carrito = _obtener_carrito(request)
    clave = str(producto_id)

    nombre = carrito.get(clave, {}).get(
        'nombre',
        'Producto'
    )

    carrito.pop(clave, None)

    _guardar_carrito(request, carrito)

    messages.warning(
        request,
        f'"{nombre}" eliminado del carrito.'
    )

    return redirect('catalogo:carrito')


def actualizar_cantidad(request, producto_id: int):
    """Actualiza la cantidad de un producto."""

    if request.method != 'POST':
        return redirect('catalogo:carrito')

    carrito = _obtener_carrito(request)
    clave = str(producto_id)

    try:
        cantidad = int(request.POST.get('cantidad', 1))
    except (TypeError, ValueError):
        messages.error(request, 'Cantidad inválida.')
        return redirect('catalogo:carrito')

    if clave in carrito:
        if cantidad > 0:
            carrito[clave]['cantidad'] = cantidad
        else:
            carrito.pop(clave)

    _guardar_carrito(request, carrito)

    return redirect('catalogo:carrito')


def vaciar_carrito(request):
    """Vacía el carrito."""

    if request.method == 'POST':
        _guardar_carrito(request, {})

        messages.info(request, 'Carrito vaciado.')

    return redirect('catalogo:carrito')


# ============================================================
# CHECKOUT
# ============================================================

@login_required
def checkout(request):
    """Prepara el pedido y crea el PaymentIntent de Stripe."""

    carrito = _obtener_carrito(request)

    if not carrito:
        messages.warning(
            request,
            'Tu carrito está vacío.'
        )
        return redirect('catalogo:catalogo')

    publishable_key = settings.STRIPE_PUBLISHABLE_KEY
    secret_key = settings.STRIPE_SECRET_KEY

    if not secret_key or not publishable_key:
        logger.error(
            'Faltan las claves de configuración de Stripe.'
        )

        messages.error(
            request,
            'El servicio de pago no está disponible temporalmente.'
        )
        return redirect('catalogo:pago_error')

    # Calcular totales.
    try:
        totales = calcular_totales(carrito)

        if totales['total'] <= 0:
            messages.error(
                request,
                'El total del carrito no es válido.'
            )
            return redirect('catalogo:carrito')

    except Exception:
        logger.exception(
            'Error al calcular los totales del checkout.'
        )

        messages.error(
            request,
            'No fue posible calcular el total del carrito.'
        )
        return redirect('catalogo:pago_error')

    # Preparar los productos.
    items_checkout = []

    try:
        for prod_id, datos in carrito.items():
            precio = Decimal(str(datos['precio']))
            cantidad = int(datos['cantidad'])

            if precio < 0 or cantidad <= 0:
                raise ValueError(
                    'Precio o cantidad inválidos.'
                )

            subtotal = precio * cantidad

            items_checkout.append({
                'prod_id': prod_id,
                'nombre': datos['nombre'],
                'precio': precio,
                'cantidad': cantidad,
                'subtotal': subtotal,
                'imagen': datos.get('imagen'),
            })

    except (KeyError, TypeError, ValueError, InvalidOperation):
        logger.exception(
            'El carrito contiene información inválida.'
        )

        messages.error(
            request,
            'Hay información inválida en tu carrito.'
        )
        return redirect('catalogo:carrito')

    # POST: crear pedido y PaymentIntent.
    if request.method == 'POST':

        pedido = None
        intent = None

        try:
            stripe.api_key = secret_key

            cliente = obtener_o_crear_cliente(request.user)
            numero = generar_numero_pedido()

            snapshot = [
                {
                    'producto_id': int(prod_id),
                    'nombre': datos['nombre'],
                    'cantidad': int(datos['cantidad']),
                    'precio': str(datos['precio']),
                }
                for prod_id, datos in carrito.items()
            ]

            pedido = Pedido.objects.create(
                numero_pedido=numero,
                cliente=cliente,
                estado='pendiente',
                total_pagado=totales['total'],
                items_snapshot=snapshot,
            )

            monto_centavos = int(
                (totales['total'] * 100).quantize(
                    Decimal('1')
                )
            )

            intent = stripe.PaymentIntent.create(
                amount=monto_centavos,
                currency='mxn',
                metadata={
                    'pedido_id': str(pedido.pk),
                    'pedido_num': pedido.numero_pedido,
                    'cliente': cliente.nombre,
                },
                idempotency_key=f'pedido-{pedido.pk}',
            )

            pedido.stripe_payment_intent_id = intent.id
            pedido.save(update_fields=['stripe_payment_intent_id'])

            logger.info(
                'PaymentIntent %s guardado en pedido %s.',
                intent.id,
                pedido.numero_pedido
            )

            # Guardar PaymentIntent en la sesión.
            pagos = request.session.get(
                'stripe_payment_intents',
                {}
            )

            pagos[str(pedido.pk)] = intent.id

            request.session['stripe_payment_intents'] = pagos
            request.session.modified = True

            logger.info(
                'PaymentIntent %s creado para pedido %s.',
                intent.id,
                pedido.numero_pedido
            )

            return render(
                request,
                'catalogo/checkout.html',
                {
                    'carrito': carrito,
                    'items': items_checkout,
                    'totales': totales,
                    'pedido': pedido,
                    'client_secret': intent.client_secret,
                    'publishable_key': publishable_key,
                }
            )

        except stripe.error.StripeError:
            logger.exception(
                'Error de Stripe durante el checkout.'
            )

            if pedido is not None:
                logger.warning(
                    'Se conserva el pedido pendiente %s para revision.',
                    pedido.numero_pedido
                )
                if intent is not None:
                    logger.error(
                        'PaymentIntent del pedido %s: %s',
                        pedido.numero_pedido,
                        intent.id
                    )

            messages.error(
                request,
                'No fue posible conectar con el servicio de pago.'
            )

            return redirect('catalogo:pago_error')

        except Exception:
            logger.exception(
                'Error inesperado durante el checkout.'
            )

            if pedido is not None:
                logger.warning(
                    'Se conserva el pedido pendiente %s para revision.',
                    pedido.numero_pedido
                )
                if intent is not None:
                    logger.error(
                        'PaymentIntent del pedido %s: %s',
                        pedido.numero_pedido,
                        intent.id
                    )

            messages.error(
                request,
                'No se pudo iniciar el pago. Inténtalo nuevamente.'
            )

            return redirect('catalogo:pago_error')

    # GET: mostrar resumen.
    return render(
        request,
        'catalogo/checkout.html',
        {
            'carrito': carrito,
            'items': items_checkout,
            'totales': totales,
            'pedido': None,
            'client_secret': None,
            'publishable_key': publishable_key,
        }
    )


# ============================================================
# CONFIRMACIÓN DE PAGO
# ============================================================

@login_required
def pago_exitoso(request, pedido_id: int):
    """
    Verifica el PaymentIntent directamente en Stripe.
    Confirma el pedido y descuenta el inventario una sola vez.
    """

    pedido = get_object_or_404(
        Pedido,
        pk=pedido_id
    )

    # Si el pedido ya está pagado, no repetir operaciones.
    if pedido.estado == 'pagado':
        _guardar_carrito(request, {})

        return render(
            request,
            'catalogo/pago_exitoso.html',
            {'pedido': pedido}
        )

    # Recuperar el ID del PaymentIntent.
    pagos = request.session.get(
        'stripe_payment_intents',
        {}
    )

    intent_id = (
        request.GET.get('payment_intent_id')
        or pagos.get(str(pedido.pk))
    )

    if not intent_id:
        logger.warning(
            'No se encontró PaymentIntent para pedido %s.',
            pedido.numero_pedido
        )

        messages.error(
            request,
            'No se encontró la referencia del pago. '
            'No vuelvas a realizar el cobro; solicita una revisión.'
        )

        return redirect('catalogo:pago_error')

    # --------------------------------------------------------
    # 1. VERIFICAR PAGO EN STRIPE
    # --------------------------------------------------------

    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY

        if not stripe.api_key:
            raise ValueError(
                'No está configurada la clave secreta de Stripe.'
            )

        # Consultar el PaymentIntent directamente en Stripe.
        intent = stripe.PaymentIntent.retrieve(intent_id)

        # CORRECCIÓN: convertir correctamente los metadatos.
        metadata_raw = intent.metadata

        if metadata_raw is None:
            metadata = {}

        elif hasattr(metadata_raw, 'to_dict'):
            metadata = metadata_raw.to_dict()

        elif isinstance(metadata_raw, dict):
            metadata = metadata_raw

        else:
            metadata = {}

        # Calcular el importe esperado en centavos.
        importe_esperado = int(
            (Decimal(str(pedido.total_pagado)) * 100).quantize(
                Decimal('1')
            )
        )

        importe_recibido = int(
            intent.amount_received or 0
        )

        moneda = (intent.currency or '').lower()

        # Comprobar que el pago pertenece a este pedido.
        pago_valido = (
            intent.status == 'succeeded'
            and str(metadata.get('pedido_id')) == str(pedido.pk)
            and importe_recibido == importe_esperado
            and moneda == 'mxn'
        )

        if not pago_valido:
            logger.warning(
                'Pago no válido. Pedido: %s. '
                'PaymentIntent: %s. Estado: %s. '
                'Importe recibido: %s. Importe esperado: %s. '
                'Moneda: %s. Pedido en metadata: %s.',
                pedido.numero_pedido,
                intent_id,
                intent.status,
                importe_recibido,
                importe_esperado,
                moneda,
                metadata.get('pedido_id')
            )

            messages.error(
                request,
                'Stripe todavía no confirma el pago '
                'o los datos del pago no coinciden. '
                'No vuelvas a realizar el cobro.'
            )

            return redirect('catalogo:pago_error')

    except stripe.error.StripeError:
        logger.exception(
            'Error de Stripe al verificar pedido %s.',
            pedido.numero_pedido
        )

        messages.error(
            request,
            'No fue posible verificar el pago. '
            'No vuelvas a realizar el cobro.'
        )

        return redirect('catalogo:pago_error')

    except Exception:
        logger.exception(
            'Error inesperado al verificar pedido %s.',
            pedido.numero_pedido
        )

        messages.error(
            request,
            'Ocurrió un error al verificar el pago. '
            'No vuelvas a realizar el cobro.'
        )

        return redirect('catalogo:pago_error')

    # --------------------------------------------------------
    # 2. CONFIRMAR PEDIDO Y DESCONTAR INVENTARIO
    # --------------------------------------------------------

    pedido_confirmado_ahora = False

    try:
        with transaction.atomic():

            pedido_bloqueado = (
                Pedido.objects
                .select_for_update()
                .get(pk=pedido.pk)
            )

            if pedido_bloqueado.estado == 'pendiente':

                snapshot = pedido_bloqueado.items_snapshot

                if not isinstance(snapshot, list) or not snapshot:
                    raise ValueError(
                        'El pedido no contiene productos válidos.'
                    )

                for item in snapshot:

                    producto_id = int(item['producto_id'])
                    cantidad = int(item['cantidad'])

                    if producto_id <= 0 or cantidad <= 0:
                        raise ValueError(
                            'El producto o la cantidad no son válidos.'
                        )

                    filas = Producto.objects.filter(
                        pk=producto_id,
                        stock__gte=cantidad
                    ).update(
                        stock=F('stock') - cantidad
                    )

                    if filas == 0:
                        raise ValueError(
                            f'No hay stock suficiente del producto '
                            f'ID {producto_id}.'
                        )

                pedido_bloqueado.estado = 'pagado'

                pedido_bloqueado.save(
                    update_fields=['estado']
                )

                pedido_confirmado_ahora = True

            elif pedido_bloqueado.estado != 'pagado':
                raise ValueError(
                    'El pedido no está pendiente ni pagado.'
                )

        pedido.refresh_from_db()

    except Exception:
        logger.exception(
            'Error al confirmar pedido o actualizar inventario: %s.',
            pedido.numero_pedido
        )

        messages.error(
            request,
            'Stripe confirmó el pago, pero hubo un problema '
            'al actualizar el pedido o el inventario. '
            'No vuelvas a pagar; el pedido necesita revisión.'
        )

        return redirect('catalogo:pago_error')

    # --------------------------------------------------------
    # 3. LIMPIAR CARRITO Y REFERENCIA DE PAGO
    # --------------------------------------------------------

    _guardar_carrito(request, {})

    pagos.pop(str(pedido.pk), None)

    request.session['stripe_payment_intents'] = pagos
    request.session.modified = True

    # --------------------------------------------------------
    # 4. PROGRAMAR CORREO CON CELERY
    # --------------------------------------------------------

    if pedido_confirmado_ahora:
        try:
            enviar_confirmacion_pedido.delay(
                pedido.pk
            )

            logger.info(
                'Correo de confirmación programado para pedido %s.',
                pedido.numero_pedido
            )

        except Exception:
            logger.exception(
                'No se pudo programar el correo del pedido %s.',
                pedido.numero_pedido
            )

    # --------------------------------------------------------
    # 5. MOSTRAR CONFIRMACIÓN
    # --------------------------------------------------------

    messages.success(
        request,
        f'¡Pago exitoso! Tu pedido {pedido.numero_pedido} '
        'está confirmado. Recibirás un correo de confirmación pronto.'
    )

    return render(
        request,
        'catalogo/pago_exitoso.html',
        {
            'pedido': pedido,
        }
    )


# ============================================================
# ERROR DE PAGO
# ============================================================

def pago_error(request):
    """Muestra la página de error de pago."""

    return render(
        request,
        'catalogo/pago_error.html'
    )
