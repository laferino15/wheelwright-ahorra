# Pruebas locales de wheel-ahorra

Scripts para ejecutar mediante `odoo-bin shell` en una base local de desarrollo
preparada. No son pruebas para ejecutar en producción. Se protege explícitamente
el nombre de base `wheelwright_ahorra_dev`.

- `verificar_reparto.py`: verificaciones del modelo; revierte su transacción.
- `verificar_reparto_web.py`: vistas, RPC y portal con fixtures temporales.
- `probar_jornada_completa.py`: última verificación integral aprobada. Usa HTTP/RPC
  contra `127.0.0.1:8070`, tres comercios, cuatro compradores, seis productos y
  seis pedidos; incluye confirmaciones concurrentes de la última unidad.

Los scripts web crean y eliminan datos de prueba. No ejecutarlos mientras haya
usuarios operando: la jornada compara el catálogo y los pedidos anteriores al
finalizar. Requieren `requests` y `lxml` en el entorno Python de Odoo.
La jornada exige el proveedor COD habilitado con ID 25, sitio ID 1 y categorías
9, 10 y 15 del entorno local; revisar estas precondiciones en otra base.
No contiene contraseñas: las cuentas ficticias usan claves aleatorias en memoria.
El postproceso COD se ejecuta desde el proceso de pruebas con las notificaciones
de pedido suprimidas. No verifica cobros bancarios, entregas físicas ni el envío
de correos. Los informes generados junto al script están excluidos de Git.

Para ejecutarlos desde la consola de Odoo, abrir el archivo por ruta absoluta
con `exec(compile(open(r"RUTA/archivo.py", encoding="utf-8").read(), "prueba", "exec"))`.
El resultado de la última jornada está en `docs/pruebas/RESULTADO_JORNADA.md`.
