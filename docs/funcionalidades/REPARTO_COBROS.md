# Reparto y cobros de wheel-ahorra

Versión 19.0.2.7.0. Panel: **wheel-ahorra → Reparto y cobros**.

## Circuito operativo

1. Administración carga nombre y teléfono de cada repartidor en **Repartidores**.
   No crea una cuenta de acceso ni le concede permisos al repartidor.
2. Una compra confirmada aparece en el panel, agrupada por fecha y franja. Se
   elige un repartidor activo y se pulsa **Asignar repartidor**.
3. Cada local prepara sus productos y los marca listos. Administración registra
   cada retiro desde la pestaña **Retiros de locales**. No puede retirar lo que
   aún no está listo ni hacerlo sin repartidor asignado.
4. Con todos los locales retirados se habilita **Marcar En camino**. Se conserva
   una copia del destino e indicaciones al salir. No se permite cambiar destino,
   fecha, repartidor, productos o importes mientras el pedido está en reparto.
5. **Registrar entrega** marca entregadas todas sus preparaciones. No registra
   un cobro. El comprador ve En camino y Entregado en su cuenta.
6. **Registrar cobro** abre un asistente: importe completo, efectivo recibido y
   vuelto, o transferencia que administración haya verificado con su referencia.
   Se conserva número de registro, fecha, responsable y repartidor. El comprador
   ve Cobro registrado, sin acceso al registro interno ni datos del repartidor.

El filtro inicial **Por completar** incluye entregas pendientes y entregados
pendientes de cobro. Los filtros permiten consultar entregados, en camino,
repartidor, fecha y franja. Se mantiene el acceso desde cada preparación y desde
la pestaña Reparto y cobros del pedido de venta.

## Registros y controles

- El historial conserva quién asignó, retiró, despachó, entregó y registró/anuló
  el cobro. Los usuarios no pueden editar ni borrar eventos.
- El registro de cobro es inalterable. Una corrección requiere **Anular con
  motivo** y luego un nuevo registro. Anular un registro no devuelve dinero ni
  revierte transferencias; el original, motivo y responsable quedan guardados.
- No se registran importes parciales, importes diferentes al total ni efectivo
  insuficiente. Los importes se redondean a la moneda del pedido.
- No se puede registrar dos veces el mismo pedido ni iniciar otro pago asociado
  al pedido si ya existe un cobro del reparto. Se bloquean cobros manuales cuando
  existe un pago en Odoo o un pago electrónico en proceso que requiere revisión.
- Las acciones y el registro de cobro bloquean la fila de la orden. El guardado
  de líneas también usa ese bloqueo para impedir cambios simultáneos al salir.
- Solo administración del marketplace puede operar reparto y cobros. Los
  registros e historiales se limitan a las compañías habilitadas.
- Se puede cancelar antes del retiro: se devuelve stock según su control vigente
  y no queda cobro pendiente. Después de retirar o entregar se bloquea cancelar;
  primero se debe resolver la devolución física. No se repone mercadería que ya
  está con el repartidor como si siguiera en el local.

## Alcance

Es un **registro operativo de cobranza**. No modifica transacciones de pago
previas, no genera account.payment, no concilia bancos, no emite facturas y no
liquida dinero ni comisiones a comercios. Esos circuitos contables siguen
separados. La transferencia se registra solo después de verificarla; no hay
conexión automática con bancos ni pagos reales ejecutados por esta función.

Tampoco incorpora una cuenta de repartidor, geolocalización, optimización de
rutas, notificaciones, devoluciones parciales o reembolsos. El operador es la
administración. Los pedidos cancelados anteriores se reconocen sin inventar
repartidores, fechas de entrega ni cobros históricos.

## Verificación

`verificar_reparto.py`: dos locales, permisos reales de administrador/portal,
stock, retiros, salida, entrega separada del cobro, vuelto, duplicados,
anulación con motivo, privacidad, inalterabilidad del historial, bloqueo de
importes posteriores a la salida, cancelación anterior al retiro y bloqueo de
nuevos pagos después del cobro. Todas las transacciones se revierten.

`verificar_reparto_web.py`: vistas administrativas procesadas para el usuario
real de prueba, acciones RPC de administración, cliente consultando En camino,
Entregado y Cobro registrado, protección de registros y cobros duplicados. Los
fixtures se eliminan al terminar. No se enviaron correos ni se registraron
cobros reales o asientos contables.

La inspección visual con la sesión habitual de administrador queda pendiente:
el navegador integrado no tenía una sesión iniciada. Las vistas y las acciones
se verificaron mediante las mismas solicitudes que usa el cliente de Odoo.
