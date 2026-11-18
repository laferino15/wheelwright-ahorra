# Stock y disponibilidad de wheel-ahorra

Versión 19.0.2.4.0, instalada en la base local wheelwright_ahorra_dev.

## Cómo usarlo

Desde **Mi comercio → Mis productos → Ajustar stock** el dueño puede:

- Activar **Controlar la cantidad disponible** e ingresar cuántas presentaciones
  puede vender: 10 bandejas de 500 g son 10, no 5.000.
- Mantener **Habilitado para vender** o pausarlo temporalmente.
- Reponer la cantidad disponible sin cambiar la aprobación ni el precio.

Con control activo y cantidad 0 se muestra **Agotado** en el catálogo y la
ficha, y se deshabilita su botón principal de compra. El servidor también limita
las cantidades del carrito y vuelve a validarlas antes del pago y al confirmar.

Los productos existentes conservan el control de cantidad desactivado hasta
que el dueño registre existencias. No se inventaron cantidades. El formulario
de nuevos productos propone activar el control, con cantidad inicial 0.

Administración consulta estas cantidades desde **wheel-ahorra → Productos para
revisar**, en la lista o ficha del producto del comerciante.

## Descuento y cancelaciones

Agregar al carrito no reserva unidades. Se descuentan al confirmar el pedido
web. Las confirmaciones y ajustes bloquean la fila de stock en la base de datos
para evitar vender la misma última unidad dos veces. Se suman todas las líneas
del mismo producto y se respetan las conversiones de unidades de Odoo.

Cancelar devuelve una sola vez las unidades reservadas que aún no se entregaron,
si continúa activo el control de cantidad. No se repone automáticamente lo ya
entregado; requiere revisar la devolución. Con el control desactivado, la venta
no impone límite cuantitativo. Al reactivarlo debe ingresarse la disponibilidad
actual para nuevos pedidos.

Este es el stock ofrecido por el comercio para ventas en wheel-ahorra. No crea
inventarios físicos, ajustes de almacén ni movimientos de depósito en Odoo.
Los productos ilustrativos sin dueño registrado conservan su comportamiento.

## Verificación

- `verificar_stock.py`: dueño y permisos, cantidades negativas/no finitas,
  pausa/reactivación, agotados, límites del carrito, pedidos de varios locales y
  líneas duplicadas, descuento único y devolución única al cancelar, entregados
  y modo sin límite. Todas sus transacciones se revierten.
- `verificar_stock_web.py`: formulario HTTP, protección CSRF y aislamiento,
  ficha agotada con CTA deshabilitado, carrito nativo y dos confirmaciones
  concurrentes por la última unidad. Solo una se confirma. Los datos de prueba
  se eliminan al finalizar; sin correos ni cobros.

Código: `models/stock.py`, `views/stock.xml` y las rutas del controlador de
comercios. Los cambios de disponibilidad usan la misma aprobación existente;
editar el resto del producto conserva su circuito de revisión.
