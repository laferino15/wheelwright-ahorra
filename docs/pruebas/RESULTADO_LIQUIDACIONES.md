# Verificación de liquidaciones

Resultado: APROBADA en la base local wheelwright_ahorra_dev (17/11/2026).

- Comisión inicial 0 %, configurable por comercio y validada entre 0 y 100 %.
- Solo se incluyen pedidos entregados y cobrados del período seleccionado.
- Envío excluido de los importes del local.
- Duplicados bloqueados y detalle protegido contra cambios.
- Comisión conservada aunque cambie la configuración del comercio.
- Confirmación y pago único con referencia, fecha y responsable.
- Anulación de documentos sin pagar, conservando historial y liberando pedidos.
- Protección del cobro que respalda una liquidación.
- Acceso administrativo, rechazo de acceso de comerciantes y control de compañías.
- Vistas administrativas resueltas correctamente por Odoo.
- Prueba anterior de reparto, entrega, cobro, anulación y stock: APROBADA.
- Tienda, carrito, portal de comercios y acceso a administración: HTTP 200.

Los scripts revirtieron los datos ficticios al finalizar. Sin pagos reales ni correos.
No se ensayaron transferencias reales ni contabilidad. La generación simultánea está protegida por bloqueos y restricción única; esta sesión probó intentos duplicados secuenciales.
