# Tabla de seguimiento de casos de uso — SGR La Serena

Responde al comentario del profesor Ciceo en la retroalimentación de la
primera prueba de Proyecto Integrado: "cuidado con las relaciones en la
gestión de los CU de alto nivel" y "qué pasa con los demás casos de uso de
detalle". Esta tabla conecta cada caso de uso con su actor real, la ruta
del sistema que lo implementa y la prueba automatizada que lo cubre, para
que quede trazable de principio a fin (requerimiento → código → prueba).

## Actores del sistema

| Actor | Quién es en el sistema | Nivel |
|---|---|---|
| Administrador | Staff/superuser de Django (Django Admin) | Más alto — gestiona todo el catálogo |
| Coordinador | `Funcionario.rol = 'Coordinador'` | Estratégico, supervisa delegaciones |
| Delegado | `Funcionario.rol = 'Delegado'` (uno por delegación) | Valida actividades de su delegación |
| Funcionario Operativo | `Funcionario.rol = 'Funcionario'` | Registra actividades y evidencia |
| Visitante / público | Sin cuenta, navega el sitio público | Solo lectura |

## Matriz de trazabilidad

| # | Caso de uso | Actor(es) | Implementado en (ruta) | Estado | Prueba automatizada |
|---|---|---|---|---|---|
| CU-01 | Ver página de inicio con resumen general | Visitante | `delegaciones:inicio` (`/`) | ✅ Completo | — (manual, Evaluación 1) |
| CU-02 | Listar delegaciones, con búsqueda | Visitante | `delegaciones:listado` (`/delegaciones/`) | ✅ Completo | `DelegacionVistasTests.test_listado_responde_200`, `test_busqueda_filtra_resultados` |
| CU-03 | Ver ficha de una delegación | Visitante | `delegaciones:detalle` (`/delegaciones/<slug>/`) | ✅ Completo | `test_detalle_existente_responde_200`, `test_detalle_inexistente_responde_404` |
| CU-04 | Registrar una nueva delegación | Administrador / Coordinador | `delegaciones:crear` (`/delegaciones/nueva/`) | ✅ CRUD real (antes "en construcción") | `DelegacionCrudTests.test_crear_delegacion_mediante_formulario` |
| CU-05 | Modificar una delegación | Administrador / Coordinador | `delegaciones:editar` | ✅ CRUD real | `test_editar_delegacion_mediante_formulario` |
| CU-06 | Eliminar una delegación | Administrador | `delegaciones:eliminar` (con confirmación) | ✅ CRUD real | `test_eliminar_delegacion_mediante_formulario`, `test_eliminar_muestra_confirmacion_antes_de_borrar` |
| CU-07 | Listar actividades, filtrar por estado y buscar | Visitante / Funcionario | `gestion:listado` (`/gestion/`) | ✅ Completo | `ActividadVistasTests.test_listado_sin_filtro_muestra_todo`, `test_filtro_por_estado`, `test_busqueda_por_codigo` |
| CU-08 | Ver ficha de una actividad (incl. estado de validación) | Visitante / Funcionario / Delegado | `gestion:detalle` (`/gestion/<id>/`) | ✅ Completo | `ActividadValidacionVistaTests.*` |
| CU-09 | **Registrar una actividad con evidencia** | Funcionario Operativo | `gestion:crear` (`/gestion/nueva/`) | ✅ CRUD real (antes "en construcción") | `ActividadCrudTests.test_crear_actividad_mediante_formulario` |
| CU-10 | Modificar una actividad | Funcionario Operativo (dueño) | `gestion:editar` | ✅ CRUD real | `test_editar_actividad_mediante_formulario` |
| CU-11 | Eliminar una actividad | Administrador | `gestion:eliminar` (con confirmación) | ✅ CRUD real | `test_eliminar_actividad_mediante_formulario`, `test_eliminar_muestra_confirmacion_antes_de_borrar` |
| CU-12 | **Validar una actividad registrada por un Funcionario** | **Delegado** (nunca el mismo Funcionario) | Formulario de validación dentro de `gestion:detalle` (`ValidacionForm`) | ✅ Nuevo — regla de negocio del profesor Ciceo | `ActividadValidacionTests.*` (modelo), `ActividadValidacionVistaTests.*` (vista) |
| CU-13 | Ver resumen de gestión (semáforo por estado) | Visitante / Coordinador | `gestion:resumen` (`/gestion/resumen/`) | ✅ Completo | — (manual, Evaluación 2) |
| CU-14 | Listar funcionarios, con búsqueda por nombre/cargo/delegación | Visitante | `organizacion:listado` (`/organizacion/funcionarios/`) | ✅ Completo | — (manual, Evaluación 2) |
| CU-15 | Administrar catálogo completo (cargos, metas, funcionarios, categorías, delegaciones, actividades) | Administrador | Django Admin (`/admin/`) | ✅ Completo, incl. acción masiva "Marcar como validadas" | — (cubierto indirectamente por las pruebas de modelo) |
| CU-16 | Autenticarse en el sistema | Todos los roles | `cuentas:login` (`/cuentas/ingresar/`) | ✅ Completo (v1.0) | `CP-ACC-*`, `CP-LOGIN-*` |
| CU-17 | Ver y editar solo lo que corresponde a su rol y delegación | Funcionario / Delegado / Coordinador | `cuentas/perfiles.py` (filtros de ámbito) | ✅ Completo (v1.1) | `CP-PERF-001` a `CP-PERF-010` |
| CU-18 | Subir evidencia y validarla o rechazarla | Funcionario / Delegado | `gestion:detalle` | ✅ Completo (v1.1) | `CP-EVI-*`, `CP-VLD-*` |
| CU-19 | Asignar metas a los funcionarios y ver el cumplimiento con semáforo | Delegado / Coordinador | `organizacion:metas`, paneles por rol | ✅ Completo (v1.1) | `CP-MET-*`, `CP-CUM-*` |

### Casos de uso nuevos de la versión 2.0 (Nuevos requerimientos, octubre 2026)

| # | Caso de uso | Actor(es) | Implementado en (ruta) | Requisito | Prueba automatizada |
|---|---|---|---|---|---|
| CU-20 | Registrar una actividad sabiendo si suma puntaje (solicitante, nombre y teléfono, gestión previa o realización), con máximo 7 por día y cierre semanal | Funcionario Operativo | `gestion:crear` | RF-040 a RF-044 | `CP-V2-001` a `CP-V2-005` |
| CU-21 | Registrar felicitaciones y reclamos con respaldo formal | **Delegado** | `organizacion:reconocimientos` (`/organizacion/felicitaciones/`) | RF-046 | `CP-V2-009`, `CP-V2-010`, `CP-V2-012`, `CP-V2-013` |
| CU-22 | Registrar ausencias del equipo (ajustan el semáforo) | **Delegado** | `organizacion:ausencias` (`/organizacion/ausencias/`) | RF-047 | `CP-V2-011`, `CP-V2-014`, `CP-V2-015` |
| CU-23 | Gestionar organizaciones comunitarias territoriales y funcionales | Delegado / Coordinador / Administrador | `delegaciones:organizaciones` (`/organizaciones/`) | RF-039 | `CP-V2-006`, `CP-V2-016` |

## Limitaciones conocidas (declaradas, no ocultas)

- Las limitaciones CU-16 y CU-17 de la versión 1.0 (no había login por rol) quedaron **resueltas en la versión 1.1**.
- No hay bitácora general de auditoría (quién cambió qué y cuándo). Solo quedan registrados quién validó (`validado_por`, `fecha_validacion`) y quién registró felicitaciones y ausencias (`registrado_por`).
- La regla 6 de los Nuevos requerimientos ("no ingresar solo para generar puntaje") no se puede verificar de forma automática. La apoyan las reglas de puntaje y la validación del Delegado.
