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
| **2.0.0** | **CP-V2-001 a CP-V2-016** | `gestion/tests_v2.py` | **156** |

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

Resultado de la corrida de la versión 2.0: **156 pruebas, 0 fallos** (`resultados_pruebas.csv`). Además, `flake8` reporta 0 observaciones.

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
  (6 delegaciones, 10 funcionarios, 8 actividades).
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
