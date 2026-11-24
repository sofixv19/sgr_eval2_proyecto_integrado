# Seguridad — SGR La Serena

Cubre los criterios **2.1.5.10** (autenticación y autorización),
**2.1.5.11** (amenazas y mitigación) y **2.1.5.12** (estándares de
codificación segura) de la rúbrica de Evaluación 2.

## 2.1.5.10 — Políticas de autenticación y autorización

> Actualizado en la versión 2.2.2 (noviembre 2026). La versión anterior de esta sección describía el sistema de la Evaluación 1, cuando el sitio todavía no tenía inicio de sesión.

**Autenticación** (`cuentas/`, `django.contrib.auth`):
- Todas las páginas, salvo la de ingreso, exigen haber iniciado sesión.
- Las contraseñas se guardan solo como hash PBKDF2-SHA256 con sal y pasan por los validadores de Django (largo mínimo, contraseñas comunes, solo números, parecido al usuario).
- Después de 5 intentos fallidos la cuenta se bloquea 15 minutos (`SGR_LOGIN_MAX_INTENTOS`, `SGR_LOGIN_MINUTOS_BLOQUEO`).
- La sesión vence a los 30 minutos sin actividad o al cerrar el navegador. La cookie es HttpOnly y SameSite=Lax.
- Cuando se crea un funcionario, el sistema genera una contraseña temporal que se muestra una sola vez.

**Autorización: permisos por rol y ámbito por delegación.** Cada cuenta pertenece a un grupo con permisos mínimos (`configurar_roles`). Además, cada consulta se filtra por el ámbito del usuario (`cuentas/perfiles.py`); un registro fuera de ese ámbito responde 404, sin confirmar siquiera que existe.

| Rol | Permisos | Qué puede hacer |
|---|---|---|
| Funcionario | 14 | Registrar y corregir sus actividades mientras están pendientes, subir evidencias, crear y actualizar compromisos de su delegación. Ve solo lo suyo |
| Delegado | 32 | Validar o rechazar las actividades de su equipo (nunca las propias), asignar metas, registrar felicitaciones, reclamos y ausencias, crear funcionarios de su delegación y reasignar compromisos |
| Coordinador | 22 | Ver todas las delegaciones, crearlas y desactivarlas, crear Delegados, administrar períodos y consultar la auditoría |
| Verificador / Auditor | 14 | Solo lectura de todo el sistema, incluida la auditoría |
| Administrador | 51 | Todas las tablas maestras. Tampoco puede modificar ni borrar la auditoría |

Las acciones prohibidas responden "Acceso denegado" (403) y quedan registradas en la auditoría con usuario, IP y ruta.

## 2.1.5.11 — Amenazas comunes y medidas de mitigación

| Amenaza | Medida de mitigación |
|---|---|
| Inyección SQL | Todas las consultas pasan por el ORM de Django (`QuerySets`), que genera SQL parametrizado automáticamente; no hay SQL armado por concatenación de texto en el proyecto. |
| Cross-Site Scripting (XSS) | Los templates de Django escapan automáticamente cualquier dato mostrado (`{{ variable }}`), salvo que se marque explícitamente como seguro — algo que este proyecto no usa. |
| Exposición de credenciales y `SECRET_KEY` | `SECRET_KEY`, contraseña de base de datos y demás configuración sensible viven solo en el archivo `.env` (`python-decouple`), excluido de Git mediante `.gitignore`. |
| Acceso no autorizado al panel administrativo | Django Admin exige autenticación y permisos de `staff`/`superuser`; no es accesible sin una cuenta válida. |
| Falsificación de solicitudes entre sitios (CSRF) | Middleware `CsrfViewMiddleware` de Django activo por defecto; todos los formularios del proyecto (incluidos los nuevos de Agregar/Modificar/Eliminar) usan `{% csrf_token %}`. |
| Borrado accidental o indebido de datos en uso | Restricciones `on_delete=PROTECT/RESTRICT` impiden borrar un Funcionario o Categoría en uso; además, la pantalla de "Eliminar" pide confirmación explícita antes de borrar cualquier registro (ver `CASOS_DE_USO.md`). |
| Validación falsa o manipulada (que alguien no autorizado marque una actividad como validada) | Aplicado en dos capas: el formulario público (`ValidacionForm`) solo lista Funcionarios con rol Delegado como opción, y el modelo (`Actividad.clean()`) rechaza igual la operación aunque se intente por otra vía (Admin, API futura, etc.). |
| Acceso horizontal (ver datos de otra delegación) | Cada consulta se filtra por el ámbito del usuario; un registro de otra delegación responde 404. Probado con CP-PERF y CP-AGE-001. |
| Exposición de datos personales (RUT, correo, teléfono del vecino) | Solo datos ficticios en el prototipo; cada rol ve únicamente su ámbito. Antes de usar datos reales hay que cumplir la Ley 19.628 y preparar la Ley 21.719 (vigencia fijada para el 1-12-2026; un proyecto de ley en trámite propone postergarla al 15-10-2027). |

## 2.1.5.12 — Estándares de codificación segura

- Todas las consultas a la base de datos pasan por el ORM de Django
  (`QuerySets`), nunca por SQL concatenado manualmente.
- Configuración sensible (`SECRET_KEY`, credenciales de BD) solo en
  variables de entorno (`.env`), nunca escrita en el código ni subida al
  repositorio.
- `DEBUG=False` obligatorio para el despliegue en EC2, controlado por
  variable de entorno (en desarrollo local se usa `True`).
- Validación de datos en dos capas: a nivel de formulario (`forms.py`,
  `ModelForm`) y a nivel de modelo (`clean()`), para que la regla de
  negocio se cumpla sin importar por dónde se intente guardar el dato.
- Protección CSRF activa por defecto en todos los formularios del
  proyecto.
- Referencia general: OWASP Top 10 como checklist de revisión.


## Auditoría de operaciones críticas (versión 2.1 — RF-036, RNF-008, HU-30)

- **Qué se registra**:
  - Altas, modificaciones y eliminaciones de todas las tablas del SGR.
  - Validaciones y rechazos de evidencia.
  - Inicios de sesión, correctos y fallidos.
  - **Accesos denegados (403)**, con la ruta que se intentó abrir.
- **Qué guarda cada evento**: usuario, IP, fecha, entidad, identificador, valor anterior y valor nuevo (`comun/auditoria.py`).
- **Protección**: el modelo `RegistroAuditoria` rechaza cualquier modificación o eliminación (`save()` y `delete()` lanzan `PermissionDenied`). En Django Admin está en solo lectura incluso para el Administrador.
- **Acceso**: lo consultan solo el Administrador, el Coordinador y el Verificador, en `/auditoria/`. Un Funcionario recibe 403, y ese intento también queda registrado (CP-AUD-003 y CP-AUD-004).
- **Períodos cerrados** (RN-013): sus resultados no se alteran. Reabrir un período queda registrado en la auditoría.


## Revisión de seguridad de noviembre de 2026 (versión 2.2.2)

Como parte de la Evaluación 3 de Ingeniería de Software, el sistema se revisó contra el **OWASP Top 10:2025**:

| Riesgo | Control | Estado |
|---|---|---|
| A01 Control de acceso roto | Permisos por rol y filtro por delegación (404). Prueba CP-SEG-004 | Cumple |
| A02 Configuración insegura | DEBUG=False, ALLOWED_HOSTS, X-Frame-Options, nosniff, Referrer-Policy | Parcial: falta HTTPS y HSTS |
| A03 Fallas en la cadena de suministro | 5 dependencias; revisión con `pip-audit` | Pendiente: ver hallazgo 2 |
| A04 Fallas criptográficas | PBKDF2-SHA256; secretos en `.env` | Parcial: tráfico sin HTTPS |
| A05 Inyección | ORM con SQL parametrizado; plantillas que escapan HTML. Pruebas CP-SEG-001 y 002 | Cumple |
| A06 Diseño inseguro | Nadie valida lo propio; períodos cerrados; tope de 7 ingresos diarios | Cumple |
| A07 Fallas de autenticación | Bloqueo tras 5 intentos; validadores; sesión de 30 minutos | Cumple |
| A08 Integridad de software o datos | CSRF; evidencias JPG, PNG o PDF de hasta 5 MB. Prueba CP-SEG-003 | Cumple |
| A09 Registro y alertas | Auditoría que no se puede modificar; `logs/seguridad.log` | Cumple |
| A10 Condiciones excepcionales | Páginas 403 y 404 propias; la auditoría nunca bloquea la operación | Cumple |

**Hallazgos** (se informan tal como salieron):
1. `python manage.py check --deploy` avisa que faltan HSTS, la redirección a HTTPS y las cookies seguras. El código está listo (`USAR_HTTPS=True` en `.env`); falta instalar un certificado (Nginx con Let's Encrypt o un balanceador de AWS con ACM). **Plan: Sprint 6.**
2. `pip-audit -r requirements.txt` encontró **9 avisos de vulnerabilidad en Django 4.2.30**. La rama 4.2 dejó de recibir correcciones de seguridad en abril de 2026. Para actualizar a **Django 5.2 LTS** se necesita Python 3.10 o superior, y Amazon Linux 2023 trae Python 3.9. **Plan, Sprint 6:**
   1. Instalar Python 3.11 en la instancia (`sudo dnf install python3.11`).
   2. Recrear el `venv`.
   3. Actualizar `requirements.txt` a `Django>=5.2,<5.3`.
   4. Correr las pruebas y desplegar.
