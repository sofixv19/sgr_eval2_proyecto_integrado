# Matriz de trazabilidad — SGR La Serena (versión 2.1)

Es la matriz que exige la Guía SGR (sección 15.1). Cada historia de usuario se relaciona con:
- el requisito,
- el código que la implementa,
- los casos de prueba automatizados y su resultado,
- la ruta de la página donde se ve.

Los resultados salen de la corrida real de `python plan_pruebas.py`, guardada en `resultados_pruebas.csv`: **174 casos, 174 aprobados**. Los casos marcados con `*` incluyen todos los casos de ese grupo.

> **Responsable**: completar con el integrante que presenta cada historia (Sofía Veliz, Elías Medina, Ignacio Sepúlveda o Diego Villalobos). Diego es el responsable de las pruebas CP-PER, CP-MET, CP-ACT y CP-VLD.

| HU | Historia | Prioridad / versión | Requisitos | Implementación (archivo) | Casos de prueba | Resultado | Responsable | Evidencia (ruta en la página) |
|---|---|---|---|---|---|---|---|---|
| HU-01 | Registro de actividades | P1 | RF-009, RF-010, RF-014, RF-022 | `gestion/forms.py (ActividadForm), gestion/views.py (crear)` | CP-ACT-*, CP-COD-*, CP-V2-001–006 | 21/21 aprobados | Equipo SGR | `/gestion/nueva/` |
| HU-02 | Registro de compromisos ciudadanos | P1 | RF-016 a RF-021 | `gestion/views_agenda.py, gestion/models.py (Compromiso)` | CP-AGE-001–005 | 5/5 aprobados | Equipo SGR | `/gestion/agenda/` |
| HU-03 | Registro de servicios entregados (atención social) | P2 | RF-004, RF-015 | ⛔ No implementado (prioridad P2, limitación declarada) | — | — | — | — |
| HU-04 | Funciones por cargo | P1 | RF-003, RF-006, RF-007 | `organizacion/forms.py (CargoFuncionForm, MetaFuncionarioForm)` | CP-CAR-*, CP-ORG-*, CP-MET-* | 22/22 aprobados | Equipo SGR | `/organizacion/cargos/` |
| HU-05 | Definición de metas | P1 | RF-005 a RF-007 | `organizacion/forms.py (MetaFuncionarioForm, PeriodoForm)` | CP-MET-*, CP-PER-* | 17/17 aprobados | Equipo SGR | `/organizacion/metas/` |
| HU-06 | Seguimiento de avance | P1 | RF-008, RF-022, RF-023, RF-028 | `delegaciones/views.py (panel_funcionario), gestion/indicadores.py` | CP-CUM-001, CP-PERF-008, CP-ALE-003 | 3/3 aprobados | Equipo SGR | `/` |
| HU-07 | Cálculo automático de cumplimiento | P1 | RF-023 a RF-026 | `gestion/indicadores.py` | CP-CUM-*, CP-V2-008–011, CP-EXP-002 | 9/9 aprobados | Equipo SGR | `/gestion/exportar/cumplimiento/` |
| HU-08 | Desempeño organizacional | P2 | RF-029, RF-031 | `delegaciones/views.py (panel_delegado, panel_coordinador)` | CP-CUM-004, CP-PERF-008 | 2/2 aprobados | Equipo SGR | `/` |
| HU-09 | Evidencia fotográfica | P1 | RF-012, RNF-017 | `gestion/models.py (Evidencia), gestion/views.py (detalle, evidencia)` | CP-EVI-* | 5/5 aprobados | Equipo SGR | `/gestion/<id>/` |
| HU-10 | Códigos verificadores | P1 | RF-011 | `gestion/models.py (Actividad.siguiente_codigo)` | CP-COD-001, CP-COD-002 | 2/2 aprobados | Equipo SGR | `/gestion/<id>/` |
| HU-11 | Validación de actividades | P1 | RF-013, RF-014, RF-036 | `gestion/views.py (detalle), gestion/forms.py (RevisionForm)` | CP-VLD-*, CP-AUD-002 | 11/11 aprobados | Equipo SGR | `/gestion/?validacion=Pendiente` |
| HU-12 | Agenda compartida | P1 | RF-016, RF-017 | `gestion/views_agenda.py (agenda, compromiso_crear)` | CP-AGE-001, CP-AGE-002 | 2/2 aprobados | Equipo SGR | `/gestion/agenda/` |
| HU-13 | Actualización de estados | P1 | RF-018, RF-036 | `gestion/models.py (Compromiso.cambiar_estado, CambioCompromiso)` | CP-AGE-003 | 1/1 aprobados | Equipo SGR | `/gestion/agenda/<id>/` |
| HU-14 | Seguimiento de compromisos | P1 | RF-019, RF-021, RF-037 | `gestion/views_agenda.py (resumen_por_funcionario), gestion/alertas.py` | CP-AGE-004, CP-AGE-005, CP-ALE-002 | 3/3 aprobados | Equipo SGR | `/gestion/agenda/?situacion=vencidos` |
| HU-15 | Continuidad operativa (reasignar) | P2 | RF-017, RF-036 | `gestion/models.py (Compromiso.reasignar)` | CP-AGE-006 | 1/1 aprobados | Equipo SGR | `/gestion/agenda/<id>/` |
| HU-16 | Semáforo de cumplimiento | P1 | RF-026, RF-027 | `gestion/indicadores.py (semaforo)` | CP-CUM-003 | 1/1 aprobados | Equipo SGR | `/` |
| HU-17 | Avance esperado vs real | P1 | RF-023, RF-026, RF-027 | `gestion/indicadores.py (porcentaje_esperado_funcionario)` | CP-CUM-*, CP-V2-011 | 5/5 aprobados | Equipo SGR | `/` |
| HU-18 | Resumen ejecutivo | P1 | RF-028, RF-029, RF-031 | `delegaciones/views.py (panel_delegado, panel_coordinador)` | CP-PERF-008, CP-CUM-004 | 2/2 aprobados | Equipo SGR | `/` |
| HU-19 | Control de actividad de usuarios | P2 | RF-030, RF-037 | `gestion/alertas.py (actividad_reciente)` | CP-ALE-001, CP-ALE-002 | 2/2 aprobados | Equipo SGR | `/` |
| HU-20 | Generación de informes | P1 | RF-032, RF-033 | `gestion/exportar.py` | CP-EXP-001, CP-EXP-002 | 2/2 aprobados | Equipo SGR | `/gestion/exportar/actividades/` |
| HU-21 | Funcionarios rezagados | P2 | RF-027, RF-029, RF-037 | `gestion/alertas.py (alertas_delegacion)` | CP-ALE-002 | 1/1 aprobados | Equipo SGR | `/` |
| HU-22 | Brechas de productividad | P3 | RF-031, RF-038 | `Parcial: consulta de períodos anteriores en los paneles` | CP-ALE-003 | 1/1 aprobados | Equipo SGR | `/?periodo=<id>` |
| HU-23 | Trabajo colaborativo en línea | P1 | RF-034, RNF-003 | `gestion/models.py (código atómico), transacciones de la BD` | CP-COD-002 | 1/1 aprobados | Equipo SGR | `—` |
| HU-24 | Comunicación entre delegaciones | P2 | RF-035 | `Parcial: observaciones de validación e historial de compromisos` | CP-VLD-*, CP-AGE-003 | 11/11 aprobados | Equipo SGR | `—` |
| HU-25 | Adaptación continua | P1 | RF-038 | `gestion/models.py (version_reglas), organizacion/models.py (Periodo)` | CP-V2-007, CP-PCE-001 | 2/2 aprobados | Equipo SGR | `—` |
| HU-26 | Delegaciones, usuarios y roles | P1 | RF-001, RF-002, RNF-004, RNF-005 | `delegaciones/, organizacion/, cuentas/perfiles.py, configurar_roles` | CP-DEL-*, CP-FUN-*, CP-ROL-*, CP-PERF-*, CP-ACC-*, CP-LOGIN-*, CP-AUD-004 | 60/60 aprobados | Equipo SGR | `/delegaciones/` |
| HU-27 | Administración de catálogos | P1 | RF-004 | `gestion/views.py (Categoria*), delegaciones/views.py (Organizacion*)` | CP-CAT-*, CP-V2-016 | 8/8 aprobados | Equipo SGR | `/gestion/categorias/` |
| HU-28 | Administración de períodos | P1 | RF-005, RN-013 | `organizacion/forms.py (PeriodoForm), gestion/forms.py (período cerrado)` | CP-PER-*, CP-PCE-001 | 9/9 aprobados | Equipo SGR | `/organizacion/periodos/` |
| HU-29 | Búsqueda y filtros | P1 | RF-032 | `gestion/views.py (filtrar_listado_actividades), gestion/views_agenda.py (filtrar_agenda)` | CP-FIL-001, CP-AGE-004 | 2/2 aprobados | Equipo SGR | `/gestion/` |
| HU-30 | Auditoría de cambios | P1 | RF-036, RNF-008 | `comun/models.py, comun/auditoria.py, comun/views.py` | CP-AUD-* | 4/4 aprobados | Equipo SGR | `/auditoria/` |
| HU-31 | Alertas operativas | P2 | RF-037 | `gestion/alertas.py` | CP-ALE-002 | 1/1 aprobados | Equipo SGR | `/` |
| HU-V2-01 | Saber si la actividad suma puntaje | 2.0 | RF-040, RF-041, RF-044 | `gestion/models.py (motivos_sin_puntaje)` | CP-V2-001–003 | 3/3 aprobados | Equipo SGR | `/gestion/nueva/` |
| HU-V2-02 | Máx. 7 ingresos diarios y cierre semanal | 2.0 | RF-042, RF-043 | `gestion/forms.py (ActividadForm.clean)` | CP-V2-004, CP-V2-005, CP-COD-003 | 3/3 aprobados | Equipo SGR | `/gestion/nueva/` |
| HU-V2-03 | Felicitaciones y reclamos | 2.0 | RF-046 | `organizacion/models.py (Reconocimiento)` | CP-V2-009, CP-V2-010, CP-V2-012, CP-V2-013 | 4/4 aprobados | Equipo SGR | `/organizacion/felicitaciones/` |
| HU-V2-04 | Ausencias que ajustan el semáforo | 2.0 | RF-047 | `organizacion/models.py (Ausencia), gestion/indicadores.py` | CP-V2-011, CP-V2-014, CP-V2-015 | 3/3 aprobados | Equipo SGR | `/organizacion/ausencias/` |
| HU-V2-05 | Organizaciones comunitarias | 2.0 | RF-039 | `delegaciones/models.py (OrganizacionComunitaria)` | CP-V2-006, CP-V2-016 | 2/2 aprobados | Equipo SGR | `/organizaciones/` |

## Limitaciones declaradas

Según la sección 15.3 de la Guía, las limitaciones se declaran y no se ocultan:

- **HU-03 / RF-015 (atención social de hasta 3 gestiones por persona, P2)**: no está implementada.
- **HU-22 (P3)** y **HU-24 (P2)**: son parciales.
  - Se pueden consultar los períodos anteriores, pero no hay análisis de tendencias entre períodos.
  - Las observaciones quedan en las validaciones y en el historial de los compromisos, pero no hay conversación en hilo.
- **RF-003 / RF-031**: los ítems se asignan como metas por funcionario y período, y la vista global se agrupa por delegación, no por cargo.

## Cómo regenerar la evidencia

```bash
python plan_pruebas.py           # ejecuta todas las pruebas y reescribe resultados_pruebas.csv
python manage.py test -v 2       # muestra cada prueba con su resultado
flake8                           # estilo del código: 0 observaciones
```
