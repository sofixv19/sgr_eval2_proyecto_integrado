# Estándares de desarrollo y seguridad — SGR La Serena

Este documento resume los estándares que el equipo aplica al construir el sistema
y dónde se puede comprobar cada uno en el código.

## 1. Estándares de construcción

| Estándar | Cómo se aplica | Dónde verlo |
|---|---|---|
| PEP 8 (estilo de Python) | Revisión automática con `flake8` (largo máximo 130). El proyecto pasa sin errores. | `setup.cfg` |
| Nombres en español | Los modelos van en singular y en PascalCase (`Funcionario`, `MetaProyecto`). Las funciones y variables van en snake_case (`validar_credenciales`). Las URLs tienen nombre con espacio de nombres (`organizacion:cargo_crear`). | Todo el proyecto |
| Una app por dominio | La lógica se reparte en `delegaciones`, `gestion` y `organizacion`, que son el negocio. Además están `cuentas`, que maneja el acceso, y `comun`, que guarda el código reutilizable. | Carpetas del proyecto |
| Capas separadas | Los modelos guardan los datos y las reglas del modelo. Los formularios validan la entrada. Las vistas solo coordinan. Los servicios contienen lógica pura que se puede probar sola (`cuentas/servicios.py`, `gestion/services.py`). Los templates se encargan de la presentación. | — |
| Reutilización (DRY) | Los mantenedores de tablas maestras usan vistas genéricas comunes, y los validadores y templates también se comparten. | `comun/vistas.py`, `comun/validadores.py`, `comun/templates/` |
| Plantillas con herencia | Todas las pantallas extienden `base.html`, que tiene el menú, los mensajes y el pie. | `templates/base.html` |
| Configuración fuera del código | `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` y los datos de la base de datos se leen desde `.env` con python-decouple. | `sgr_evaluacion/settings.py`, `.env.example` |
| Base de datos versionada | Todo cambio de estructura o de datos de ejemplo se hace mediante una migración. | `*/migrations/` |
| Documentación en el código | Cada módulo, clase y función tiene su docstring en español. | Todo el proyecto |
| Pruebas | Cada caso del plan de pruebas tiene su prueba automatizada con el ID en el docstring (`CP-...`). | `*/tests.py`, `plan_pruebas.py` |
| Control de versiones | Se usa Git con commits descriptivos, y `.gitignore` excluye `.env`, `db.sqlite3` y `logs/`. | `.gitignore` |

## 2. Estándares de seguridad (basados en OWASP Top 10)

| Riesgo OWASP | Control aplicado | Dónde verlo |
|---|---|---|
| A01 Control de acceso roto | Todo el sitio exige sesión iniciada. Cada acción de crear, modificar o eliminar exige el permiso de Django que le corresponde, y si falta se responde 403. Hay grupos por rol con mínimo privilegio. | `cuentas/middleware.py`, `comun/vistas.py`, `configurar_roles` |
| A02 Fallas criptográficas | Las contraseñas se guardan con hash PBKDF2-SHA256. La `SECRET_KEY` vive fuera del código. Las cookies seguras quedan listas para activarse con HTTPS (`USAR_HTTPS`). | `settings.py` |
| A03 Inyección | Todas las consultas pasan por el ORM, que usa consultas parametrizadas. Los templates escapan el HTML automáticamente (XSS). Las entradas se validan con listas blancas, por ejemplo el formato de usuario, el RUT y el teléfono. | `comun/validadores.py`, `cuentas/servicios.py` |
| A04 Diseño inseguro | El login responde con un mensaje genérico, para no revelar qué usuarios existen. La sesión se cierra solo por POST. Se bloquea la redirección hacia sitios externos (`next`). | `cuentas/views.py` |
| A05 Configuración insegura | Se usa `DEBUG=False` en producción, con páginas propias de error 403, 404 y 500. Se envían las cabeceras `X-Frame-Options: DENY`, `nosniff` y `Referrer-Policy`. | `settings.py`, `templates/40x.html` |
| A07 Fallas de autenticación | La cuenta se bloquea 15 minutos después de 5 intentos fallidos. La sesión expira tras 30 minutos sin uso. Las cookies son `HttpOnly` y `SameSite=Lax`. Se exige una contraseña segura con los validadores de Django. | `cuentas/servicios.py`, `settings.py` |
| A08 Integridad de datos | Hay protección CSRF en todos los formularios. Las claves foráneas usan PROTECT o RESTRICT, de modo que no se borran datos en uso, y el error se informa al usuario. | Formularios, modelos |
| A09 Registro y monitoreo | Los intentos de acceso fallidos y los accesos con cuentas inactivas o bloqueadas se registran en `logs/seguridad.log`. | `settings.py` (`LOGGING`) |

## 3. Pendiente (siguiente etapa)

- Habilitar HTTPS con Nginx y Gunicorn, y después activar `USAR_HTTPS=True`.
- Restringir el puerto 22 (SSH) del grupo de seguridad a la IP del equipo.
