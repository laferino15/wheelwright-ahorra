# Ajustes del entorno local

Ejecutar con `odoo-bin shell` solo después de actualizar el módulo y revisar los
registros objetivo. Ambos scripts protegen el nombre `wheelwright_ahorra_dev`.

- `activar_franjas.py`: activa las franjas del sitio ID 1; requiere checkout local.
- `inicializar_reparto.py`: reconoce pedidos web cancelados anteriores. No inventa
  repartidores, entregas ni cobros históricos.

Ambos guardan cambios en la base; no son parte de las pruebas con rollback.
