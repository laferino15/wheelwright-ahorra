# Portal propio de comercios

Versión 19.0.3.3.0. Acceso: http://127.0.0.1:8070/mi-comercio

El portal tiene encabezado propio, menú de cuenta y navegación permanente entre Resumen, Productos, Stock y Pedidos. Las cuentas con comercio registrado ingresan desde Mi cuenta directamente a este portal. Si una cuenta también es repartidor, se conserva el ingreso inicial a Mi reparto y ambos espacios siguen accesibles.

- Resumen: cantidad de productos, productos con control de cantidad agotados, preparaciones en curso y últimos cinco pedidos pendientes.
- Productos: precio, presentación, aprobación, disponibilidad, stock y acciones para agregar, editar o enviar a revisión.
- Stock: cantidad restante por presentación y ajuste de cantidad o pausa de venta con los controles existentes. Sin control de cantidad se muestra ese estado expresamente. La actualización de stock conserva la aprobación.
- Pedidos: filtros de preparaciones en curso y finalizadas, detalle de los productos del local, preparación, aviso de listo y retiro por el repartidor.

La interfaz no añade ACLs ni permite acceder a productos o preparaciones de otro dueño. Los formularios POST mantienen CSRF y validación de propiedad. El stock sigue descontándose al confirmar una compra según la lógica existente.

Verificación: carga y edición HTTP con dos comercios ficticios, envío a revisión, aprobación, ajuste de stock, conservación del estado aprobado, bloqueo HTTP de stock ajeno y CSRF. Verificación transaccional de preparación, retiro, entrega y cobro. Revisión visual de Resumen, Stock y Pedidos y revisión móvil a 390 px sin desbordamiento horizontal. Datos ficticios eliminados; pruebas de operaciones revertidas. Captura portal-comercio.jpg muestra un comercio ficticio de revisión que ya fue eliminado.
