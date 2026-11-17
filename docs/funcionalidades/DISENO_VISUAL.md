# Identidad visual de wheel-ahorra

Versión del módulo: 19.0.2.2.0. Instalada en wheelwright_ahorra_dev.

La portada, tienda, fichas de producto y portal comparten la paleta verde
#07533f, verde oscuro #073e31, amarillo #f5cf52 y fondo #f7f8f4.

- Encabezado único con marca, búsqueda nativa del catálogo, cuenta y carrito
  nativo (con contador). Menú de cuenta conserva acceso administrativo y cierre
  de sesión. Navegación completa en dos filas en celulares.
- Portada sin el segundo encabezado. Categorías en mosaico, selección inicial
  con productos de distintos rubros y acceso diferenciado para sumar un local.
- Tienda con presentación y categorías, sin duplicar la tira de categorías
  original. Conserva filtros, búsqueda dentro de categorías, precios, impuestos,
  carrito y paginación de Odoo.
- Formularios y tablas de Mi comercio con espaciado consistente y estados
  identificados por texto y color. Pie de página sin datos empresariales falsos.
- Los productos de prueba mantienen su advertencia y comercio asociado.

## Archivos

`views/visual.xml` contiene el encabezado, pie y presentación del catálogo;
`static/src/css/visual.css` define los estilos compartidos y responsive.
La portada sigue en `views/plantilla_home.xml`.

## Actualización de vistas anteriores

El sitio tenía copias específicas de algunas vistas del módulo. Se respaldaron
en `respaldo_vistas_diseno.json` antes de sincronizarlas con el código actualizado.
Para actualizar una instalación anterior a esta versión se debe ejecutar primero
`preparar_actualizacion_visual.py` en Odoo shell: adapta el XPath del enlace de
comerciantes antes de quitar la navegación duplicada. Después de actualizar el
módulo, `sincronizar_diseno_local.py` sincroniza las copias del sitio 1 y aplica
el nombre y metadatos de wheel-ahorra. Son scripts para esta base local; no deben
ejecutarse sobre otra base sin revisar sus identificadores. Reiniciar Odoo tras
los cambios externos al proceso web permite renovar su caché de vistas.

## Verificación

Inspección visual en escritorio y ancho móvil de 390 px: portada, catálogo,
Mi comercio y pedidos. Sin imágenes rotas en portada ni desbordamiento horizontal
de página en móvil. Menú de categorías con desplazamiento propio.
Comprobación HTTP de inicio, tienda, categoría, búsqueda, vender, carrito y login.
Las operaciones de compra, aprobación y preparación no se modificaron.
