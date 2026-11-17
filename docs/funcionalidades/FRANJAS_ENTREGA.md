# Franjas de entrega

Versión 19.0.2.5.0, activada en el sitio local 1 (wheelwright_ahorra_dev).

| Franja | Horario de Argentina |
|---|---|
| Mediodía | 12:00 a 14:00 |
| Tarde | 17:00 a 20:00 |
| Noche | 22:00 a 00:00 del día siguiente |

Después de validar la dirección, antes del pago, el cliente elige fecha y franja
en `/shop/entrega`. Ver horarios de esa fecha actualiza las opciones sin guardar
la selección; Guardar y continuar al pago conserva ambos datos en el pedido.
Las franjas del día dejan de estar disponibles cuando comienzan. No hay un
horario de corte anticipado ni cupos. No se promete una hora exacta.

La fecha corresponde al comienzo de la franja: la noche del martes termina el
miércoles a las 00:00. Se calcula con America/Argentina/Buenos_Aires, sin depender
del reloj o zona horaria del navegador ni del administrador.

La entrega elegida aparece en revisión/pago, confirmación y Mi cuenta/Pedidos.
Cada comerciante ve la fecha y franja en sus preparaciones, sin acceder a la
orden completa ni a otros locales.

Administración dispone de **wheel-ahorra → Pedidos por franja**, con pedidos
confirmados agrupados por fecha y horario. La pestaña **Entrega wheel-ahorra**
de la venta permite consultar/coordinar la fecha y franja, con seguimiento en el
historial nativo. También aparecen en Preparaciones y reparto.

Los pedidos anteriores no recibieron fechas inventadas. Las nuevas compras web
de productos requieren una selección válida antes de pagar y confirmar. Una
franja que vence mientras el carrito está abierto debe volver a elegirse. El
carrito no reserva cupos y las ventas de solo servicios no exigen horario.

La ruta solo modifica el carrito de la sesión, valida CSRF y bloquea la orden
durante el guardado. No permite editar pedidos ajenos ni confirmados mediante
un identificador enviado por el navegador.

Pruebas: `verificar_franjas.py` (límites horarios, cambio de día, validación previa
al stock y acceso del local) y `verificar_franjas_web.py` (checkout, CSRF, fecha y
franja inválidas, persistencia en pago y portal). Los fixtures fueron revertidos
o eliminados; no se enviaron correos ni se registraron cobros.
