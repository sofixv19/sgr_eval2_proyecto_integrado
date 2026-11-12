# Seguridad — SGR La Serena

Cubre los criterios **2.1.5.10** (autenticación y autorización),
**2.1.5.11** (amenazas y mitigación) y **2.1.5.12** (estándares de
codificación segura) de la rúbrica de Evaluación 2.

## 2.1.5.10 — Políticas de autenticación y autorización

**Autenticación**: el sistema usa el mecanismo propio de Django
(`django.contrib.auth`). Las contraseñas nunca se guardan en texto
plano, sino con hash (PBKDF2) manejado automáticamente por el framework.
El acceso a Django Admin exige una sesión iniciada con permisos de
`staff` o `superuser`.

**Autorización — dos niveles, documentados de forma honesta**:

| Nivel | Cómo se protege hoy | Alcance |
|---|---|---|
| Django Admin | Login real + permisos de `staff`/`superuser` de Django | Control total: crear, editar, eliminar y validar cualquier entidad. |
| Regla de negocio (modelo) | `Actividad.clean()` / `marcar_validado()` impiden que alguien sin rol Delegado valide, o que el Delegado se autovalide | Se aplica siempre, incluso si el dato se intenta guardar desde Admin, desde el formulario público o desde una prueba automatizada. |
| Formularios públicos (`/gestion/`, `/delegaciones/`) | **Sin login todavía** — son formularios abiertos, no restringidos por sesión de usuario | Limitación declarada (ver también `CASOS_DE_USO.md`, CU-16/CU-17): un sistema de login por rol para el sitio público es el siguiente paso natural, fuera del alcance actual. |

Roles definidos en `Funcionario.rol` (principio de mínimo privilegio, en
la medida de lo ya implementado):

| Rol | Qué puede hacer hoy, en el código real |
|---|---|
| Funcionario Operativo | Registrar y actualizar sus propias actividades (CRUD público). |
| **Delegado** | Lo mismo que el Funcionario Operativo, **más**: validar actividades de su delegación — nunca las que él mismo registró (única acción con control de autorización aplicado a nivel de datos). |
| Coordinador Estratégico | Rol reservado en el catálogo para supervisión de varias delegaciones; sin funciones adicionales implementadas aún en el código (ver `CRONOGRAMA.md`, Sprint 5). |
| Verificador / Auditor | Solo lectura de todo el sistema, incluida la auditoría (versión 2.1). |
| Administrador (staff Django) | Control total desde Django Admin: catálogos, cargos, metas, usuarios, y acción masiva "Marcar como validadas". |

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
| Acceso al sitio público sin autenticación (limitación declarada) | Mientras no exista login por rol para el sitio público, cualquiera con la URL puede registrar o editar actividades. Mitigación parcial actual: el despliegue está pensado para una red interna/instancia controlada (EC2 con `ALLOWED_HOSTS` restringido), no expuesto como sitio público masivo. |
| Exposición de datos personales (RUT, email) en reportes | Pendiente de revisión conforme a la Ley N.º 19.628 sobre protección de datos personales, antes de un despliegue con datos reales (no ficticios) de funcionarios. |

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
