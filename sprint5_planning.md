# Sprint 5 Planning — ERP Django
## Semanas W16–W18 · Espiral 6: Celery e Integraciones

**Sprint Goal:**
Al finalizar el Sprint 5, el ERP ejecutará tareas pesadas de forma
asíncrona con Celery+Redis: correos de confirmación, alertas de
stock bajo y reporte diario de ventas.

## Sprint Backlog — actualización W16

| Tarea | Estado |
|---|---|
| pip install celery redis flower | ✅ W16 |
| core/celery.py + core/__init__.py | ✅ W16 |
| CELERY_* en settings.py | ✅ W16 |
| docker-compose.yml con worker + flower | ✅ W16 |
| ventas/tasks.py (2 tareas placeholder) | ✅ W16 |
| pago_exitoso: .delay() al vaciar carrito | ✅ W16 |
| webhook: .delay() al confirmar pago | ✅ W16 |
| Worker corriendo + Flower en :5555 | ✅ W16 |
| SendGrid correo transaccional real | ⏳ W17 |
| Alerta de stock bajo por correo | ⏳ W17 |
| Celery Beat + tareas programadas | ⏳ W18 |

## DoD — Sprint 5
- celery -A core worker → procesa tareas sin error
- POST /catalogo/checkout/ → tarea de correo en la cola (no espera)
- Correo de confirmación recibido en < 30 s (W17)
- Alerta de stock enviada cuando stock < umbral (W17)
- Reporte diario ejecutado a las 8:00 AM (W18)
- python manage.py test → ≥ 155 tests OK
