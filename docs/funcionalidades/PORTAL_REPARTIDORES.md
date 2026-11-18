# Mi comercio y Mi reparto

Versión 19.0.3.1.0. Se conserva una compra completa con un repartidor, retiros por local y un único registro de cobro del total.

## Comercio

En Mi comercio → Pedidos de mi local → abrir preparación:

1. Comenzar preparación y marcar Listo para retirar.
2. Solicitar retiro. La fecha y el responsable quedan registrados, y coordinación puede filtrar **Retiro solicitado** en Preparaciones y reparto.
3. Cuando el repartidor asignado recibe los productos, pulsar Confirmar entrega al repartidor.

El comercio ve únicamente su preparación y el nombre/teléfono del repartidor asignado. No puede entregar la compra completa ni registrar su cobro.

## Repartidor

Ingresar con la cuenta vinculada al repartidor y abrir `/mi-reparto` (también aparece en Mi cuenta).

1. Aceptar el recorrido asignado.
2. Registrar el retiro de cada local cuando corresponda. Si el comercio ya confirmó la entrega al repartidor, se muestra como retirado y no se duplica.
3. Marcar En camino cuando estén retirados todos los locales.
4. Registrar la entrega completa al cliente.
5. Registrar el cobro en efectivo o una transferencia verificada, por el total de productos y envío. El sistema calcula el vuelto y conserva número de registro, fecha y responsable.

Los entregados sin cobrar siguen en **En curso y por cobrar**. Un recorrido iniciado desde administración puede aceptarse desde su estado actual para continuar sus tareas pendientes.

## Coordinación

Una vez por persona: Administración → Repartidores → Cuenta para Mi reparto, seleccionar su cuenta de wheel-ahorra.

Por pedido: asignar el repartidor. La asignación sigue siendo manual en esta versión; el portal no selecciona ni reasigna recorridos automáticamente. Administración conserva el panel de supervisión y las acciones existentes.

## Permisos y controles

- No se otorgan permisos generales sobre pedidos, cobros ni repartidores a las cuentas de reparto.
- Los controladores filtran por cuenta vinculada, repartidor activo, sitio, compañía y pedido confirmado. Solo entregan al portal los datos necesarios del recorrido.
- Las acciones privadas vuelven a comprobar la asignación dentro de un bloqueo de pedido. Se valida nuevamente la vinculación con el repartidor antes de registrar movimientos.
- Cambiar el repartidor revoca el acceso anterior y reinicia la aceptación.
- Comercio y repartidor no pueden operar pedidos ajenos.
- Todos los cambios se envían por POST con CSRF nativo. Los totales se toman del servidor.
- La salida requiere todos los retiros; la entrega y el cobro son pasos distintos; cobros duplicados bloqueados. La anulación de cobros queda en administración.
- No se envían avisos externos ni se realizan transferencias bancarias desde estas pantallas.

## Verificación

`verificar_portal_reparto.py`: dos locales, solicitud idempotente, entrega desde comercio, retiro desde repartidor, salida bloqueada si falta un local, entrega total, cobro único con vuelto, responsable real, permisos, desactivación y cambio de repartidor. También renderiza los formularios con permisos de portal. Los datos ficticios se revierten.

Prueba HTTP con una cuenta vinculada: ingreso y recorrido asignado HTTP 200; acceso no autorizado 404; POST sin CSRF rechazado con 400. Sin avanzar entregas ni cobros de pedidos existentes.
