# Inicio del sistema local

Ejecutar `iniciar_sistema.ps1` con la cuenta habitual de Windows, fuera del entorno restringido de Codex.

- Tienda: http://127.0.0.1:8070/shop
- Administración: http://127.0.0.1:8070/odoo
- Base de datos: wheelwright_ahorra_dev
- Registros: odoo-estable.err.log y odoo-estable.out.log

El arranque usa la configuración existente y conserva los datos y sesiones. Se vincula únicamente a 127.0.0.1 y mantiene cron desactivado, como el entorno de pruebas anterior.

Se pasa `--limit-time-real=0` para esta instancia de desarrollo: el servidor con hilos de Odoo contabiliza conexiones HTTP inactivas del navegador y, con el límite predeterminado de 120 segundos, intentaba reiniciarse. El diagnóstico mostró un hilo esperando en `socket.recv_into`, sin una solicitud activa. Esta opción evita ese reinicio; no es una configuración de producción.

No iniciar dentro del sandbox: el guardado de sesiones puede quedar bloqueado por permisos al crear archivos temporales.
