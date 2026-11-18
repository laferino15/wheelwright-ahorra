# Casos de uso de wheel ahorra

Versión 19.0.3.1.0 · 17 de noviembre de 2026

Catálogo funcional con 60 casos. Una compra unificada, preparaciones por comercio, un repartidor para la entrega y el cobro completo. La asignación inicial sigue en coordinación.

## Roles

| Rol | Responsabilidad |
|---|---|
| Cliente | Comprar y consultar sus pedidos |
| Comercio | Preparar, solicitar retiro y entregar sus productos al repartidor |
| Repartidor | Aceptar, retirar, entregar y cobrar la compra completa |
| Administración | Revisar, asignar, supervisar, corregir y liquidar |

## Acceso y cuenta

### A01 Crear una cuenta

**Actor:** Visitante. **Estado:** Disponible.

**Condición inicial:** El registro del sitio está habilitado.

**Recorrido:** Abrir Crear cuenta; completar nombre, correo y contraseña; repetir la contraseña y enviar el formulario.

**Resultado:** Se crea una cuenta y se continúa hacia el destino solicitado. La cuenta puede comprar y solicitar el alta de un comercio.

**Alternativas y controles:** Corregir datos faltantes, correo ya registrado o contraseñas diferentes. Crear la cuenta no aprueba automáticamente un comercio.

### A02 Iniciar sesión

**Actor:** Usuario registrado. **Estado:** Disponible.

**Condición inicial:** La cuenta existe y está activa.

**Recorrido:** Abrir Ingresar; escribir correo y contraseña; confirmar; acceder a Mi cuenta y al panel habilitado para su rol.

**Resultado:** La sesión queda autenticada. Se conserva el destino de acceso cuando corresponde.

**Alternativas y controles:** Credenciales incorrectas no permiten entrar. Si el formulario pertenece a una sesión anterior, abrirlo de nuevo antes de enviarlo.

### A03 Cerrar sesión y cambiar de cuenta

**Actor:** Usuario autenticado. **Estado:** Disponible.

**Condición inicial:** Existe una sesión abierta.

**Recorrido:** Abrir Mi cuenta; seleccionar Cerrar sesión; abrir un formulario nuevo para ingresar con otra cuenta.

**Resultado:** La siguiente sesión utiliza los permisos de la cuenta elegida.

**Alternativas y controles:** Las pestañas abiertas pueden conservar formularios de la sesión anterior. Recargarlas antes de enviar cambios.

### A04 Recuperar o cambiar la contraseña

**Actor:** Usuario registrado y soporte autorizado. **Estado:** Condicionado por configuración.

**Condición inicial:** Para cambiarla, se conoce la clave actual; para recuperarla por correo, Odoo tiene configurado el envío.

**Recorrido:** Usar Cambiar contraseña desde las preferencias o la opción de recuperación de la pantalla de ingreso; seguir las instrucciones correspondientes.

**Resultado:** Se actualiza el acceso mediante el mecanismo nativo. Soporte puede intervenir en la instalación local cuando se autorice.

**Alternativas y controles:** La recepción del correo depende de la configuración. Una solicitud de recuperación no acredita la identidad ni autoriza a soporte a cambiar cualquier cuenta.

### A05 Acceder al panel correspondiente

**Actor:** Cliente, comerciante, repartidor o administrador. **Estado:** Disponible.

**Condición inicial:** La sesión y las vinculaciones de cuenta están configuradas.

**Recorrido:** Entrar a Mi cuenta; abrir Mis compras, Mi comercio o Mi reparto según corresponda; usar administración solo con los permisos habilitados.

**Resultado:** Cada persona encuentra sus tareas y los datos que le corresponden. Una cuenta de comercio también puede comprar.

**Alternativas y controles:** Tener una cuenta no la convierte en repartidor ni en dueño de un comercio. La administración debe establecer la vinculación correcta.

## Compra del cliente

### C01 Explorar y buscar productos

**Actor:** Visitante o cliente. **Estado:** Disponible.

**Condición inicial:** Existen productos publicados para el sitio.

**Recorrido:** Entrar a Inicio o Tienda; navegar categorías o escribir una búsqueda; revisar los resultados y abrir un producto.

**Resultado:** Se muestran productos disponibles del catálogo público con su precio y comercio cuando está asociado.

**Alternativas y controles:** Una búsqueda puede no tener resultados. Las categorías duplicadas deben corregirse mediante mantenimiento conservando las asociaciones de productos.

### C02 Consultar la ficha de un producto

**Actor:** Visitante o cliente. **Estado:** Disponible.

**Condición inicial:** El producto está publicado y es accesible en el sitio.

**Recorrido:** Abrir la ficha; revisar presentación, imagen, precio, comercio y disponibilidad; elegir la cantidad permitida.

**Resultado:** El cliente conoce qué está comprando y puede continuar al carrito cuando el producto se puede vender.

**Alternativas y controles:** Los productos ilustrativos se identifican como precios de prueba. Un producto agotado o pausado no debe poder confirmarse aunque exista un enlace anterior.

### C03 Encontrar una promoción vigente

**Actor:** Visitante o cliente. **Estado:** Disponible.

**Condición inicial:** Hay una oferta publicada cuya regla de precios aplica al visitante.

**Recorrido:** Abrir Ofertas desde el menú o el banner de Inicio; comparar precio anterior, precio actual, descuento y ahorro; abrir Ver oferta.

**Resultado:** La promoción mostrada utiliza la regla de precios que también aplicará al pedido. La portada destaca hasta cuatro ofertas.

**Alternativas y controles:** No se muestran promociones futuras, vencidas, agotadas o que otra regla de precios haya desplazado. Sin ofertas se presenta un aviso, sin descuentos inventados.

### C04 Armar y modificar el carrito

**Actor:** Visitante o cliente. **Estado:** Disponible.

**Condición inicial:** Los productos se pueden vender.

**Recorrido:** Agregar productos; ajustar cantidades o quitar líneas; revisar subtotales, envío y total antes de continuar.

**Resultado:** El carrito representa la intención de compra y vuelve a validar las cantidades. Todavía no reserva stock.

**Alternativas y controles:** Otra compra puede agotar unidades antes de confirmar. Los precios de un carrito no confirmado pueden actualizarse según las condiciones vigentes.

### C05 Comprar productos de varios locales

**Actor:** Visitante o cliente. **Estado:** Disponible.

**Condición inicial:** Los productos pertenecen al sitio y pueden comprarse.

**Recorrido:** Agregar productos de diferentes comercios a un mismo carrito; completar la compra; revisar una confirmación y un total consolidados.

**Resultado:** Se conserva un pedido del cliente y se genera una preparación por local. Un repartidor entrega y cobra la compra completa.

**Alternativas y controles:** Los productos sin comercio registrado requieren intervención de coordinación. El cliente no debe realizar cobros separados por cada preparación.

### C06 Completar la dirección y las indicaciones

**Actor:** Visitante o cliente. **Estado:** Disponible.

**Condición inicial:** El carrito tiene productos y se inició el checkout.

**Recorrido:** Completar datos de contacto y domicilio; agregar indicaciones para la entrega; revisar la información y continuar.

**Resultado:** Los datos quedan en el pedido para la entrega. El checkout local utiliza Wheelwright, Santa Fe, código postal 2722 y Argentina.

**Alternativas y controles:** Corregir campos inválidos. Las indicaciones admiten hasta 1000 caracteres. No se implementó selección de zonas de entrega para otras ciudades.

### C07 Elegir una fecha y franja de entrega

**Actor:** Visitante o cliente. **Estado:** Disponible.

**Condición inicial:** El pedido requiere entrega con franjas y todavía no está confirmado.

**Recorrido:** Abrir la selección de entrega; elegir fecha; consultar horarios; seleccionar una franja disponible; guardar y continuar al pago.

**Resultado:** La fecha y franja se conservan en el pedido y se muestran al cliente, al comercio y en coordinación.

**Alternativas y controles:** No se aceptan franjas ya iniciadas. Si la franja vence durante el checkout, debe elegirse otra. No existen cupos ni cortes anticipados configurados en este circuito.

### C08 Confirmar una compra con efectivo al recibir

**Actor:** Visitante o cliente. **Estado:** Disponible.

**Condición inicial:** Dirección y franja válidas; stock disponible; proveedor Efectivo al recibir habilitado.

**Recorrido:** Revisar el total; elegir Efectivo al recibir; confirmar; esperar el resultado del postproceso de la compra.

**Resultado:** El pedido pasa a confirmado, se reserva el stock controlado y se crean las preparaciones. El cobro queda pendiente hasta que se registre la recepción del dinero.

**Alternativas y controles:** Una validación fallida puede dejar la compra sin confirmar. Una transacción pendiente de efectivo no significa que la compra esté pagada.

### C09 Consultar el seguimiento de una compra

**Actor:** Cliente autenticado o comprador con acceso válido a su pedido. **Estado:** Disponible.

**Condición inicial:** La compra corresponde al cliente y existe acceso autorizado.

**Recorrido:** Abrir Mis compras o el acceso de confirmación; consultar productos, franja, preparación, reparto y situación del cobro.

**Resultado:** El cliente conoce el avance conjunto de su pedido. En camino y Entregado son estados distintos del cobro registrado.

**Alternativas y controles:** Un cliente no puede consultar pedidos ajenos. La página debe actualizarse para ver novedades; no hay seguimiento GPS ni avisos automáticos por WhatsApp.

### C10 Indicar efectivo y datos de facturación

**Actor:** Visitante o cliente. **Estado:** Disponible.

**Condición inicial:** Se está completando la información del checkout local.

**Recorrido:** Si se necesita vuelto, indicar con cuánto se pagará; si corresponde, solicitar factura con datos específicos y completar los campos requeridos.

**Resultado:** El pedido conserva el efectivo indicado y la solicitud de datos de factura. El repartidor puede consultar la referencia de efectivo para preparar cambio.

**Alternativas y controles:** El importe indicado debe ser finito, no negativo y alcanzar el total cuando se completa. Solicitar datos de factura no emite automáticamente una factura.

## Gestión del comercio

### M01 Registrar un comercio

**Actor:** Usuario autenticado. **Estado:** Disponible.

**Condición inicial:** La cuenta todavía no tiene un local en ese sitio.

**Recorrido:** Entrar a Quiero vender o Mi comercio; completar nombre, rubro, dirección y teléfono; agregar horarios, descripción y logo si corresponde; enviar.

**Resultado:** El comercio queda pendiente de aprobación y vinculado a la cuenta que lo registró.

**Alternativas y controles:** Se admite un local por cuenta y sitio. El dueño no puede asignarse otro propietario ni aprobar su propia solicitud.

### M02 Corregir una solicitud de comercio

**Actor:** Dueño del comercio. **Estado:** Disponible.

**Condición inicial:** Administración solicitó cambios o dejó observaciones.

**Recorrido:** Entrar a Mi comercio; leer las observaciones; corregir los datos del local y guardar para una nueva revisión.

**Resultado:** La solicitud vuelve al circuito de aprobación con la información corregida.

**Alternativas y controles:** Cambiar los datos no implica aprobación inmediata. La administración debe revisar la solicitud nuevamente.

### M03 Actualizar los datos de un local

**Actor:** Dueño del comercio. **Estado:** Disponible.

**Condición inicial:** El comercio pertenece a la cuenta autenticada.

**Recorrido:** Editar datos públicos del local; guardar; revisar el estado de la solicitud.

**Resultado:** Los cambios quedan guardados y el local vuelve a revisión según el circuito vigente.

**Alternativas y controles:** El dueño no puede cambiar el propietario, el sitio ni el estado de aprobación mediante el formulario. Los efectos sobre publicaciones deben revisarse con administración.

### M04 Crear un producto en borrador

**Actor:** Dueño de un comercio aprobado. **Estado:** Disponible.

**Condición inicial:** El comercio está habilitado para gestionar ofertas de productos.

**Recorrido:** Entrar a Mis productos; agregar nombre, presentación, categoría, precio final, descripción e imagen; guardar como borrador.

**Resultado:** El producto queda preparado para revisión y todavía no está publicado.

**Alternativas y controles:** El precio debe ser positivo y válido. Las imágenes admiten JPG, PNG o WebP, hasta 5 MB; se requiere una imagen para enviarlo a revisión.

### M05 Enviar un producto a revisión

**Actor:** Dueño del comercio. **Estado:** Disponible.

**Condición inicial:** El producto propio está en borrador o requiere correcciones y tiene imagen.

**Recorrido:** Revisar sus datos; usar Enviar a revisión; esperar la evaluación de administración.

**Resultado:** La propuesta queda pendiente. Al aprobarse se vincula con un producto del catálogo público.

**Alternativas y controles:** No se pueden aprobar productos propios. Si faltan datos o imagen, se rechaza el envío y se informa qué corregir.

### M06 Editar un producto publicado

**Actor:** Dueño del comercio. **Estado:** Disponible.

**Condición inicial:** El producto pertenece al local.

**Recorrido:** Abrir el producto; modificar precio, descripción, presentación u otros datos comerciales; guardar; reenviar a revisión.

**Resultado:** La edición vuelve a borrador y retira la versión publicada hasta una nueva aprobación.

**Alternativas y controles:** No confundir edición comercial con ajuste de stock. El ajuste de stock y disponibilidad tiene un circuito propio que conserva la aprobación.

### M07 Configurar y reponer el stock ofrecido

**Actor:** Dueño de un comercio aprobado. **Estado:** Disponible.

**Condición inicial:** Existe un producto propio asociado al catálogo.

**Recorrido:** Abrir Ajustar stock; activar el control de cantidad si se desea; ingresar presentaciones disponibles; guardar una reposición o corrección.

**Resultado:** La tienda aplica el límite a las ventas futuras. Con cantidad cero se muestra Agotado cuando el control está activo.

**Alternativas y controles:** No se aceptan cantidades negativas ni no finitas. Se cuentan presentaciones comerciales, no gramos sueltos. Este stock no equivale al inventario físico de depósito de Odoo.

### M08 Pausar o reactivar la venta de un producto

**Actor:** Dueño de un comercio aprobado. **Estado:** Disponible.

**Condición inicial:** El producto pertenece al local.

**Recorrido:** Entrar a Ajustar stock; cambiar Habilitado para vender; guardar; verificar la disponibilidad pública.

**Resultado:** El producto deja de poder venderse o vuelve a publicarse según aprobación, disponibilidad y stock.

**Alternativas y controles:** Desactivar el control cuantitativo elimina ese límite. Al volver a activarlo, el comercio debe informar la cantidad real disponible; el sistema no la inventa.

### M09 Consultar los pedidos del local

**Actor:** Dueño del comercio. **Estado:** Disponible.

**Condición inicial:** Hay compras confirmadas que incluyen productos vinculados a ese local.

**Recorrido:** Entrar a Mi comercio y Pedidos de mi local; filtrar En curso, Finalizados o Todos; abrir Gestionar pedido.

**Resultado:** Se ven los productos, cantidades, subtotal y franja propios. El dueño no accede al pedido completo ni a datos de otros locales.

**Alternativas y controles:** Un carrito en borrador no aparece como preparación. Si falta un pedido, revisar confirmación, asociación del producto y cuenta propietaria del comercio.

### M10 Preparar los productos de un pedido

**Actor:** Dueño del comercio. **Estado:** Disponible.

**Condición inicial:** La preparación propia está en Recibido.

**Recorrido:** Usar Comenzar preparación; preparar las cantidades solicitadas; guardar una observación si hace falta; marcar Listo para retirar al terminar.

**Resultado:** La preparación pasa de Recibido a En preparación y luego a Listo para retirar, conservando sus marcas de tiempo.

**Alternativas y controles:** No se puede preparar un pedido cancelado ni alterar los productos ya enviados a preparación. Una observación informa el problema, pero no realiza una sustitución ni devolución.

### M11 Solicitar el retiro

**Actor:** Dueño del comercio. **Estado:** Disponible.

**Condición inicial:** La preparación está Lista para retirar.

**Recorrido:** Abrir el pedido en Mi comercio; pulsar Solicitar retiro; consultar el repartidor asignado cuando exista.

**Resultado:** Se registran fecha y responsable. Coordinación puede filtrar los retiros solicitados y el repartidor ve la solicitud en su recorrido.

**Alternativas y controles:** Repetir la solicitud no duplica el movimiento. Si no hay repartidor asignado, la solicitud queda registrada y la asignación sigue a cargo de coordinación.

### M12 Confirmar la entrega al repartidor

**Actor:** Dueño del comercio. **Estado:** Disponible.

**Condición inicial:** El retiro fue solicitado y hay un repartidor activo asignado al pedido.

**Recorrido:** Verificar físicamente la entrega de los productos; pulsar Confirmar entrega al repartidor desde la preparación propia.

**Resultado:** Ese local queda Retirado por el repartidor y se registra quién confirmó el movimiento.

**Alternativas y controles:** No confirma la entrega al cliente ni el cobro. Si el repartidor ya registró ese retiro, no debe duplicarse. Los demás locales conservan su propio estado.

## Operación del repartidor

### R01 Consultar los recorridos asignados

**Actor:** Repartidor autenticado. **Estado:** Disponible.

**Condición inicial:** Su cuenta está vinculada a un repartidor activo.

**Recorrido:** Entrar a Mi reparto; revisar En curso y por cobrar, Completados o Todos; abrir un recorrido asignado.

**Resultado:** Solo aparecen pedidos confirmados de ese repartidor en el sitio correspondiente. Los entregados sin cobrar siguen en curso.

**Alternativas y controles:** Una cuenta sin vinculación no ve recorridos. No se conceden permisos generales de venta, cobros ni acceso al listado de repartidores.

### R02 Aceptar un recorrido

**Actor:** Repartidor asignado. **Estado:** Disponible.

**Condición inicial:** El pedido tiene tareas pendientes y está asignado a su cuenta activa.

**Recorrido:** Revisar el pedido y usar Aceptar recorrido; continuar desde el estado actual.

**Resultado:** Se guarda la aceptación y el responsable. Puede continuar un recorrido iniciado desde administración si aún tiene tareas pendientes.

**Alternativas y controles:** No se acepta un pedido ajeno, cancelado o completamente terminado. Cambiar de repartidor reinicia la aceptación y revoca el acceso anterior.

### R03 Consultar retiros y destino

**Actor:** Repartidor asignado. **Estado:** Disponible.

**Condición inicial:** Tiene acceso al recorrido.

**Recorrido:** Abrir su detalle; revisar dirección y teléfono del cliente, indicaciones y franja; consultar los locales, direcciones, productos y observaciones de retiro.

**Resultado:** Dispone de los datos necesarios para retirar y entregar la compra completa, incluido el total a cobrar.

**Alternativas y controles:** No se muestran comisiones, liquidaciones ni datos de pedidos ajenos. Un local sin dirección o dueño registrado requiere coordinación manual.

### R04 Registrar el retiro de un local

**Actor:** Repartidor que aceptó el recorrido. **Estado:** Disponible.

**Condición inicial:** El pedido sigue asignado y los productos de ese local están Listos para retirar.

**Recorrido:** Recibir físicamente los productos; pulsar Registrar retiro de este local; repetir el proceso en los demás locales.

**Resultado:** La preparación queda Retirada y el historial identifica al repartidor que registró el movimiento.

**Alternativas y controles:** No se puede retirar una preparación de otro pedido ni una que no esté lista. Si el comercio ya confirmó la entrega al repartidor, el movimiento no se duplica.

### R05 Marcar el pedido en camino

**Actor:** Repartidor que aceptó el recorrido. **Estado:** Disponible.

**Condición inicial:** Todos los locales del pedido tienen registrado el retiro.

**Recorrido:** Revisar los retiros; pulsar Marcar En camino; iniciar la entrega al cliente.

**Resultado:** El pedido completo pasa a En camino y se conserva la información de destino al salir a reparto.

**Alternativas y controles:** Si falta retirar un local, la salida se bloquea. Después de salir se restringen cambios de repartidor, destino, horario e importes.

### R06 Registrar la entrega completa

**Actor:** Repartidor asignado. **Estado:** Disponible.

**Condición inicial:** El pedido está En camino y el cliente recibe la compra completa.

**Recorrido:** Verificar la entrega; pulsar Registrar entrega completa.

**Resultado:** El pedido y sus preparaciones pasan a Entregado. Se guarda fecha y responsable.

**Alternativas y controles:** Entregar no registra el dinero recibido. Una entrega parcial, un rechazo o un faltante posterior al retiro requieren intervención: no hay circuito completo de devolución parcial.

### R07 Registrar el cobro en efectivo

**Actor:** Repartidor asignado. **Estado:** Disponible.

**Condición inicial:** La entrega está registrada y el pedido tiene importe pendiente de cobro.

**Recorrido:** Elegir Efectivo recibido; ingresar el efectivo entregado por el cliente; confirmar el cobro del total de productos y envío.

**Resultado:** Se registra un único cobro, su responsable, el efectivo recibido y el vuelto. El importe del pedido se toma del servidor.

**Alternativas y controles:** El efectivo debe alcanzar el total. Se bloquean cobros duplicados y conflictos con pagos registrados. Registrar el cobro no genera un pago contable.

### R08 Registrar una transferencia verificada

**Actor:** Repartidor asignado. **Estado:** Disponible.

**Condición inicial:** La compra está entregada y se verificó la recepción de la transferencia.

**Recorrido:** Elegir Transferencia verificada; completar la referencia o comprobante; confirmar el registro del total.

**Resultado:** El cobro operativo queda registrado con medio, referencia, fecha y responsable.

**Alternativas y controles:** La referencia es obligatoria. El formulario no verifica el banco, no realiza transferencias y no sustituye una conciliación bancaria. No registrar una transferencia solo por recibir una imagen.

## Administración y coordinación

### G01 Aprobar el alta de un comercio

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** Existe una solicitud pendiente con datos verificables.

**Recorrido:** Abrir Comercios; revisar propietario, rubro, dirección y contacto; aprobar la solicitud.

**Resultado:** El comercio queda aprobado y se vincula con su ficha de comercio en catálogo.

**Alternativas y controles:** Aprobar el comercio no aprueba automáticamente todos sus productos. La propiedad de la cuenta debe verificarse antes de dar acceso a pedidos.

### G02 Solicitar cambios o suspender un local

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** Existe una solicitud o un comercio que requiere revisión.

**Recorrido:** Revisar el caso; escribir observaciones; usar la acción de solicitar cambios o revisión del comercio.

**Resultado:** El local queda en revisión y sus productos pueden ser retirados del catálogo según la acción aplicada.

**Alternativas y controles:** Reaprobar el local no republica automáticamente sus productos. Las compras ya confirmadas requieren seguimiento operativo para resolver sus compromisos.

### G03 Aprobar y publicar un producto

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** El comercio está aprobado y el producto está pendiente con imagen.

**Recorrido:** Revisar nombre, presentación, categoría, imagen y precio final; aprobar y publicar.

**Resultado:** Se crea o actualiza el producto público y se calcula el precio base para conservar el precio final con los impuestos configurados.

**Alternativas y controles:** Un local no aprobado, una imagen faltante o impuestos incompatibles impiden publicar. No aprobar precios ilustrativos como reales sin validación del comercio.

### G04 Pedir correcciones de un producto

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** La propuesta requiere cambios.

**Recorrido:** Abrir el producto; registrar observaciones; solicitar cambios; esperar la corrección y un nuevo envío del comercio.

**Resultado:** La propuesta queda para revisión y el producto público se retira cuando corresponde.

**Alternativas y controles:** No modificar silenciosamente una presentación ya comprada para resolver faltantes de pedidos confirmados; ese problema requiere otro circuito.

### G05 Corregir la cuenta propietaria de un local

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** Se verificó qué cuenta debe gestionar el comercio.

**Recorrido:** Revisar el propietario actual y la cuenta correcta; verificar que no tenga otro local en el mismo sitio; actualizar la vinculación; probar su acceso.

**Resultado:** Los permisos de local, productos y preparaciones siguen al propietario correcto.

**Alternativas y controles:** No asignar un comercio a una cuenta por coincidencia de nombre. La transferencia cambia quién accede a sus datos y debe estar autorizada.

### G06 Dar de alta y vincular un repartidor

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** La persona tiene una cuenta activa o se autorizó crearla.

**Recorrido:** Crear la ficha con nombre y teléfono; seleccionar Cuenta para Mi reparto; guardar; verificar el ingreso del repartidor.

**Resultado:** La persona accede a Mi reparto y solo ve los pedidos que se le asignan.

**Alternativas y controles:** Una cuenta no puede vincularse a dos fichas de repartidor. Desactivar al repartidor bloquea el acceso operativo a sus recorridos.

### G07 Asignar o cambiar el repartidor

**Actor:** Coordinación o administrador autorizado. **Estado:** Disponible.

**Condición inicial:** El pedido está confirmado y todavía no salió a reparto.

**Recorrido:** Abrir Reparto y cobros; elegir un repartidor activo; pulsar Asignar repartidor. Para cambiarlo antes de salir, elegir el reemplazo y guardar.

**Resultado:** El pedido queda asignado. Un reemplazo reinicia la aceptación y revoca el acceso del repartidor anterior.

**Alternativas y controles:** El botón no elige automáticamente una persona. No se permite cambiar de repartidor después de salir. La asignación automática por zona o capacidad está pendiente.

### G08 Supervisar pedidos y resolver incidencias

**Actor:** Coordinación o administrador autorizado. **Estado:** Disponible.

**Condición inicial:** Existen pedidos confirmados o solicitudes de retiro.

**Recorrido:** Consultar Preparaciones y reparto, Pedidos por franja y Reparto y cobros; filtrar retiros solicitados, estados y entregados sin cobrar; revisar el historial.

**Resultado:** Coordinación identifica los pendientes y puede intervenir con las acciones administrativas existentes.

**Alternativas y controles:** No confundir Listo para retirar, Entregado y Cobrado. Las acciones manuales deben reflejar hechos reales y respetar los mismos controles de estado.

### G09 Cancelar una compra antes del retiro

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** El pedido puede cancelarse, no salió a reparto, no hay productos retirados ni cobros activos.

**Recorrido:** Revisar el pedido y sus preparaciones; cancelar desde administración; comprobar el estado y la devolución del stock reservado.

**Resultado:** El pedido y sus preparaciones pendientes quedan cancelados. Se repone una sola vez el stock reservado cuando sigue activo su control.

**Alternativas y controles:** Después del retiro o con un cobro registrado, la cancelación simple se bloquea. No existe un circuito completo de devolución posterior a la entrega.

### G10 Anular y corregir un registro de cobro

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** Existe un cobro registrado y se identificó el error.

**Recorrido:** Abrir el registro; elegir Anular con motivo; explicar la corrección; registrar un nuevo cobro si corresponde.

**Resultado:** El original se conserva como anulado con fecha y responsable. La corrección genera un registro nuevo y mantiene la trazabilidad.

**Alternativas y controles:** No se puede borrar ni editar el importe original. Si respalda una liquidación activa, deben resolverse primero las liquidaciones; las pagadas requieren otro circuito.

### G11 Crear y publicar una oferta

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** Hay listas de precios habilitadas y un producto publicado con una sola variante.

**Recorrido:** Abrir Ofertas y promociones; elegir producto, sitio y lista; indicar descuento, inicio y fin opcional; publicar.

**Resultado:** Se crea una regla porcentual nativa sobre el precio de venta. La promoción se muestra cuando esté vigente y sea la regla aplicable al visitante.

**Alternativas y controles:** El descuento debe ser mayor que 0 y menor que 100. Solo puede existir una oferta publicada por producto y lista. No hay cupones ni promociones dos por uno en esta versión.

### G12 Pausar o actualizar una promoción

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** Existe una oferta publicada o pausada.

**Recorrido:** Pausar para retirar su regla; editar condiciones; volver a publicar cuando corresponda; revisar el precio público y el pedido.

**Resultado:** La pausa restaura el precio resultante de las demás reglas vigentes. Una oferta vencida deja de aplicar y de mostrarse.

**Alternativas y controles:** El registro vencido conserva el estado Publicada hasta pausarlo. Los pedidos confirmados conservan sus importes; los carritos abiertos pueden actualizar su precio.

## Comisiones y liquidaciones

### L01 Configurar la comisión por comercio

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** Existe un comercio registrado.

**Recorrido:** Abrir su ficha; indicar Comisión de la plataforma entre 0 y 100 por ciento; guardar.

**Resultado:** La próxima liquidación generada toma ese porcentaje. El valor inicial del circuito es cero.

**Alternativas y controles:** Cambiar la comisión no modifica detalles ya generados. La comisión se calcula sobre productos con impuestos; el envío queda fuera de la liquidación al local.

### L02 Generar el detalle de una liquidación

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** Existen preparaciones entregadas de pedidos confirmados y completamente cobrados.

**Recorrido:** Crear un borrador; elegir comercio y período de entrega; usar Generar detalle; revisar productos, comisión y neto.

**Resultado:** Se reservan las preparaciones elegibles y se guarda una copia de la comisión aplicada. Cada preparación puede estar en una sola liquidación activa.

**Alternativas y controles:** No se incluyen pendientes de entrega o cobro, preparaciones ya reservadas ni pedidos en otra moneda. El período usa la fecha de entrega elegida en el pedido, inclusive.

### L03 Confirmar una liquidación

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** El borrador tiene detalle generado y revisado.

**Recorrido:** Revisar cada pedido, el total de productos, comisión y neto; confirmar la liquidación.

**Resultado:** Queda confirmada con fecha y responsable. El detalle permanece protegido contra modificaciones.

**Alternativas y controles:** Se vuelven a comprobar entrega y cobro de los pedidos. Si hay inconsistencias, debe resolverse el caso antes de confirmar.

### L04 Registrar el pago realizado al comercio

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** La liquidación está confirmada y sin pagar.

**Recorrido:** Realizar el pago por el canal habitual; cargar medio y referencia o recibo; usar Registrar pago realizado.

**Resultado:** La liquidación queda Pagada con fecha y responsable. No puede pagarse de nuevo desde el mismo documento.

**Alternativas y controles:** El sistema no transfiere dinero, no verifica el banco ni genera automáticamente un asiento contable. No usar el botón antes de realizar y verificar el pago.

### L05 Anular y recalcular una liquidación

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** La liquidación está en borrador o confirmada y todavía no se pagó.

**Recorrido:** Cargar un motivo; anular; crear una nueva liquidación para el período y comercio cuando corresponda.

**Resultado:** El detalle anterior se conserva y sus preparaciones quedan libres. El nuevo documento usa la comisión vigente al generarse.

**Alternativas y controles:** Una liquidación pagada no puede anularse en este circuito. No se elimina el historial para corregir importes.

### L06 Consultar y proteger el historial de liquidaciones

**Actor:** Administrador autorizado. **Estado:** Disponible.

**Condición inicial:** Existen liquidaciones o registros de cobro relacionados.

**Recorrido:** Filtrar por comercio y estado; abrir el detalle; consultar confirmación, pago y anulaciones; revisar dependencias antes de corregir un cobro.

**Resultado:** Se conoce qué pedidos se liquidaron, cuánto se descontó, cuánto se registró como pagado y quién lo hizo.

**Alternativas y controles:** Comercios y repartidores no tienen acceso al módulo de liquidaciones. Una liquidación activa bloquea la anulación del cobro que la respalda.

## Controles y excepciones

### X01 Rechazar el acceso a datos ajenos

**Actor:** Sistema. **Estado:** Disponible.

**Condición inicial:** La petición está autenticada o se intenta abrir una dirección privada.

**Recorrido:** Comprobar propietario, repartidor asignado, sitio y compañía; aplicar reglas de lectura y escritura; limitar los datos mostrados.

**Resultado:** Cada comercio ve lo suyo; cada repartidor ve sus recorridos; el cliente consulta sus compras; administración utiliza sus permisos específicos.

**Alternativas y controles:** Cambiar un identificador en una dirección no concede acceso. El rechazo puede presentarse como acceso denegado o página no encontrada para no exponer datos ajenos.

### X02 Resolver compras simultáneas de la última unidad

**Actor:** Sistema. **Estado:** Disponible.

**Condición inicial:** El control de stock está activo y hay demanda concurrente.

**Recorrido:** Bloquear los registros de stock al confirmar; recalcular lo necesario; confirmar solo si alcanza; descontar las unidades una vez.

**Resultado:** Se evita confirmar dos ventas sobre la misma última unidad. La compra que no puede reservar recibe una validación.

**Alternativas y controles:** Agregar al carrito no reserva. Repetir una confirmación no debe duplicar el descuento de stock; cancelar tampoco debe reponer más de una vez.

### X03 Rechazar formularios de una sesión vencida

**Actor:** Sistema y usuario. **Estado:** Disponible.

**Condición inicial:** Se envía un formulario protegido cuyo token ya no corresponde a la sesión.

**Recorrido:** Validar la sesión y el token CSRF; rechazar el cambio si son inválidos; abrir de nuevo el formulario e ingresar cuando corresponda.

**Resultado:** No se ejecuta una operación con un formulario de otra sesión. Un formulario nuevo permite retomar la tarea.

**Alternativas y controles:** No desactivar la protección para resolver el error. Revisar las pestañas antiguas después de cambiar de cuenta o cerrar sesión.

### X04 Confirmar una compra sin generador PDF

**Actor:** Sistema. **Estado:** Disponible.

**Condición inicial:** La venta es web y el generador wkhtmltopdf no está instalado.

**Recorrido:** Detectar la falta del generador al preparar la notificación; omitir el reporte PDF automático; continuar el postproceso del pedido.

**Resultado:** La ausencia del PDF no revierte la compra ni impide generar preparaciones. Los adjuntos estáticos se conservan.

**Alternativas y controles:** Los reportes manuales siguen necesitando el generador. El envío de correos depende de la configuración; el circuito vuelve a adjuntar reportes si se instala el componente.

### X05 Detectar una preparación sin dueño registrado

**Actor:** Coordinación o administrador autorizado. **Estado:** Disponible.

**Condición inicial:** Una compra contiene un producto cuyo comercio no tiene una cuenta propietaria asociada.

**Recorrido:** Revisar la preparación en administración; identificar el origen; validar la vinculación del comercio y coordinar la preparación o la corrección necesaria.

**Resultado:** El caso queda bajo supervisión y no se asigna automáticamente a una persona arbitraria.

**Alternativas y controles:** Los productos de demostración pueden generar este caso. Corregir el catálogo futuro no debe cambiar sin revisión la identidad comercial capturada en compras anteriores.

### X06 Bloquear un repartidor sin acceso vigente

**Actor:** Sistema y coordinación. **Estado:** Disponible.

**Condición inicial:** La cuenta está inactiva, el repartidor está desactivado o la asignación cambió.

**Recorrido:** Volver a validar la vinculación al abrir el recorrido y antes de registrar movimientos; rechazar la acción si ya no corresponde.

**Resultado:** Una pestaña antigua no permite seguir operando un recorrido que dejó de pertenecer a esa cuenta.

**Alternativas y controles:** La reasignación se permite antes de salir y requiere nueva aceptación. Si el pedido ya está en camino, coordinación debe resolver la incidencia sin alterar registros arbitrariamente.

### X07 Conservar trazabilidad y precios coherentes

**Actor:** Sistema y administración. **Estado:** Disponible.

**Condición inicial:** Se registra una acción de preparación, reparto, cobro, promoción o liquidación.

**Recorrido:** Tomar importes del servidor; aplicar la regla de precios real; registrar responsables y momentos; bloquear cambios incompatibles con el estado del pedido.

**Resultado:** Los importes mostrados, el cobro completo y las liquidaciones se pueden explicar a partir de sus registros.

**Alternativas y controles:** Una anotación no reemplaza una acción de estado. Registrar un cobro no equivale a una factura, una conciliación o una transferencia bancaria.

## Pruebas de aceptación sugeridas

- **QA01 Compra de un local con efectivo al recibir:** Pedido confirmado; una preparación; cobro pendiente.
- **QA02 Compra de dos locales:** Dos preparaciones y un total de compra; cada dueño ve solo la suya.
- **QA03 Dos compras simultáneas de la última unidad:** Solo una confirma; el stock final no queda negativo.
- **QA04 Franja que vence antes de confirmar:** Se solicita una nueva fecha o franja disponible.
- **QA05 Retiro solicitado dos veces:** Se conserva una solicitud y su responsable, sin duplicados.
- **QA06 Salida con un local todavía sin retirar:** El sistema bloquea En camino.
- **QA07 Entrega sin registrar dinero:** El pedido queda Entregado y el cobro continúa pendiente.
- **QA08 Efectivo insuficiente y segundo cobro:** Ambos intentos se rechazan; el cobro válido calcula el vuelto.
- **QA09 Reasignación antes de salir:** El anterior pierde acceso y el reemplazo debe aceptar.
- **QA10 Oferta futura, vigente y pausada:** Solo la vigente aparece; el pedido utiliza la misma regla.
- **QA11 Liquidación de un pedido sin cobrar:** No se incluye en el detalle elegible.
- **QA12 Liquidación pagada y corrección de su cobro:** Se bloquean la anulación simple y la pérdida del historial.
- **QA13 Formulario de sesión anterior y acceso ajeno:** Se rechazan el token inválido y los datos fuera del alcance de la cuenta.
- **QA14 Confirmación sin generador PDF:** La compra confirma sin el reporte automático y genera preparación.

## Casos pendientes y límites operativos

### Devoluciones y faltantes parciales

Sustituir productos, devolver una parte o ajustar el importe después del retiro y de la entrega.

### Asignación automática

Elegir repartidor por zona, franja, cercanía, disponibilidad y capacidad. La asignación vigente es manual.

### Múltiples entregas por compra

Dividir un pedido en recorridos o entregas independientes. El modelo actual utiliza una entrega completa.

### Cupos y horarios comerciales

Limitar pedidos por franja, anticipar cierres, bloquear días y validar horarios de cada local.

### Avisos y seguimiento en vivo

Notificaciones automáticas por WhatsApp, actualizaciones sin recargar y ubicación GPS.

### Contabilidad y facturación

Emitir comprobantes, generar pagos y asientos, calcular retenciones y conciliar bancos.

### Dinero en poder del repartidor

Rendición de caja, arqueo, depósitos y diferencias entre lo cobrado y lo entregado a administración. El cobro actual identifica al responsable, pero no completa esa rendición.

### Pagos electrónicos integrados

Verificación bancaria automática, tarjetas, billeteras y conciliación. La transferencia actual se registra como verificada manualmente.

### Promociones avanzadas

Cupones, dos por uno, combinaciones y productos con múltiples variantes en el módulo de ofertas.

### Autoservicio adicional

Cancelación del comprador, visualización de liquidaciones por el comercio y resolución autónoma de disputas.

### Preparación para producción

Validar catálogo y stock reales, configurar correo y PDF, respaldos, supervisión y recuperación, y hacer ensayos con las personas que operarán el servicio.

## Referencias

Módulo wheelwright_ahorra versión 19.0.3.1.0. Los paneles actuales prevalecen sobre instrucciones de etapas anteriores.

- **Acceso y checkout:** INGRESO_CUENTAS.md; controllers/checkout.py; models/checkout.py.
- **Comercios y productos:** PORTAL_COMERCIOS.md; controllers/merchant.py; models/merchant.py.
- **Stock y entrega programada:** STOCK_DISPONIBILIDAD.md; FRANJAS_ENTREGA.md; models/stock.py; models/delivery_windows.py.
- **Retiro y reparto:** PORTAL_REPARTIDORES.md; models/courier_portal.py; controllers/courier_portal.py; models/dispatch.py.
- **Cobros y liquidaciones:** REPARTO_COBROS.md; LIQUIDACIONES_COMERCIOS.md; models/settlement.py.
- **Promociones y continuidad:** OFERTAS_PROMOCIONES.md; models/offers.py; CONFIRMACION_SIN_PDF.md; models/order_notifications.py.
