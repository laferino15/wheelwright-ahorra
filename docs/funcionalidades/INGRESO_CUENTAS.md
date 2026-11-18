# Ingreso y creación de cuenta

Versión 19.0.2.9.0. Las pantallas de ingreso, alta de cuenta y recuperación comparten la identidad visual de wheel-ahorra: marca verde y amarilla, ilustración de compras locales, formulario con etiquetas en español y adaptación a celular.

- Ingreso: http://127.0.0.1:8070/web/login
- Registro: http://127.0.0.1:8070/web/signup
- Recuperación: http://127.0.0.1:8070/web/reset_password

Las vistas heredan los formularios nativos de Odoo y conservan campos de autenticación, CSRF, destinos de redirección, tokens de invitación, errores y opciones de autenticación adicionales habilitadas. Se muestra directamente el formulario de ingreso en lugar del selector de usuarios recordados.

Las contraseñas mantienen los controles nativos para mostrar u ocultar el texto. Los botones tienen etiquetas accesibles y se distinguen los elementos enfocados al usar teclado.

La recuperación por correo conserva la configuración existente de Odoo; el diseño no configura SMTP ni envía mensajes por sí mismo.

Verificación: renderizado de ingreso y registro en navegador; navegación entre ambos manteniendo el destino /mi-comercio; revisión de registro a 390 px sin desbordamiento horizontal. No se crearon cuentas ni se modificaron contraseñas durante esta revisión visual.
