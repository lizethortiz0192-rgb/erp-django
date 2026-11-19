import logging

import stripe

from django.conf import settings
from django.db.models import F
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from productos.models import Producto
from ventas.models import Pedido
from ventas.tasks import enviar_confirmacion_pedido


# ── REGISTRO DE ERRORES ────────────────────────────────────────────────

logger = logging.getLogger(__name__)


# ── WEBHOOK DE STRIPE ──────────────────────────────────────────────────

@csrf_exempt
@require_POST
def stripe_webhook(request) -> HttpResponse:
    """Recibe y procesa eventos de Stripe."""

    payload = request.body

    sig_header = request.META.get(
        'HTTP_STRIPE_SIGNATURE',
        ''
    )

    # ── 1. Verificar firma ────────────────────────────────────────────

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )

    except ValueError:
        logger.warning(
            'Webhook: payload inválido recibido.'
        )

        return HttpResponse(
            'Payload inválido.',
            status=400
        )

    except stripe.error.SignatureVerificationError:
        logger.warning(
            'Webhook: firma inválida — posible ataque.'
        )

        return HttpResponse(
            'Firma inválida.',
            status=400
        )

    # ── 2. Despachar por tipo de evento ───────────────────────────────

    tipo = event['type']

    logger.info(
        'Webhook recibido: %s',
        tipo
    )

    if tipo == 'payment_intent.succeeded':

        _manejar_pago_exitoso(
            event['data']['object']
        )

    elif tipo == 'payment_intent.payment_failed':

        _manejar_pago_fallido(
            event['data']['object']
        )

    else:
        logger.debug(
            'Evento ignorado: %s',
            tipo
        )

    return HttpResponse(status=200)


# ── HANDLERS INTERNOS ──────────────────────────────────────────────────

def _manejar_pago_exitoso(payment_intent: dict) -> None:
    # ... (código existente) ...
    pedido_id = _extraer_pedido_id(payment_intent)
    if pedido_id is None:
        return

    try:
        pedido = Pedido.objects.get(pk=pedido_id)
    except Pedido.DoesNotExist:
        logger.error(f'Webhook: Pedido {pedido_id} no encontrado en BD.')
        return

    if pedido.estado != 'pagado':
        pedido.estado = 'pagado'
        pedido.save(update_fields=['estado'])
        logger.info(
            f'Pedido {pedido.numero_pedido} actualizado a "pagado".'
        )
        _descontar_stock(pedido)

        # ── NUEVO W16: disparar tarea de confirmación ─────────────────
        # El webhook es el lugar más confiable para disparar el correo:
        # se ejecuta incluso si el usuario cerró el navegador antes de
        # llegar a pago_exitoso().
        enviar_confirmacion_pedido.delay(pedido.pk)
        # ─────────────────────────────────────────────────────────────
    else:
        logger.info(
            f'Pedido {pedido.numero_pedido} ya estaba pagado — '
            f'idempotente, sin cambios.'
        )

def _manejar_pago_fallido(payment_intent: dict) -> None:
    """Procesa un pago fallido o rechazado."""

    pedido_id = _extraer_pedido_id(payment_intent)

    if pedido_id is None:
        return

    try:
        pedido = Pedido.objects.get(
            pk=pedido_id
        )

    except Pedido.DoesNotExist:
        logger.error(
            'Webhook: Pedido %s no encontrado.',
            pedido_id
        )
        return

    if pedido.estado == 'pendiente':

        pedido.estado = 'cancelado'

        pedido.save(
            update_fields=['estado']
        )

        logger.info(
            'Pedido %s cancelado por pago fallido.',
            pedido.numero_pedido
        )


# ── UTILIDADES ─────────────────────────────────────────────────────────

def _extraer_pedido_id(payment_intent: dict) -> int | None:
    """Extrae el pedido_id del metadata del PaymentIntent."""

    metadata = payment_intent.get(
        'metadata',
        {}
    )

    pedido_id = metadata.get('pedido_id')

    if not pedido_id:
        logger.warning(
            'Webhook: PaymentIntent sin pedido_id en metadata. '
            'ID de PaymentIntent: %s',
            payment_intent.get('id')
        )

        return None

    try:
        return int(pedido_id)

    except (ValueError, TypeError):
        logger.error(
            'Webhook: pedido_id inválido: %r',
            pedido_id
        )

        return None


def _descontar_stock(pedido: 'Pedido') -> None:
    """Descuenta el stock de los productos del pedido con expresiones F()."""

    items = pedido.items_snapshot or []

    for item in items:

        producto_id = item.get('producto_id')

        try:
            cantidad = int(
                item.get('cantidad', 0)
            )
        except (ValueError, TypeError):
            logger.warning(
                'Cantidad inválida en el pedido %s.',
                pedido.numero_pedido
            )
            continue

        if not producto_id or cantidad <= 0:
            continue

        filas_actualizadas = Producto.objects.filter(
            pk=producto_id,
            stock__gte=cantidad
        ).update(
            stock=F('stock') - cantidad
        )

        if filas_actualizadas:

            logger.info(
                'Stock decrementado: Producto %s - %s unidades.',
                producto_id,
                cantidad
            )

        else:

            logger.warning(
                'Producto %s: stock insuficiente para '
                'decrementar %s unidades.',
                producto_id,
                cantidad
            )
