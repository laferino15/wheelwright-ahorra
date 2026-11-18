# wheel-ahorra

Marketplace de comercios de Wheelwright, Santa Fe, sobre Odoo 19 Community.
Versión actual del módulo: **19.0.3.3.0**.

## Funciones implementadas

- Tienda y portal con identidad visual verde y amarilla, catálogo por categoría
  y productos asociados a cada comercio.
- Registro de comerciantes y revisión administrativa de locales y productos.
- Carrito unificado, checkout local y pago en efectivo al recibir.
- Stock por oferta, disponibilidad, reserva al confirmar y reposición al cancelar
  antes del retiro; protección de compras concurrentes de la última unidad.
- Preparaciones separadas por comercio y seguimiento del cliente.
- Franjas: 12:00–14:00, 17:00–20:00 y 22:00–00:00 del día siguiente.
- Asignación de repartidores, retiros por local, salida y entrega.
- Registro operativo de cobros en efectivo o transferencia verificada, vuelto,
  bloqueo de duplicados y anulación con motivo y trazabilidad.
- Liquidaciones por comercio con comisión configurable (inicialmente 0 %), detalle de pedidos entregados y cobrados, registro de pago y anulación con historial.
- Inicio administrativo con cuadrícula de aplicaciones y estilo de la tienda.

- Portal propio de comercios con Resumen, Productos, Stock y Pedidos.
- Portal propio de repartidores con retiros, entregas y cobros.
- Ofertas con listas de precios nativas y acceso directo según la cuenta.

## Instalación y actualización

Agregar `addons/custom` al `addons_path` de Odoo 19. El manifiesto declara las
dependencias de Website, eCommerce, localización argentina, delivery y registro
de usuarios. Instalar o actualizar `wheelwright_ahorra` en la base de desarrollo:

```text
python odoo-bin -c RUTA_CONFIG -d BASE_DESARROLLO -u wheelwright_ahorra --stop-after-init --no-http
```

Reiniciar el servicio tras actualizar. La configuración, credenciales y base
de datos se administran fuera de Git. Los productos, fotos del catálogo, locales,
usuarios y pedidos cargados en Odoo residen en PostgreSQL y su filestore; este
repositorio no sustituye un respaldo de ambos.

## Documentación y validación

- [Identidad visual](docs/funcionalidades/DISENO_VISUAL.md)
- [Portal de comercios](docs/funcionalidades/PORTAL_COMERCIOS.md)
- [Ingreso y creación de cuenta](docs/funcionalidades/INGRESO_CUENTAS.md)
- [Ofertas y promociones](docs/funcionalidades/OFERTAS_PROMOCIONES.md)
- [Stock y disponibilidad](docs/funcionalidades/STOCK_DISPONIBILIDAD.md)
- [Franjas de entrega](docs/funcionalidades/FRANJAS_ENTREGA.md)
- [Inicio de módulos](docs/funcionalidades/INICIO_MODULOS.md)
- [Reparto y cobros](docs/funcionalidades/REPARTO_COBROS.md)
- [Mi comercio y Mi reparto](docs/funcionalidades/PORTAL_REPARTIDORES.md)
- [Liquidaciones a comercios](docs/funcionalidades/LIQUIDACIONES_COMERCIOS.md)
- [Inicio local estable](docs/funcionalidades/INICIAR_SISTEMA.md)
- [Jornada simulada aprobada](docs/pruebas/RESULTADO_JORNADA.md)
- [Ejecución de pruebas locales](tests/local/README.md)
- [Ajustes locales](scripts/local/README.md)

La jornada comprobó compras, stock, preparación, reparto, entrega, cobros,
cancelación, permisos y concurrencia con datos ficticios eliminados al finalizar.
La inspección visual administrativa y la operación física con personas requieren
validación manual. El registro de cobro es operativo: no genera pagos contables,
conciliación bancaria ni facturas. Las liquidaciones calculan productos y comisión y registran el pago al local; no realizan transferencias ni generan asientos contables.
Las devoluciones posteriores al retiro todavía no tienen un circuito implementado.

## Documentos de producto y lanzamiento

- [Portal propio del comercio](docs/funcionalidades/PORTAL_PROPIO_COMERCIOS.md)
- [Casos de uso](docs/planificacion/Wheel_ahorra_Casos_de_uso.pdf)
- [Plan de lanzamiento de 30 días](docs/planificacion/Wheelwright_Ahorra_Plan_de_lanzamiento_30_dias.pdf)

El directorio `frontend` conserva un prototipo estático anterior; la aplicación activa es el módulo Odoo en `addons/custom/wheelwright_ahorra`.

## Reglas de trabajo

- No almacenar credenciales ni respaldos de bases en Git.
- Validar en desarrollo antes de desplegar; no modificar producción al probar.
- Trabajar mediante ramas y pull requests.
