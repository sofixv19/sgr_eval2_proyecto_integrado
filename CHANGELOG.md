# Historial de versiones — SGR La Serena

El proyecto usa **versionado semántico** (`MAYOR.MENOR.PARCHE`):

- **MAYOR** cambia cuando cambian los requerimientos del cliente (la Municipalidad). La 2.0 corresponde al documento *Nuevos Requerimientos, octubre 2026*.
- **MENOR** cambia con funciones nuevas o correcciones pedidas en una revisión, sin cambiar los requerimientos base.
- **PARCHE** cambia con arreglos chicos.

La versión vigente se ve en el pie de cada página y está en `SGR_VERSION` (`sgr_evaluacion/settings.py`). Cada versión queda marcada en Git con un *tag* (`v1.0`, `v1.1`, `v2.0`, `v2.1`, `v2.1.1`, `v2.1.2`, `v2.2`, `v2.2.1`, `v2.2.2`, `v2.2.3`, `v3.0`, `v3.0.1`).

| Versión | Fecha | Base de requerimientos | Pruebas |
|---|---|---|---|
| [3.0.1](#301--transiciones-suaves-y-mensajes-que-se-cierran-solos) | 24-11-2026 | Observación del equipo (interfaz) | 217 |
| [3.0.0](#300--solución-completa-guía-pi-evaluación-3) | 26-11-2026 | Guía PI Evaluación 3 (alcance funcional mínimo) | 217 |
| [2.2.3](#223--pruebas-de-seguridad) | 16-11-2026 | Pedido del docente: demostrar la seguridad con código | 180 |
| [2.2.2](#222--diagramas-y-seguridad-al-día) | 14-11-2026 | Evaluación 3 de Ingeniería de Software | 176 |
| [2.2.1](#221--los-cambios-hechos-desde-la-página-se-respetan) | 12-11-2026 | Error reportado por el equipo | 176 |
| [2.2.0](#220--interfaz-más-ordenada) | 12-11-2026 | Revisión visual del equipo | 175 |
| [2.1.2](#212--datos-de-demostración-limpios) | 12-11-2026 | Ajuste tras revisión del equipo | 175 |
| [2.1.1](#211--menú-más-simple) | 12-11-2026 | Ajuste tras revisión del equipo | 174 |
| [2.1.0](#210--alcance-mínimo-completo-de-la-guía-sgr) | 12-11-2026 | Guía SGR (MVP completo) + Nuevos Requerimientos | 174 |
| [2.0.0](#200--nuevos-requerimientos-octubre-2026) | 12-11-2026 | Guía SGR + Nuevos Requerimientos (octubre 2026) | 156 |
| [1.1.0](#110--correcciones-de-la-revisión-de-la-evaluación-2) | 05-11-2026 | Guía SGR + retroalimentación del profesor | 140 |
| [1.0.0](#100--evaluación-2-de-proyecto-integrado) | 22-10-2026 | Guía SGR (RF-001 a RF-038) | 118 |

---

## 3.0.1 — Transiciones suaves y mensajes que se cierran solos

Observación del equipo: al cambiar de página o abrir un menú todo aparecía de golpe, y los mensajes ("Bienvenido/a…", "Actividad registrada…") quedaban pegados arriba.

- **Cambio de página**: fundido suave del contenido; la barra superior queda quieta (View Transitions en Chrome, Edge y Brave; fundido de entrada en los demás navegadores).
- **Menús desplegables y autocompletar**: se abren con un fundido corto.
- **Mensajes del sistema**: tarjetas flotantes arriba a la derecha (abajo en el celular) que se cierran solas: éxito e información 4,5 s, aviso 7 s, error 9 s. Una barra muestra el tiempo que queda; con el mouse encima esperan; la X los cierra al tiro.
- Quien tiene activado "reducir movimiento" en su equipo no ve animaciones (accesibilidad).
- Archivos: `static/css/custom.css`, `static/js/sgr.js`, `templates/base.html`. Sin cambios en la base de datos. 217 pruebas aprobadas.

## 3.0.0 — Solución completa (Guía PI Evaluación 3)

Cambio MAYOR porque la Guía de la Evaluación 3 agrega requerimientos al alcance funcional mínimo.

**Cuentas y seguridad**
- Contraseña temporal con **cambio obligatorio en el primer ingreso** (`cuentas/models.py: EstadoCuenta`, `CambioClaveObligatorioMiddleware`). Pruebas CP-CLA-001 a 003 y 008.
- **Recuperación de contraseña por correo** con enlace de un solo uso que **vence en una hora** (`PASSWORD_RESET_TIMEOUT`). La respuesta es la misma exista o no el correo. Pruebas CP-CLA-004 a 007.
- El cambio y la recuperación de contraseña quedan en la auditoría ("Cambio de clave").

**Verificación**
- Nuevo estado **"Se solicitan más antecedentes"**: el Delegado pide antecedentes con una observación; al completarlos, el registro vuelve a "Pendiente". Pruebas CP-VER-001 a 003.
- **Un registro aprobado no se modifica ni se elimina**, tampoco el Administrador (antes el Administrador sí podía). Prueba CP-VER-004.

**Catálogos y comunidad (app nueva `territorio`)**
- CRUD con validaciones de **territorios**, **vecinos** (RUT validado y único), **socios y dirigentes** de juntas de vecinos (un cargo vigente por organización), **hitos** con responsable y **tipos y subtipos de atención**. Los períodos de medición pasan a llamarse **trimestres**. Pruebas CP-COM-001 a 010.
- **Autocompletar**: al escribir el RUT o el nombre del vecino se completan su nombre y teléfono (`/territorio/vecinos/buscar/`).

**Registros y Tubo**
- **Gestiones sociales**: mismo flujo que la actividad (código GS-0001, evidencia, verificación y metas), con vecino y tipo/subtipo de atención. Pruebas CP-GSO-001 a 005 (la 005 cubre el defecto INC-13: el compromiso hereda el territorio del vecino).
- Al registrar una actividad o gestión social se puede **ingresar o no al Tubo** (casilla "Ingresar también al Tubo").
- **Tubo de cartas** por delegación (código TC-0001): todos lo ven; cada funcionario modifica solo lo suyo mientras no esté aprobado; solo el Delegado aprueba o finaliza. Pruebas CP-TUB-001 a 004.
- **Búsqueda dinámica mientras se escribe** en el Tubo de seguimiento y en el Tubo de cartas, por código, RUT o nombre del solicitante. Prueba CP-TUB-005. El listado también busca por RUT y nombre del vecino.

**Dashboard**
- Página **Dashboard** con filtros (trimestre, delegación, funcionario, verificación y fechas) y gráficos de cumplimiento por funcionario y por delegación (semáforo), tendencia semanal, carga de trabajo, estado de los compromisos y verificación. Chart.js 4.4.4 servido desde `static/js` (sin CDN). Pruebas CP-DAS-001 a 003.

**Base de datos y entorno**
- Índices para búsquedas frecuentes en actividades (delegación+fecha, funcionario+fecha, estado de validación) y en RUT y nombres.
- Comandos `respaldar` y `restaurar` (base de datos + evidencias en un .zip). Pruebas CP-RES-001 y 002.
- Correo configurable en `.env` (por defecto se guarda en `logs/correos/`).
- `INCIDENCIAS.md`: registro de incidencias de configuración resueltas. `CONTRIBUTING.md`: flujo de ramas y *pull requests* del equipo.

**Total: 217 pruebas automatizadas, todas aprobadas; flake8 sin observaciones.**

---

## 2.2.3 — Pruebas de seguridad

El docente pidió demostrar con código los controles que no se ven en la pantalla. Se agregaron cuatro pruebas en `gestion/tests_seguridad.py`:
- **CP-SEG-001 (inyección SQL, OWASP A05):** una búsqueda con `' OR 1=1 --` responde sin registros de más. La prueba revisa además que el texto viaja como parámetro (`%s`) y nunca pegado dentro del SQL.
- **CP-SEG-002 (XSS, A05):** una descripción con `<script>` se muestra escapada.
- **CP-SEG-003 (CSRF, A08):** un formulario enviado sin token se rechaza con 403.
- **CP-SEG-004 (control de acceso, A01):** el filtro por ámbito deja al Funcionario solo con lo suyo, y la ficha de otra delegación responde 404.

El código de la aplicación no cambia. Total: 180 pruebas.

---

## 2.2.2 — Diagramas y seguridad al día

Solo cambia la documentación; el código de la aplicación no cambia.

### Cambiado
- **Diagramas actualizados al código**, en `docs/diagramas/` (imagen y fuente Mermaid editable):
  - clases de diseño;
  - modelo entidad-relación de las 15 tablas;
  - estados de la actividad y del compromiso;
  - componentes.
- Los diagramas de la Evaluación 2 eran un modelo conceptual: clases Indicador y Validacion, subclases por rol y el estado "Observada". Ya no coincidían con lo construido.
- `DIAGRAMA_CLASES.md` y `MODELO_DATOS.md` muestran primero el diagrama actualizado.
- `SEGURIDAD.md`:
  - se reescribió la sección de autenticación y autorización, que todavía decía que el sitio no tenía inicio de sesión;
  - se agregó la revisión OWASP Top 10:2025 con sus hallazgos (falta HTTPS; `pip-audit` encontró 9 avisos en Django 4.2.30, que se resolverán migrando a Django 5.2 LTS en el Sprint 6).

---

## 2.2.1 — Los cambios hechos desde la página se respetan

### Corregido
- **Error:** el equipo cambió los nombres de los funcionarios desde la página. Después de instalar una versión nueva volvieron a aparecer los nombres antiguos.
  - **Causa:** cada instalación corre `cargar_datos_iniciales`, que hacía `update_or_create` y volvía a escribir el nombre, el RUT, la delegación, el cargo y el rol de los funcionarios de ejemplo. Lo mismo pasaba con los datos de las delegaciones y las metas por cargo.
  - **Corrección:** ahora solo **crea lo que falta** y nunca modifica lo que ya existe.
- Los funcionarios y delegaciones de ejemplo se reconocen por su **correo o RUT**, no por su nombre. Así, un nombre cambiado no genera duplicados.
- `reiniciar_demo` conserva los nombres que el equipo les haya puesto a los funcionarios y delegaciones de ejemplo. Sigue borrando los datos de prueba.
- Prueba nueva: CP-DEM-002.

---

## 2.2.0 — Interfaz más ordenada

El equipo encontró los paneles difíciles de leer. Ahora los tres paneles (Funcionario, Delegado y Coordinador/Administrador/Verificador) siguen el mismo orden.

### Cambiado
1. **Encabezado** con el nombre, los datos clave y el selector de período. Los botones salen del encabezado.
2. **Indicadores**: cuatro tarjetas compactas en una sola fila.
3. **Accesos rápidos**, en dos tarjetas:
   - **Registrar y gestionar**: lo que el rol puede hacer, como botones grandes.
   - **Consultar información**: lo que puede revisar, como una grilla de botones.
   - Cada rol ve solo sus opciones. El Verificador ve "Descargar informes", porque es de solo lectura.
4. **Cumplimiento y Avisos** lado a lado. Los avisos están en una tarjeta compacta: se ven 4 y el resto se despliega con "Ver más".
5. **Detalle**: metas, evidencias pendientes y tablas, igual que antes.

### Otros cambios
- El aviso amarillo de "delegaciones sin Delegado" pasó a la tabla de cumplimiento por delegación.
- En el teléfono, todo queda en una columna.
- Sin cambios de base de datos ni de permisos.

---

## 2.1.2 — Datos de demostración limpios

### Cambiado
- **Equipo de ejemplo más pequeño y coherente** (`cargar_datos_iniciales`):
  - **Rural:** Delegado C. Araya (`delegado.rural`), F. Contreras (`funcionario.rural`) y L. Tapia.
  - **Centro:** Delegado S. Pizarro y J. Herrera.
  - Las otras cuatro delegaciones quedan sin equipo.
  - Se quitaron los tres funcionarios de la Evaluación 1 con rol "Coordinador" dentro de una delegación. El Coordinador es un rol transversal (`coordinador.sgr`).
- `data/actividades.json` tiene 7 actividades del nuevo equipo. Las realizadas quedan validadas por su Delegado, y las pendientes traen un PDF de evidencia ficticio para poder mostrar la validación.
- Los compromisos de ejemplo se reparten entre los funcionarios de la delegación, para que se vea el resumen por responsable.

### Agregado
- Comando **`reiniciar_demo --confirmar`**:
  - Borra lo creado probando el sistema (actividades, evidencias, compromisos, metas, felicitaciones, ausencias, funcionarios y cuentas de prueba, delegaciones extra y períodos de prueba).
  - Vuelve a cargar el equipo de ejemplo.
  - Conserva las 5 cuentas demo **con su contraseña**.
  - Deja en la auditoría un registro del reinicio.
  - Es solo para el ambiente de demostración.
- Prueba CP-DEM-001.

---

## 2.1.1 — Menú más simple

### Quitado
- Página **"Resumen de gestión"** (`/gestion/resumen/`), de la versión 1.0. Solo contaba las actividades por estado, y eso ya lo muestran los paneles de cada rol. Se quitó del menú del Coordinador, del Administrador y del Verificador.
- El **resumen colectivo por responsable** de la Agenda **se mantiene**, porque lo exige RF-021 / HU-14.

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
