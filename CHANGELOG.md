# Historial de versiones — SGR La Serena

El proyecto usa **versionado semántico** (`MAYOR.MENOR.PARCHE`):

- **MAYOR** cambia cuando cambian los requerimientos del cliente (la Municipalidad). La 2.0 corresponde al documento *Nuevos Requerimientos, octubre 2026*.
- **MENOR** cambia con funciones nuevas o correcciones pedidas en una revisión, sin cambiar los requerimientos base.
- **PARCHE** cambia con arreglos chicos.

La versión vigente se ve en el pie de cada página y está en `SGR_VERSION` (`sgr_evaluacion/settings.py`). Cada versión queda marcada en Git con un *tag* (`v1.0`, `v1.1`, `v2.0`).

| Versión | Fecha | Base de requerimientos | Pruebas |
|---|---|---|---|
| [2.1.0](#210--alcance-mínimo-completo-de-la-guía-sgr) | 12-11-2026 | Guía SGR (MVP completo) + Nuevos Requerimientos | 174 |
| [2.0.0](#200--nuevos-requerimientos-octubre-2026) | 12-11-2026 | Guía SGR + Nuevos Requerimientos (octubre 2026) | 156 |
| [1.1.0](#110--correcciones-de-la-revisión-de-la-evaluación-2) | 05-11-2026 | Guía SGR + retroalimentación del profesor | 140 |
| [1.0.0](#100--evaluación-2-de-proyecto-integrado) | 22-10-2026 | Guía SGR (RF-001 a RF-038) | 118 |

---

## 2.1.0 — Alcance mínimo completo de la Guía SGR

Completa el **alcance mínimo recomendado (MVP)** de la Guía SGR, sección 13.2. Son requisitos de la versión 1.0 de los requerimientos que no se habían implementado. Cobertura completa en `REQUISITOS_V2.md`, sección 4.

### Agregado
- **Agenda colectiva o "tubo de trabajo"** (RF-016 a RF-021, HU-12 a HU-15), en `gestion/agenda/`:
  - Compromisos con solicitante, territorio, responsable, área de apoyo y fecha comprometida. Código AC-0001.
  - Estados Ingresado → Pendiente → En proceso → Realizado, con transiciones controladas e **historial** (estado anterior, nuevo, autor, fecha y observación).
  - Destaca los compromisos **próximos a vencer** (amarillo) y **vencidos** (rojo), y los realizados fuera de plazo.
  - Filtros por responsable, estado, situación, territorio y fechas, más un **resumen colectivo por responsable** (% realizado y % pendiente).
  - El Delegado **reasigna** compromisos (por ejemplo, por licencia) dejando el motivo en el historial.
  - Relación con la medición: una actividad puede **originar** un compromiso, o **cumplirlo** (lo cierra una sola vez).
- **Auditoría** (RF-036, HU-30, CA-09), en `auditoria/`:
  - Registra altas, modificaciones, eliminaciones, validaciones, rechazos, inicios de sesión y **accesos denegados**.
  - Cada evento guarda usuario, IP, fecha, valor anterior y valor nuevo.
  - Es de solo lectura, incluso para el Administrador. La consultan el Administrador, el Coordinador y el Verificador.
- **Exportación a Excel (CSV)** (RF-033, HU-20): de actividades, agenda colectiva y cumplimiento por funcionario (con la fórmula). Respeta los filtros y el ámbito, e incluye la fecha de generación.
- **Filtros de actividades** (RF-032, HU-29): por delegación, funcionario, ítem, período y rango de fechas.
- **Consulta de períodos anteriores** en los tres paneles (RF-008, RF-028).
- **Períodos cerrados protegidos** (RN-013, CA-10): no se registra, edita, elimina ni valida nada en un período cerrado.
- **Actividad reciente** por funcionario en el panel del Delegado (RF-030): último ingreso, días sin ingreso, registros y promedio diario.
- **Alertas** en los paneles (RF-037): compromisos vencidos o por vencer, evidencias pendientes, actividades rechazadas, funcionarios sin registros y avance bajo el umbral.
- **Parámetros configurables**: umbral ámbar del semáforo (RN-008), umbral colectivo (RN-006), días de aviso y días sin registro.
- Compromisos de ejemplo en `cargar_datos_iniciales`.
- 18 pruebas nuevas (`gestion/tests_v21.py`: CP-AGE, CP-AUD, CP-EXP, CP-PCE, CP-FIL y CP-ALE).
- `MANUAL_USUARIO.md` y `MATRIZ_TRAZABILIDAD.md`.

### Migraciones
- `gestion/0008_agenda_colectiva`.
- `comun/0001_auditoria`.
- Al actualizar: `migrate`, `configurar_roles`, `collectstatic`.

---

## 2.0.0 — Nuevos requerimientos (octubre 2026)

Requisitos nuevos **RF-039 a RF-048** (detalle y trazabilidad en `REQUISITOS_V2.md`).

### Agregado
- **Organizaciones comunitarias** (RF-039), en `delegaciones/organizaciones/`:
  - Las Juntas de Vecinos son las organizaciones territoriales.
  - También se registran las funcionales: Club de Adulto Mayor, Organización Deportiva, Centro de Madres, Centro Cultural, Agrupación Juvenil, Comité de Vecinos, Comité de Allegados y Comité de Seguridad.
  - Una actividad puede indicar qué organización la solicitó.
- **Reglas de puntaje por actividad**: cada actividad muestra si **suma o no suma puntaje** y por qué. No suman:
  - las que solicitó el propio Delegado (RF-040);
  - las que no tienen nombre y teléfono del usuario (RF-041);
  - las gestiones previas: coordinaciones, correos e invitaciones. Solo puntúa la realización de la acción (RF-044).
- **Máximo 7 ingresos diarios** por funcionario (RF-042).
- **Cierre semanal** (RF-043): la semana de lunes a viernes se puede ingresar hasta el lunes siguiente. Desde el martes queda cerrada.
- **Felicitaciones y reclamos** (RF-046), en `organizacion/felicitaciones/`:
  - Los registra solo el Delegado, con respaldo formal.
  - Cada felicitación suma +10 (máximo 3 por período) y cada reclamo resta −20.
- **Ausencias** (RF-047), en `organizacion/ausencias/`: licencias, vacaciones, días administrativos y días libres. Las registra el Delegado y se descuentan del período para ajustar la meta esperada del semáforo.
- **Versión de reglas por actividad** (RF-048): cada actividad guarda con qué versión de requerimientos se registró. Las reglas 2.0 **no se aplican hacia atrás**.
- Menú **"Mi equipo"** del Delegado, con felicitaciones, ausencias y organizaciones.
- La versión del sistema se muestra en el pie de página.
- 16 pruebas nuevas (`gestion/tests_v2.py`, casos CP-V2-001 a CP-V2-016).
- Documentos `REQUISITOS_V2.md` y `CHANGELOG.md`.

### Cambiado
- **Tope por ítem: 150 % → 120 %** (RF-045). El 150 % queda como máximo del total del colaborador, contando felicitaciones (`SGR_TOPE_ITEM`, `SGR_TOPE_CUMPLIMIENTO`).
- Registro hacia atrás: **"hasta 7 días atrás" (1.x) → cierre semanal (2.0)**. Se eliminó el parámetro `SGR_DIAS_REGISTRO_RETROACTIVO`.
- Las pruebas CP-CUM-002 y CP-COD-003 se actualizaron a las reglas 2.0.

### Migraciones
- `delegaciones/0003_organizaciones_comunitarias`.
- `organizacion/0008_felicitaciones_ausencias`.
- `gestion/0007_reglas_v2`: las actividades existentes quedan con `version_reglas = "1.0"`.
- Al actualizar un servidor hay que correr `migrate`, `configurar_roles` (permisos nuevos) y `collectstatic`.

### No incluido en esta versión
- **Base de datos de JJVV "sin verificar"**: no se importa, porque está pendiente de verificación. El catálogo de organizaciones queda listo para recibirla.
- **Planilla Matriz SGR (Excel) que el profesor mostró en clases**: el equipo la usó solo como referencia. No se trabajó sobre ese archivo.

---

## 1.1.0 — Correcciones de la revisión de la Evaluación 2

Cambios pedidos por el profesor Caiceo en la revisión de la página (audio del 04-11-2026).

### Agregado
- **Ámbito por rol**:
  - El Funcionario ve solo sus actividades.
  - El Delegado ve solo su delegación y su equipo, y no modifica actividades.
  - El Coordinador gestiona las delegaciones y crea a los Delegados.
  - El Administrador es aparte.
- **Cuenta de acceso ligada al registro del funcionario**, con entrega de credenciales temporales.
- **Código de actividad automático por área**: TR-0001, SO-, OC-, DI-, SE-, AD-, PC-.
- **Datos automáticos al registrar**: fecha, estado Pendiente, delegación y funcionario.
- **Evidencias** (foto o PDF de hasta 5 MB) y **validación del Delegado** (validada / rechazada con observación / pendiente).
- **Metas por funcionario y período** (las asigna el Delegado), con **cumplimiento ponderado y semáforo**.
- **Panel distinto por rol** (Funcionario, Delegado y Coordinador), con indicador circular, tarjetas y línea de tiempo.
- 22 pruebas nuevas (`gestion/tests_roles.py`).

---

## 1.0.0 — Evaluación 2 de Proyecto Integrado

- Inicio de sesión obligatorio, con bloqueo temporal tras 5 intentos fallidos.
- Mantenedores (CRUD) de delegaciones, funcionarios, cargos, metas, categorías y períodos.
- Roles (Administrador, Coordinador, Delegado, Funcionario y Verificador) con permisos mínimos.
- Despliegue en AWS EC2 con MariaDB.
- 118 pruebas unitarias con matriz de resultados (`plan_pruebas.py`).
