# Inicio de módulos de administración

Versión 19.0.2.6.0. Instalado en wheelwright_ahorra_dev.

El inicio administrativo de `/odoo`, cuando no se indica una acción específica,
abre una cuadrícula de aplicaciones con los íconos nativos, búsqueda por módulos
y menús internos, y colores verde/amarillo de wheel-ahorra. El botón de cuadrícula
de la esquina superior izquierda vuelve a este inicio. En celular se conserva,
además, el botón nativo de menús del módulo actual.

El buscador tolera mayúsculas y acentos; Enter abre el primer resultado y Escape
limpia la búsqueda. Cada tarjeta mantiene un enlace para abrir con Ctrl/Cmd-clic.
La navegación usa el servicio nativo de menús y acciones, con su protección de
cambios sin guardar. Los enlaces directos y las PWA limitadas a una app conservan
su comportamiento. No se instalan aplicaciones ni se amplían permisos.

Solo se usa la información de menús que Odoo ya autoriza para la sesión. Las
cuentas de cliente/comerciante siguen entrando al portal, no al backend.

Archivos: `static/src/js/app_launcher.js`, `static/src/xml/app_launcher.xml`,
`static/src/css/app_launcher.css`, `static/src/img/app-icon.svg`.

Verificación: JavaScript comprobado con `node --check`; XML válido; Odoo genera
el paquete administrativo incluyendo los nuevos JS/CSS/XML y todos los módulos
de administrador tienen acciones válidas. El portal mantiene el rechazo nativo
de acceso a menús. Resultado en `inicio_apps_verificado.json`.

La inspección visual con una sesión de administrador queda pendiente: la sesión
disponible en el navegador integrado pertenece a un comerciante. Abrir `/odoo`
con el administrador y recargar con Ctrl+F5 para descargar los recursos nuevos.
