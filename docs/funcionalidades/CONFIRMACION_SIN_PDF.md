# Confirmación web sin generador PDF

La confirmación nativa de efectivo al recibir forzaba el envío del correo de confirmación con un reporte PDF. En un sistema sin wkhtmltopdf, la generación del adjunto fallaba y revertía la confirmación: el pedido quedaba en borrador, la transacción pendiente de postproceso y no se creaban preparaciones.

El módulo conserva el correo nativo y omite únicamente los reportes PDF generados de las plantillas de venta cuando el generador está ausente y la notificación corresponde a una venta web. Los adjuntos estáticos se conservan. Los reportes manuales siguen necesitando wkhtmltopdf; si se instala, los adjuntos automáticos vuelven a generarse normalmente.

Prueba `verificar_confirmacion_sin_pdf.py`: postproceso COD real, generación de preparación, lectura por el dueño, repetición sin duplicados y conservación de adjuntos estáticos. Todas las llamadas de envío externo se interceptan y los datos ficticios se revierten.

Para diagnosticar pedidos no visibles: revisar primero `sale.order.state`, transacción e `is_post_processed`; después la asociación `wah_merchant_id` de las líneas y el propietario del comercio. Una cuenta distinta del propietario no puede consultar sus preparaciones.
