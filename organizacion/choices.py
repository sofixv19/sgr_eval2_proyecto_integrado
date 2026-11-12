"""Opciones fijas para el rol de acceso de los funcionarios.

Jerarquía aclarada por el profesor Ciceo (retroalimentación de la
Evaluación 1): Administrador del sistema (staff de Django) -> Coordinador
-> Delegado (uno por Delegación) -> Funcionario Operativo. El Delegado y
el Funcionario Operativo NO pueden tener las mismas funciones: el
Funcionario registra actividades y sube evidencia; el Delegado es quien
VALIDA esas actividades (no se puede autovalidar un par del mismo nivel).

'Delegado' se agregó como rol propio (antes solo existían Funcionario,
Coordinador y Verificador) para poder restringir quién puede validar
actividades en el modelo 'Actividad' (ver gestion/models.py).
"""

ROLES_SISTEMA = (
    ('Funcionario', 'Funcionario Operativo'),
    ('Delegado', 'Delegado de Delegación'),
    ('Coordinador', 'Coordinador Estratégico'),
    ('Verificador', 'Verificador / Auditor'),
)


# Áreas de trabajo. El código de cada actividad se genera con la sigla del
# área del cargo del funcionario (retroalimentación del profesor Caiceo,
# Evaluación 2: "si yo estoy en territorial se crea un código TR").
AREAS = (
    ('TR', 'Territorial'),
    ('SO', 'Social'),
    ('OC', 'Organizaciones comunitarias'),
    ('DI', 'Diserco'),
    ('SE', 'Seguridad'),
    ('AD', 'Administrativa'),
    ('PC', 'Planificación y control'),
)
