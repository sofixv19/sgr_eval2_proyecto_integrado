# Plan de pruebas — SGR La Serena

Cubre los criterios **2.1.6.13** (pruebas unitarias, integrales y de
rendimiento) y **2.1.6.14** (herramientas automatizadas y manuales) de la
rúbrica de Evaluación 2, y responde al pedido del profesor Ciceo de un
plan de pruebas "con evidencia" para la segunda prueba de Proyecto
Integrado.

## Cómo ejecutarlas

```powershell
python manage.py test
```

Para ver cada prueba individual (nombre + resultado), con más detalle:

```powershell
python manage.py test -v 2
```

El runner de Django crea una base de datos de prueba aparte (no toca los
datos reales), la usa para todas las pruebas (156 en la versión 2.0) y la
destruye al terminar. Para generar la matriz de resultados con el ID de cada
caso (`resultados_pruebas.csv`):

```powershell
python plan_pruebas.py
```

## Alcance del plan

| Tipo de prueba | Qué valida | Dónde |
|---|---|---|
| Unitarias de modelo | Relaciones (`ForeignKey`), `unique`, generación de `slug`, `on_delete` (CASCADE/PROTECT/RESTRICT) | `delegaciones/tests.py`, `gestion/tests.py`, `organizacion/tests.py` |
| Unitarias de regla de negocio | Validación de actividades: solo un Delegado valida, no autovalidación, no validación entre pares (`Actividad.clean()` y `marcar_validado()`) | `gestion/tests.py::ActividadValidacionTests` |
| Integrales de vistas (HTTP) | Listados, filtros (`?estado=`), búsqueda (`?q=`), páginas de detalle, errores 404 | `delegaciones/tests.py::DelegacionVistasTests`, `gestion/tests.py::ActividadVistasTests` |
| Integrales de CRUD real | Crear/editar/eliminar Delegación y Actividad mediante los formularios reales (ya no son marcadores de posición) | `delegaciones/tests.py::DelegacionCrudTests`, `gestion/tests.py::ActividadCrudTests` |
| Integrales del flujo de validación | El formulario de validación en la vista de detalle: se muestra solo si falta validar, rechaza autovalidación, guarda correctamente cuando el Delegado es válido | `gestion/tests.py::ActividadValidacionVistaTests` |

**Total en la primera versión de este documento: 41 pruebas, 4 apps, 0 fallos.**

## Pruebas por versión del sistema

| Versión | Casos agregados | Archivo | Total acumulado |
|---|---|---|---|
| 1.0.0 | CP-ACC, CP-LOGIN, CP-ROL, CP-DEL, CP-FUN, CP-CAR, CP-MET, CP-PER, CP-ACT, CP-VLD, etc. | `*/tests.py` | 118 |
| 1.1.0 | CP-PERF-001 a 010, CP-COD-001 a 003, CP-EVI-001 a 005 y CP-CUM-001 a 004 | `gestion/tests_roles.py` | 140 |
| 2.0.0 | CP-V2-001 a CP-V2-016 | `gestion/tests_v2.py` | 156 |
| 2.1.0 | CP-AGE-001 a 007, CP-AUD-001 a 004, CP-EXP-001 y 002, CP-PCE-001, CP-FIL-001, CP-ALE-001 a 003 | `gestion/tests_v21.py` | 174 |
| 2.1.2 | CP-DEM-001 (reinicio de los datos de demostración) | `gestion/tests_v21.py` | 175 |
| 2.2.1 | CP-DEM-002 (instalar de nuevo no revierte los nombres cambiados) | `gestion/tests_v21.py` | 176 |
| 2.2.3 | CP-SEG-001 a 004 (inyección SQL, XSS, CSRF y control de acceso) | `gestion/tests_seguridad.py` | 180 |
| **3.0.0** | **CP-CLA-001 a 008** (contraseña temporal y recuperación), **CP-VER-001 a 004** (más antecedentes, bloqueo de lo aprobado), **CP-COM-001 a 010** (territorios, vecinos, socios y dirigentes, hitos, tipos de atención, autocompletar), **CP-GSO-001 a 005** (gestiones sociales e ingreso al Tubo), **CP-TUB-001 a 005** (Tubo de cartas y búsqueda dinámica), **CP-DAS-001 a 003** (dashboard), **CP-RES-001 y 002** (respaldo) | `cuentas/tests_v3.py`, `gestion/tests_v3.py`, `territorio/tests.py` | **217** |

El **protocolo de pruebas completo** de la versión 3.0 (cada caso con requerimiento, prioridad, precondiciones, perfil, datos, pasos, resultado esperado y obtenido, responsable, fecha, evidencia, defecto, corrección y reejecución), el **registro de defectos** y los **indicadores** están en `docs/pruebas/Protocolo_Pruebas_SGR_v3.xlsx`.

| Archivo | Contenido |
|---|---|
| `docs/pruebas/Protocolo_Pruebas_SGR_v3.xlsx` | Hojas Resumen, Plan, Indicadores, Protocolo (217 automáticas), Protocolo manual (12), Defectos y Ejecuciones |
| `docs/pruebas/generar_protocolo.py` | Regenera la planilla desde `resultados_pruebas.csv` y `resultados_manuales.json` |
| `docs/pruebas/protocolo_manual.js` | Ejecuta el protocolo manual en Chromium: `SGR_URL=http://127.0.0.1:8000 SGR_CLAVE_DEMO=<clave demo> node docs/pruebas/protocolo_manual.js` (necesita los datos de demostración) |
| `docs/pruebas/evidencias/` | Capturas MAN-01 a MAN-12 |
| `docs/pruebas/ejecuciones/` | Registro de las 4 ejecuciones del protocolo manual y de la suite automática |

Pasos para repetir todo: `python plan_pruebas.py` → `python docs/pruebas/generar_protocolo.py`. Las claves de prueba nuevas se generan al azar en cada corrida y no se guardan.

En la versión 2.0 se **actualizaron** dos casos de la 1.x porque su regla cambió:

- **CP-CUM-002**: el tope por ítem pasa de 150 % a 120 % (RF-045).
- **CP-COD-003**: el plazo de "7 días atrás" pasa a cierre semanal (RF-043).

### Casos de la versión 2.0

| Caso | Requisito | Qué verifica |
|---|---|---|
| CP-V2-001 | RF-040 | Solicitante Delegado → no suma puntaje |
| CP-V2-002 | RF-041 | Sin nombre o teléfono del usuario → no suma; con ambos, sí |
| CP-V2-003 | RF-044 | Gestión previa validada no aporta al avance |
| CP-V2-004 | RF-042 | La 8.ª actividad del día se rechaza |
| CP-V2-005 | RF-043 | Cierre semanal: el lunes se ingresa la semana anterior; el martes, no |
| CP-V2-006 | RF-039 | Si solicita una organización, hay que elegirla |
| CP-V2-007 | RF-048 | Actividades con reglas 1.0 conservan su puntaje |
| CP-V2-008 | RF-045 | Tope de 120 % por ítem |
| CP-V2-009 | RF-046 | Felicitación +10 y reclamo −20 |
| CP-V2-010 | RF-046 | Total entre 0 y 150 % |
| CP-V2-011 | RF-047 | Las ausencias ajustan la meta esperada |
| CP-V2-012 | RF-046 | Máximo 3 felicitaciones por período |
| CP-V2-013 | RF-046 | Solo el Delegado registra felicitaciones (403 para el Funcionario) |
| CP-V2-014 | RF-046/047 | El Delegado solo elige funcionarios de su equipo |
| CP-V2-015 | RF-047 | Ausencias sin fechas al revés ni cruzadas |
| CP-V2-016 | RF-039 | Organizaciones por delegación, territoriales y funcionales |

### Casos de la versión 2.1 (alcance mínimo de la Guía)

| Caso | Requisito | Qué verifica |
|---|---|---|
| CP-AGE-001 | RF-016 | Código AC-0001; la agenda la ve el equipo de la delegación y no otra (404) |
| CP-AGE-002 | RF-017 | Responsable y fecha comprometida obligatorios; fecha no anterior a la solicitud |
| CP-AGE-003 | RF-018 | Transiciones controladas e historial (anterior, nuevo, autor y observación) |
| CP-AGE-004 | RF-019 | Vencidos, próximos a vencer y realizados fuera de plazo; filtro de vencidos |
| CP-AGE-005 | RF-021 | El resumen por responsable coincide con el detalle filtrado |
| CP-AGE-006 | HU-15 | Solo el Delegado reasigna, con motivo en el historial |
| CP-AGE-007 | RF-020 | La actividad que cumple un compromiso lo cierra una sola vez |
| CP-AUD-001 | RF-036 | La auditoría guarda usuario, acción, valor anterior y valor nuevo |
| CP-AUD-002 | RF-036 | La validación y el rechazo quedan registrados |
| CP-AUD-003 | RNF-008 | El historial no se modifica ni se elimina; el Funcionario no lo ve (403) |
| CP-AUD-004 | HU-26 | Un acceso denegado queda registrado |
| CP-EXP-001 | RF-033 | El CSV respeta el ámbito y los filtros, e incluye la fecha de generación |
| CP-EXP-002 | RF-033 | Exportación del cumplimiento (con la fórmula) y de la agenda |
| CP-PCE-001 | RN-013 / CA-10 | En un período cerrado no se registra, edita, elimina ni valida |
| CP-FIL-001 | RF-032 | Filtros por funcionario y fechas; los filtros se conservan |
| CP-ALE-001 | RF-030 | Último ingreso, días sin ingreso, registros y promedio diario |
| CP-ALE-002 | RF-037 | Alertas del Delegado (compromisos vencidos y funcionarios sin registros) |
| CP-ALE-003 | RF-008 | El panel muestra un período anterior |
| CP-DEM-001 | Guía §15 (datos de demostración) | `reiniciar_demo` deja solo el equipo de ejemplo y no cambia las contraseñas demo |
| CP-SEG-001 | OWASP A05 | Una búsqueda con `' OR 1=1 --` viaja como parámetro y no devuelve registros de más |
| CP-SEG-002 | OWASP A05 | Un `<script>` en la descripción se muestra escapado |
| CP-SEG-003 | OWASP A08 | Un formulario sin token CSRF se rechaza (403) |
| CP-SEG-004 | OWASP A01 | El Funcionario solo ve lo suyo; otra delegación responde 404 |
| CP-DEM-002 | Guía §15 | Ni `cargar_datos_iniciales` ni `reiniciar_demo` revierten los nombres que el equipo cambió |

Resultado de la corrida de la versión 2.2.3: **180 pruebas, 0 fallos** (`resultados_pruebas.csv`). Además, `flake8` reporta 0 observaciones. La relación de cada historia con sus casos está en `MATRIZ_TRAZABILIDAD.md`.

## 2.1.6.14 — Herramientas automatizadas y manuales

El plan combina deliberadamente ambos tipos de herramienta, no solo uno:

| Tipo | Herramienta | Qué cubre |
|---|---|---|
| Automatizada | `python manage.py test` (Django `TestCase` + `unittest`) | Las 41 pruebas unitarias e integrales de modelo, reglas de negocio, vistas y CRUD — repetibles, sin intervención humana, correctas contra una base de datos real (MariaDB) creada y destruida en cada corrida. |
| Automatizada | Playwright (`screenshots_responsive.py`) | Navegación real y capturas de pantalla en 3 resoluciones (1280/768/390px) para verificar adaptabilidad — scriptado, repetible. |
| Manual | Navegador (Chrome/Edge), sesión guiada por checklist | Verificación visual de badges, formularios de validación, pantallas de confirmación de borrado y mensajes de éxito/error — cosas que una prueba automatizada de backend no "ve" (apariencia, legibilidad, experiencia de uso). |
| Manual | Revisión de código / lectura cruzada | Confirmar que `clean()` y `marcar_validado()` se llaman desde todos los puntos de entrada (Admin, formulario público, comando de carga de datos), no solo donde hay una prueba automatizada apuntando. |

Ninguno de los dos tipos sustituye al otro: lo automatizado da repetibilidad
y cobertura de regresión; lo manual detecta problemas de experiencia de
usuario que una prueba de backend no puede detectar por sí sola (así se
encontró, por ejemplo, el bug real de `.hero` en móvil — ver
`PROTOTIPO.md`, 2.1.3.6).

## Pruebas de rendimiento (2.1.6.13)

Dado el tamaño del proyecto (datos de ejemplo, no producción con miles de
usuarios concurrentes), el enfoque de rendimiento fue una verificación
básica y honesta, no una prueba de carga formal con una herramienta
dedicada (JMeter, Locust, etc. quedan fuera del alcance actual — ver
`CRONOGRAMA.md`, Sprint 5-futuro):

- Las 41 pruebas automatizadas completas corren en **0.789 segundos**
  (ver evidencia abajo), lo que ya da una señal de que no hay consultas
  N+1 obviamente lentas en las reglas de negocio ni en los `QuerySets`
  usados por las vistas.
- Verificación manual de tiempo de respuesta percibido: cada página del
  sitio (listados, detalle, formularios) carga en menos de 1 segundo en
  el entorno de desarrollo local, navegando con datos de ejemplo
  (datos de ejemplo de la versión 1.0: 6 delegaciones, 10 funcionarios y 8 actividades).
- Limitación declarada: no se probó el comportamiento con un volumen de
  datos realista de producción (cientos de actividades) ni con usuarios
  concurrentes. Es un siguiente paso razonable, no algo ya resuelto.

## Evidencia de ejecución (corrida real, no simulada)

Entorno: Python 3.11, Django 4.2.30, MariaDB 10.11 (motor `mysql` igual que
en `.env`), ejecutado el 2026-10-06.

```
Found 41 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
test_crear_delegacion_mediante_formulario (delegaciones.tests.DelegacionCrudTests...) ... ok
test_editar_delegacion_mediante_formulario (delegaciones.tests.DelegacionCrudTests...) ... ok
test_eliminar_delegacion_mediante_formulario (delegaciones.tests.DelegacionCrudTests...) ... ok
test_eliminar_muestra_confirmacion_antes_de_borrar (delegaciones.tests.DelegacionCrudTests...) ... ok
test_nombre_unico (delegaciones.tests.DelegacionModeloTests...) ... ok
test_slug_explicito_no_se_sobreescribe (delegaciones.tests.DelegacionModeloTests...) ... ok
test_slug_se_genera_automaticamente (delegaciones.tests.DelegacionModeloTests...) ... ok
test_str_representation (delegaciones.tests.DelegacionModeloTests...) ... ok
test_busqueda_filtra_resultados (delegaciones.tests.DelegacionVistasTests...) ... ok
test_detalle_existente_responde_200 (delegaciones.tests.DelegacionVistasTests...) ... ok
test_detalle_inexistente_responde_404 (delegaciones.tests.DelegacionVistasTests...) ... ok
test_listado_responde_200 (delegaciones.tests.DelegacionVistasTests...) ... ok
test_crear_actividad_mediante_formulario (gestion.tests.ActividadCrudTests...) ... ok
test_editar_actividad_mediante_formulario (gestion.tests.ActividadCrudTests...) ... ok
test_eliminar_actividad_mediante_formulario (gestion.tests.ActividadCrudTests...) ... ok
test_eliminar_muestra_confirmacion_antes_de_borrar (gestion.tests.ActividadCrudTests...) ... ok
test_actividad_queda_asociada_a_delegacion_categoria_y_funcionario (gestion.tests.ActividadModeloTests...) ... ok
test_borrar_delegacion_borra_sus_actividades_en_cascada (gestion.tests.ActividadModeloTests...) ... ok
test_codigo_unico (gestion.tests.ActividadModeloTests...) ... ok
test_no_se_puede_borrar_categoria_en_uso (gestion.tests.ActividadModeloTests...) ... ok
test_no_se_puede_borrar_funcionario_en_uso (gestion.tests.ActividadModeloTests...) ... ok
test_clean_acepta_delegado_valido (gestion.tests.ActividadValidacionTests...) ... ok
test_clean_rechaza_autovalidacion (gestion.tests.ActividadValidacionTests...) ... ok
test_clean_rechaza_validado_por_sin_rol_delegado (gestion.tests.ActividadValidacionTests...) ... ok
test_el_funcionario_no_puede_autovalidarse (gestion.tests.ActividadValidacionTests...) ... ok
test_un_delegado_puede_validar (gestion.tests.ActividadValidacionTests...) ... ok
test_un_par_funcionario_no_puede_validar (gestion.tests.ActividadValidacionTests...) ... ok
test_detalle_muestra_formulario_cuando_no_esta_validada (gestion.tests.ActividadValidacionVistaTests...) ... ok
test_detalle_no_muestra_formulario_cuando_ya_esta_validada (gestion.tests.ActividadValidacionVistaTests...) ... ok
test_validar_desde_la_vista_aplica_la_regla_de_negocio (gestion.tests.ActividadValidacionVistaTests...) ... ok
test_validar_rechaza_autovalidacion_desde_la_vista (gestion.tests.ActividadValidacionVistaTests...) ... ok
test_busqueda_por_codigo (gestion.tests.ActividadVistasTests...) ... ok
test_filtro_por_estado (gestion.tests.ActividadVistasTests...) ... ok
test_listado_sin_filtro_muestra_todo (gestion.tests.ActividadVistasTests...) ... ok
test_nombre_cargo_unico (organizacion.tests.CargoFuncionTests...) ... ok
test_str_representation (organizacion.tests.CargoFuncionTests...) ... ok
test_funcionario_queda_asociado_a_delegacion_y_cargo (organizacion.tests.FuncionarioTests...) ... ok
test_no_se_puede_borrar_cargo_con_funcionarios (organizacion.tests.FuncionarioTests...) ... ok
test_rut_unico (organizacion.tests.FuncionarioTests...) ... ok
test_borrar_cargo_borra_sus_metas_en_cascada (organizacion.tests.MetaProyectoTests...) ... ok
test_meta_asociada_a_cargo_con_ponderador (organizacion.tests.MetaProyectoTests...) ... ok

----------------------------------------------------------------------
Ran 41 tests in 0.789s

OK
Destroying test database for alias 'default' ('test_sgr_evaluacion2')...
```

## Evidencia manual (navegador, no solo pruebas automatizadas)

Además de las 41 pruebas automatizadas, se verificó manualmente con
capturas de pantalla reales (`python manage.py runserver` + navegación)
que:

- El listado de actividades muestra el badge "Validado ✓" o "Pendiente de
  validación" según corresponda.
- La ficha de una actividad pendiente muestra el formulario de validación
  (solo Funcionarios con rol Delegado aparecen en el selector).
- La ficha de una actividad ya validada muestra quién la validó y cuándo,
  y ya no muestra el formulario.
- Los formularios reales de "Agregar actividad", "Agregar delegación",
  "Modificar" y la pantalla de confirmación de "Eliminar" funcionan
  end-to-end contra la base de datos (ya no son la pantalla "en
  construcción" de la Evaluación 2).
- `python manage.py cargar_datos_iniciales` siembra 3 Funcionarios con rol
  Delegado (uno por delegación con actividades de ejemplo) y deja 3
  actividades ya validadas de ejemplo, usando el mismo método
  `marcar_validado()` que usa la interfaz real.
