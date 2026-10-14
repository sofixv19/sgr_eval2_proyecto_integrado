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
| CU-16 | Autenticarse en el sistema | Administrador / Coordinador / Delegado / Funcionario | Login de Django Admin (`/admin/login/`) | ⚠️ Solo existe para Django Admin; no hay login para el sitio público todavía | — Pendiente |
| CU-17 | Un Funcionario/Delegado inicia sesión y solo ve/edita lo que le corresponde (permisos por rol fuera de Admin) | Funcionario / Delegado | — | ❌ No implementado | — Pendiente (ver limitación abajo) |

## Limitaciones conocidas (declaradas, no ocultas)

- **CU-16/CU-17**: el rol (`Funcionario.rol`) hoy es un dato del catálogo,
  pero no está enlazado a una cuenta de usuario de Django fuera de Django
  Admin. En la práctica, "quién valida" se elige en un selector dentro del
  formulario de validación (`ValidacionForm`, limitado a
  `rol='Delegado'`), en vez de inferirse de una sesión iniciada. Esto es
  suficiente para demostrar la regla de negocio (CU-12) con las pruebas
  automatizadas, pero un sistema de login por rol para el sitio público
  queda fuera del alcance actual.
- No hay bitácora/auditoría (quién cambió qué y cuándo) más allá del par
  `validado_por` / `fecha_validacion` específico de la validación de
  actividades.

Estas dos limitaciones ya se le mencionaron a Sofía durante el desarrollo
y quedaron fuera de alcance por decisión explícita, no por descuido.
