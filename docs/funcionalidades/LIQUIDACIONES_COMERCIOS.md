# Liquidaciones a comercios

Versión del módulo: 19.0.2.8.0.

## Uso

1. Administración → wheel-ahorra → Comercios: configurar **Comisión de la plataforma (%)**. Todos los comercios existentes y nuevos empiezan en 0 %.
2. Abrir **Liquidaciones a comercios** y crear un borrador con comercio y período.
3. **Generar detalle**: incluye exclusivamente preparaciones entregadas de pedidos confirmados, entregados y completamente cobrados, todavía no reservadas en otra liquidación.
4. Revisar productos, comisión y neto; luego **Confirmar liquidación**.
5. Realizar el pago por el canal habitual. Cargar medio y referencia o recibo, y pulsar **Registrar pago realizado**.

El período usa la fecha de entrega elegida en el pedido (`wah_delivery_date`), inclusive. Se consideran únicamente pedidos en la moneda de la compañía. Los locales sin un comercio registrado asociado no se incluyen automáticamente.

## Importes

Base: subtotal con impuestos de los productos del local. El envío no se reparte al comercio. Comisión: base × porcentaje del comercio, redondeada en la moneda de la compañía por preparación. Neto: base menos comisión.

Ejemplo: productos $1.000 y comisión 10 % → comisión $100 y pago al local $900. El envío se mantiene separado.

El porcentaje se toma al generar el detalle y queda guardado allí. Cambiar la configuración del comercio no modifica liquidaciones ya generadas. Para recalcular una liquidación sin pagar, anularla con motivo y crear una nueva.

## Controles

- Una preparación puede estar reservada por una sola liquidación activa; bloqueo de generación simultánea por comercio, bloqueo de pedidos y restricción única en base de datos.
- Generar detalle reserva los pedidos también mientras el documento es borrador.
- Confirmación y pago vuelven a verificar que los pedidos estén entregados y cobrados.
- No se permite modificar el detalle, pagar dos veces ni eliminar el historial.
- Las liquidaciones sin pagar se anulan con motivo, fecha y responsable. Su detalle se conserva y sus pedidos se liberan.
- Una liquidación pagada no se puede anular en este circuito. Las devoluciones posteriores requieren un circuito separado todavía pendiente.
- No se puede anular el cobro de un pedido mientras respalde liquidaciones activas. Primero deben anularse todas las liquidaciones sin pagar de ese pedido.
- Acceso reservado a administración con permisos de productos y a compañías habilitadas. Los comerciantes y compradores no pueden leer ni modificar liquidaciones.

## Alcance y verificación

Registro operativo: no transfiere dinero ni genera facturas, pagos contables, retenciones o conciliaciones bancarias.

Pruebas en `verificar_liquidaciones.py`: comisión inicial cero y comisión distinta por local, exclusión de envío y pedidos sin entrega/cobro, filtro por período, duplicados, protección de importes, confirmación, referencia obligatoria, pago único, permisos, anulación con historial, cambio de comisión sin alterar documentos anteriores y corrección del cobro tras liberar una liquidación.

Los datos de prueba se revierten al finalizar. No se envían correos ni se realizan pagos reales.
