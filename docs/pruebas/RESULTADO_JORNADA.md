# Resultado de la jornada de pruebas

Resultado: APROBADA

HTTP y RPC locales, postproceso COD nativo con notificaciones suprimidas y prueba de confirmaciones concurrentes. Sin dinero, correos o entregas reales.

Duración: 45.84 segundos.

| Comprobación | Resultado |
|---|---|
| Registro y aprobación de 3 locales; 6 productos con imagen, precio y stock publicados | PASS |
| Compra nativa: carrito, dirección, franjas y confirmación Efectivo al recibir en 4 pedidos | PASS |
| Cancelación antes del retiro: devuelve stock y no deja cobro pendiente | PASS |
| Preparación por cada dueño, retiros, reparto y entrega de pedidos con varios locales | PASS |
| Cobros en efectivo con vuelto y transferencia verificada; segundo cobro bloqueado | PASS |
| Corrección de cobro: original anulado con motivo y nuevo registro, sin borrar historial | PASS |
| Aislamiento entre locales y bloqueo de reparto/cobros para clientes | PASS |
| Última unidad: una sola compra confirmada; stock final exacto y producto agotado | PASS |
| Conciliación de la jornada: 4 entregados, 3 cobrados, 1 sin cobrar, 1 cancelado y 1 bloqueado | PASS |
| Sin facturas, pagos contables ni correos generados por los pedidos de prueba | PASS |
| Limpieza completa y datos de negocio preexistentes conservados | PASS |

| Escenario | Pedido ficticio | Franja |
|---|---|---|
| Mediodía | S00041 | midday |
| Tarde | S00042 | afternoon |
| Noche | S00043 | night |
| Cancelación | S00044 | midday |
| Última unidad ganadora | S00045 | night |
| Última unidad perdedora | S00046 | night |
