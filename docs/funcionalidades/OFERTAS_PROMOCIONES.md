# Ofertas y promociones

Versión 19.0.3.0.0. Página pública: http://127.0.0.1:8070/ofertas.

Incluye acceso en el menú y pie, banner amarillo en portada y hasta cuatro ofertas destacadas antes de las categorías. La página de ofertas muestra todas las promociones aplicables al visitante. Sin ofertas vigentes muestra un estado vacío, sin descuentos inventados.

## Cargar una promoción

1. Administración → wheel-ahorra → Ofertas y promociones → Nuevo.
2. Elegir un producto publicado, el sitio y la lista **wheel-ahorra · Precios de tienda**.
3. Indicar porcentaje mayor que 0 y menor que 100, inicio y, si corresponde, fin. Las fechas se muestran en la zona horaria del usuario de Odoo.
4. Pulsar **Publicar oferta**. **Pausar oferta** retira la regla y permite editar sus condiciones.

La publicación crea una regla porcentual nativa de Odoo sobre el precio de venta. El precio con impuestos se calcula con la lista y la posición fiscal del visitante, igual que en la tienda. Las tarjetas incluyen descuento, precio anterior, precio actual y ahorro. No se modifica el precio base del producto.

Para esta instalación se habilitaron las listas de precios con autorización del usuario. Se creó una lista específica del sitio, sin reglas iniciales, y se comprobó que conserva los precios base de los 28 productos publicados. No se dejaron ofertas cargadas.

## Controles y alcance

- Solo administración puede crear y gestionar promociones.
- Una oferta publicada por producto y lista; restricción única en base de datos.
- Esta versión admite productos con una sola variante y descuentos porcentuales, sin códigos ni 2×1.
- Las promociones futuras, vencidas, agotadas, de otros sitios o no publicadas no se muestran.
- Se verifica que la regla elegida por Odoo sea exactamente la de la promoción; si otra regla prevalece, no se presenta un descuento incorrecto.
- Una lista compartida puede afectar a todos los clientes que la utilicen. La lista inicial creada es exclusiva del sitio wheel-ahorra.
- Al vencer, la regla deja de aplicar y la oferta deja de verse. El registro conserva el estado Publicada: pausar para editar o reemplazarla.
- Los carritos sin confirmar usan las condiciones vigentes de Odoo. Los pedidos ya confirmados mantienen sus precios guardados.

## Verificación

`verificar_ofertas.py` usa datos ficticios y revierte la transacción: publicación, descuento del 20 %, permisos, condiciones protegidas, duplicados, tarjeta renderizada, precio del pedido, pausa con restauración del precio, fechas futuras y vencidas. Resultado: APROBADO.

Los productos y promociones ficticios se revirtieron. No se hicieron compras ni cobros reales.
