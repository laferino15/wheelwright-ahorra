# Portal de comercios de wheel-ahorra

Primera etapa implementada en la base local `wheelwright_ahorra_dev`.

## Cliente comprador

Puede seguir comprando sin cuenta o crear una cuenta de cliente. Desde Mi cuenta
consulta sus pedidos con las funciones nativas de Odoo. Tener un comercio no
impide comprar con esa misma cuenta.

## Comerciante

1. Abrir `/vender` y crear una cuenta o iniciar sesión.
2. En `/mi-comercio/registro`, completar local, rubro, dirección, teléfono,
   horarios, descripción y logo opcional.
3. Esperar la aprobación de la administración.
4. En `/mi-comercio`, agregar productos con presentación, precio final e imagen.
5. Guardar borrador y seleccionar **Enviar a revisión**.
6. Corregir las observaciones de la administración cuando corresponda.

Las imágenes admitidas son JPG, PNG y WebP, hasta 5 MB. Un producto necesita una
imagen antes de enviarse a revisión. Editar un producto aprobado lo retira de la
tienda y lo devuelve a borrador hasta una nueva revisión.

Se permite un local por cuenta y sitio en esta primera etapa. El dueño no puede
modificar el propietario del local ni asignar productos a otro local.

## Administración

Los usuarios con permiso nativo **Administrar productos** de Odoo, incluido el
administrador actual, acceden a la aplicación **wheel-ahorra**:

- **Comercios**: revisar datos, aprobar o solicitar cambios/suspender.
- **Productos para revisar**: revisar foto, categoría, presentación y precio;
  aprobar y publicar o solicitar cambios.

El campo **Observaciones de la administración** permite explicar qué corregir.
Suspender un local retira sus productos del catálogo. Reaprobar el local no
republica automáticamente sus productos: se requiere revisión de cada producto.

El comerciante indica el precio final; la aprobación calcula el precio base con
los impuestos configurados para conservar ese importe. El stock ofrecido para ventas web se ajusta desde Mis productos → Ajustar stock.
El control cuantitativo se explica en STOCK_DISPONIBILIDAD.md y no modifica
las existencias físicas del depósito de Odoo.

## Datos existentes y límites de esta etapa

El catálogo ilustrativo existente conserva su condición de prueba. No se
asignaron sus comercios a cuentas de personas sin identificar al dueño.

Las comisiones y liquidaciones todavía no están implementadas.

## Preparación y reparto

Al confirmar una compra web, el sistema genera una preparación por local. El
comerciante entra en **Mi comercio → Ver pedidos de mi local** y ve únicamente
sus productos, cantidades y subtotal, sin datos personales del comprador ni
productos de otros locales.

1. **Recibido → Iniciar preparación → En preparación**.
2. **Marcar listo para retirar → Listo para retirar**.
3. Administración entra en **wheel-ahorra → Preparaciones y reparto**, registra
   el retiro por el repartidor y, luego, la entrega.

El cliente consulta el estado conjunto desde **Mi cuenta → Pedidos**. Cuando
hay varios locales, el pedido pasa a listo cuando todos están listos; pasa a
entregado cuando todos fueron entregados. El vendedor puede dejar una
observación para quien coordina el retiro. La consulta requiere actualizar la
página; no hay notificaciones automáticas.

Registrar estos estados no registra cobros ni valida movimientos de inventario.
El cobro y los remitos se gestionan por sus circuitos habituales de Odoo. Una
cancelación del pedido cancela sus preparaciones pendientes. Los productos de
un pedido enviado a preparación no se pueden modificar: se debe cancelar y
crear otro pedido para conservar la coherencia con lo que recibió cada local.

Los comercios del catálogo de prueba sin dueño quedan visibles únicamente en
administración, con la advertencia **sin dueño asignado**. No se asignan a
cuentas arbitrarias. Los pedidos anteriores pueden generar sus preparaciones
desde la pestaña **Seguimiento de preparación** del pedido administrativo.

No hay avisos automáticos por WhatsApp. Las altas de cuentas usan el sistema
nativo de Odoo; el envío y la recepción de correos dependen de su configuración.

## Verificación realizada

- Aislamiento de locales y productos entre dos cuentas de portal.
- Rechazo de cambios de dueño y de autoaprobación/publicación directa.
- Registro web con datos de dueño forzados por el servidor.
- Carga de imagen y vista previa al editar.
- Envío a revisión con protección CSRF y bloqueo de URL ajenas.
- Aprobación y publicación en el comercio correcto.
- Conservación del precio final con los impuestos locales configurados.
- Retiro de la publicación después de editar o suspender el local.

Las pruebas usaron cuentas ficticias eliminadas al finalizar; no se enviaron
invitaciones ni se registraron cobros. Las pruebas de preparación confirmaron
pedidos ficticios que se eliminaron al finalizar, y comprobaron permisos,
CSRF, cancelación y seguimiento completo hasta la entrega.
