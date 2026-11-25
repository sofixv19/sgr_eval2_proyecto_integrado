# Diego Villalobos — Rol en el proyecto SGR

## Módulos a cargo
- **Planificación (Trimestres y metas):** Define las metas por trimestre y su peso porcentual para cada funcionario, con un techo del 120 %.
- **Ejecución (Actividades y gestiones sociales):** Registra cada gestión asignándole un identificador único (`AD-0001`, `GS-0001`) junto a su respaldo documental.
- **Control (Verificación):** El Delegado evalúa los envíos para aceptarlos, rechazarlos o pedir correcciones; los registros aprobados pasan a ser definitivos e inalterables.
- **Seguimiento (Cumplimiento):** Evalúa el estado de avance en un semáforo tomando en cuenta únicamente las actividades aprobadas.

## Pruebas que reviso
- CP-PER (8), CP-MET (9), CP-ACT (12), CP-VLD (10), CP-VER (4), CP-GSO (5), CP-COD (3), CP-EVI (5), CP-CUM (4) y CP-PCE (1).
- Ejemplo: CP-VER-004 comprueba que nadie, ni el Administrador, modifica un registro aprobado.

## Archivos principales
gestion/models.py, gestion/forms.py, gestion/indicadores.py