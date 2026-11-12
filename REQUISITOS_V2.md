# Requerimientos por versión — SGR La Serena

Este documento separa los requerimientos según la versión del sistema en que entran. Así se sabe qué pidió la Guía SGR original y qué agregó el documento **Nuevos Requerimientos (octubre 2026)** de la Coordinación de Delegaciones.

| Versión de requerimientos | Fuente | Requisitos | Versión del sistema |
|---|---|---|---|
| **1.0** | *Guía Proyecto Software SGR* (documento maestro del caso) | RF-001 a RF-038, RNF-001 en adelante, HU-01 a HU-27 | 1.0.0 y 1.1.0 |
| **2.0** | *Nuevos Requerimientos — Octubre 2026* | **RF-039 a RF-048**, RN-V2-01 a RN-V2-04, HU-V2-01 a HU-V2-05 | **2.0.0** |

Los requisitos 1.0 siguen vigentes en la versión 2.0, salvo los que la 2.0 **reemplaza** de forma explícita (marcados con ⟳ en la tabla de cambios).

---

## 1. Requisitos nuevos de la versión 2.0

Las prioridades usan la misma escala de la Guía SGR: Alta, Media y Baja.

| ID | Versión | Requisito | Fuente | Prioridad | Criterio de aceptación | Implementación | Prueba |
|---|---|---|---|---|---|---|---|
| **RF-039** | 2.0 | Registrar **organizaciones comunitarias** territoriales (Juntas de Vecinos) y funcionales: Club de Adulto Mayor, Organización Deportiva, Centro de Madres, Centro Cultural, Agrupación Juvenil y Comités de Vecinos, Allegados o Seguridad. Cada actividad puede indicar la organización solicitante. | Encabezado del documento | Media | El Delegado crea organizaciones solo de su delegación. Si el solicitante es una organización, el formulario exige elegir cuál. | `delegaciones/models.py` (`OrganizacionComunitaria`), `delegaciones/views.py`, `gestion/forms.py` | CP-V2-006, CP-V2-016 |
| **RF-040** | 2.0 | Las actividades cuyo solicitante es el **propio Delegado** no se contabilizan: son "otra gestión". | Regla 1 | Alta | Una actividad con solicitante "Delegado" queda como *No suma puntaje* y no aporta al avance. | `Actividad.tipo_solicitante`, `Actividad.motivos_sin_puntaje()` | CP-V2-001 |
| **RF-041** | 2.0 | Las actividades **sin nombre y teléfono del usuario** no tienen puntuación. | Regla 2 | Alta | Sin nombre o sin teléfono, la actividad no suma. Con ambos, sí suma. | `Actividad.motivos_sin_puntaje()` | CP-V2-002 |
| **RF-042** | 2.0 | Máximo **7 ingresos diarios** por funcionario. | Regla 3 | Alta | Con 7 actividades ingresadas hoy, el formulario rechaza la octava. | `ActividadForm.clean()`, `SGR_MAX_INGRESOS_DIARIOS` | CP-V2-004 |
| **RF-043** ⟳ | 2.0 | **Cierre semanal**: la semana (lunes a viernes) se ingresa a más tardar el lunes siguiente; desde el martes ya no. *Reemplaza la regla 1.x de "hasta 7 días atrás".* | Regla 4 | Alta | El lunes se aceptan fechas de la semana anterior. Desde el martes, solo de la semana en curso. Nunca se aceptan fechas futuras. | `inicio_ventana_registro()`, `ActividadForm.clean_fecha()` | CP-V2-005, CP-COD-003 |
| **RF-044** | 2.0 | Las **gestiones previas** (correos, coordinaciones, invitaciones, coordinaciones internas) no dan punto. Solo da punto la **realización** de la acción. | Regla 5 | Alta | Una gestión previa, aunque esté validada, no aporta al avance. | `Actividad.tipo_gestion` | CP-V2-003 |
| **RF-045** ⟳ | 2.0 | **Tope de 120 % por ítem**: pasado ese punto, más gestiones no suben el puntaje. *Reemplaza el tope 1.x de 150 % por ítem.* | Regla 7 | Alta | Con 4 actividades validadas sobre una meta de 2, el ítem queda en 120 %. | `gestion/indicadores.py`, `SGR_TOPE_ITEM` | CP-V2-008, CP-CUM-002 |
| **RF-046** | 2.0 | **Felicitaciones y reclamos** los registra **solo el Delegado**, con respaldo formal. Cada felicitación suma 10 puntos (máx. 3 por período) y cada reclamo resta 20. El total del colaborador queda entre 0 y 150 %. | Regla 8 + pestaña "Reclamos" de la matriz de referencia | Media | El Funcionario recibe 403 al intentar registrar. Se rechaza una 4.ª felicitación. Los puntos se ven en el panel. | `organizacion/models.py` (`Reconocimiento`), `organizacion/views.py` | CP-V2-009, CP-V2-010, CP-V2-012, CP-V2-013 |
| **RF-047** | 2.0 | **Ausencias** (días libres, vacaciones, días administrativos, licencias) las ingresa el Delegado y **ajustan la meta esperada** del semáforo. | Regla 9 | Media | Esperado = (días transcurridos − ausencias a la fecha) / (días del período − ausencias del período). No se aceptan ausencias cruzadas. | `organizacion/models.py` (`Ausencia`), `porcentaje_esperado_funcionario()` | CP-V2-011, CP-V2-014, CP-V2-015 |
| **RF-048** | 2.0 | **Versionar las reglas**: cada actividad guarda la versión de requerimientos con que se registró. Las reglas nuevas no cambian el puntaje de actividades anteriores. | Pedido del profesor: "diferenciar entre versiones" | Alta | Una actividad 1.0 sin teléfono sigue sumando; una 2.0 sin teléfono, no. | `Actividad.version_reglas`, migración `gestion/0007_reglas_v2` | CP-V2-007 |

### Reglas de negocio 2.0

| ID | Regla | Dónde se aplica |
|---|---|---|
| RN-V2-01 | Una actividad **suma al avance** solo si está validada por el Delegado **y** es puntuable: realización, solicitante distinto del Delegado, con nombre y teléfono del usuario. | `Actividad.suma_al_avance`, `cumplimiento_funcionario()` |
| RN-V2-02 | Cumplimiento del colaborador = ponderado de sus metas (cada ítem con tope de 120 %) + 10 × felicitaciones (máx. 3) − 20 × reclamos. El resultado queda acotado entre 0 y 150 %. | `gestion/indicadores.py` |
| RN-V2-03 | La meta esperada al día descuenta las ausencias del funcionario. | `porcentaje_esperado_funcionario()` |
| RN-V2-04 | Los puntajes se ven **como equipo**: el cumplimiento de la delegación es el promedio de sus funcionarios operativos (regla 10). | `cumplimiento_delegacion()` (ya existía en 1.1; se mantiene) |

La **regla 6** ("no ingresar solo para generar puntaje") es una indicación de conducta. El sistema la apoya con las reglas RF-040 a RF-044 y con la validación del Delegado, pero no puede verificarla de forma automática.

### Historias de usuario 2.0

| ID | Historia | Requisitos |
|---|---|---|
| HU-V2-01 | Como **Funcionario**, quiero saber al registrar si mi actividad sumará puntaje y por qué, para ingresar solo lo que corresponde. | RF-040, RF-041, RF-044 |
| HU-V2-02 | Como **Coordinación**, quiero limitar a 7 ingresos diarios y cerrar cada semana el lunes, para que la matriz se llene a diario y no al final. | RF-042, RF-043 |
| HU-V2-03 | Como **Delegado**, quiero registrar felicitaciones y reclamos con su respaldo, para que se reflejen en el cumplimiento de mi equipo. | RF-046 |
| HU-V2-04 | Como **Delegado**, quiero ingresar las ausencias de mi equipo, para que el semáforo no los muestre atrasados por días que no trabajaron. | RF-047 |
| HU-V2-05 | Como **Delegado**, quiero registrar las organizaciones comunitarias de mi territorio y saber cuál solicitó cada actividad. | RF-039 |

---

## 2. Cambios respecto a la versión 1.x

| Tema | Versión 1.x | Versión 2.0 |
|---|---|---|
| Registro hacia atrás | Hasta 7 días atrás (`SGR_DIAS_REGISTRO_RETROACTIVO`) | Cierre semanal: hasta el lunes siguiente (RF-043) |
| Tope de cumplimiento | 150 % por ítem | **120 % por ítem** (RF-045); 150 % como máximo total del colaborador |
| Qué suma al avance | Toda actividad validada | Actividad validada **y puntuable** (RN-V2-01) |
| Ingresos por día | Sin límite | Máximo 7 (RF-042) |
| Meta esperada | Días transcurridos / días del período | Descuenta las ausencias (RF-047) |
| Ajustes al puntaje | No había | Felicitaciones +10 y reclamos −20 (RF-046) |
| Solicitante | Texto libre (contacto) | Vecino / Organización / Delegado, más el catálogo de organizaciones (RF-039) |

**Compatibilidad**: las actividades registradas antes de la 2.0 quedan con `version_reglas = "1.0"` y conservan su puntaje (RF-048).

---

## 3. Material recibido y alcance

| Documento | Uso en la versión 2.0 |
|---|---|
| *Nuevo Requerimientos Octubre 2026* (Word) | **Fuente** de RF-039 a RF-048. |
| *Descriptor de funciones* (Word) | Referencia para los cargos y áreas. No cambia el modelo: los cargos y su área ya existen en `CargoFuncion` desde la 1.1. |
| *Matriz SGR de una delegación* (Excel) | **Solo referencia, no se trabaja** (indicación del profesor). De ahí se tomaron los valores de felicitaciones (+10, máx. 3) y reclamos (−20). |
| *Base de datos de JJVV "sin verificar"* (Excel) | **En espera**: no se importa hasta que esté verificada. El catálogo de organizaciones (RF-039) ya tiene los mismos campos (domicilio, socios activos, fecha de constitución, N° de personalidad jurídica) para cargarla después. |
