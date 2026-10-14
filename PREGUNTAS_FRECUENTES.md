# Preparación de preguntas — SGR La Serena

Cubre el criterio **2.1.6.15** ("Responde preguntas") de la rúbrica de
Evaluación 2. Este criterio es **oral**: no se "entrega" un archivo, se
responde en vivo frente al profesor. Este documento es solo preparación —
una lista de preguntas probables (basadas en lo que Ciceo ya preguntó o
comentó en la retroalimentación de audio de la Evaluación 1) con
respuestas breves y concretas, para tenerlas claras antes de la
presentación. No reemplaza entender el proyecto: es un apoyo para no
quedarse en blanco.

## Sobre el diagrama de clases

**¿Por qué esta relación es de agregación y no de composición (o
viceversa)?**
Regla simple para responder cualquier variante de esta pregunta: mirar si
en el código real el `on_delete` es `CASCADE` (el hijo no puede existir
sin el padre → composición) o `PROTECT`/`RESTRICT` (el hijo es
independiente, solo referencia al padre → asociación/agregación). La
tabla completa de justificaciones está en `DIAGRAMA_CLASES.md`.

**¿Por qué Delegado, Coordinador y Verificador son herencia y no solo un
campo "rol"?**
En el modelo conceptual (este diagrama) se representan como herencia de
Funcionario porque cada uno tiene su propio comportamiento específico
(`validarEvidencia()`, `supervisarDelegaciones()`, `auditar()`) además de
todo lo que ya tiene Funcionario — así se ve gráficamente que comparten la
base pero no se mezclan funciones entre roles. (En el código Django real
de esta entrega, por simplicidad, se implementó solo como un campo
`rol` en el mismo modelo `Funcionario` — se puede explicar que el diagrama
conceptual es el "plano" completo y el código actual implementa la parte
ya construida de ese plano: Funcionario y Delegado.)

**¿Qué es una dependencia y por qué GestorIndicadores/GestorAlertas se
relacionan así con las demás clases?**
Una dependencia (flecha punteada) significa que una clase *usa* a otra
solo como parámetro de un método, sin guardarla como atributo propio. Por
eso GestorIndicadores "depende de" Indicador y Meta (las recibe para
calcular), pero no las "tiene" como parte de su estructura.

## Sobre la validación de actividades (la regla de negocio central)

**¿Por qué el Delegado no puede validar sus propias actividades?**
Porque el control de calidad pierde sentido si la misma persona que
registra algo también lo aprueba — es la misma lógica que un jefe que
no puede autoaprobar su propio gasto. Se aplica en dos lugares: el
formulario (`ValidacionForm`, que directamente no deja elegir al
Funcionario que registró la actividad) y el modelo (`Actividad.clean()`,
que lo rechaza aunque alguien intente forzarlo desde Admin u otra vía).

**¿Qué pasa si dos Delegados existen en la misma delegación?**
El modelo no lo impide a nivel de base de datos (no hay un límite de "un
Delegado por delegación" como restricción dura), pero la regla de negocio
sí exige que quien valida tenga `rol='Delegado'` y no sea quien registró
la actividad — cualquier Delegado de esa delegación que cumpla esa
condición puede validar. Es una limitación de diseño conocida, no un
error: se puede mencionar como posible mejora futura (ver
`CRONOGRAMA.md`, Sprint 5).

## Sobre seguridad

**¿Cómo evitan la inyección SQL si usan formularios?**
Porque nunca se escribe SQL a mano: todas las consultas pasan por el ORM
de Django (`Actividad.objects.filter(...)`, por ejemplo), que genera
SQL parametrizado automáticamente — el dato que escribe el usuario nunca
se concatena directo a una consulta.

**¿Por qué los formularios públicos no tienen login?**
Es una limitación declarada, no un olvido: el foco de esta entrega fue la
regla de negocio de validación (que sí está protegida en dos capas,
formulario y modelo) y el CRUD real. Login por rol para el sitio público
es el siguiente paso natural (ver `SEGURIDAD.md`, 2.1.5.10, y
`CRONOGRAMA.md`, Sprint 5). Es mejor decir esto con seguridad que
inventar que ya existe.

## Sobre el prototipo y la metodología

**¿Por qué no usaron Figma si el plan original lo mencionaba?**
Porque el proyecto real de Django ya existe y funciona de verdad contra
una base de datos — es un prototipo funcional, no solo visual, lo que es
evidencia más fuerte que un mockup estático. Se puede mencionar que esto
fue una decisión consciente, no que se "saltó" un paso.

**¿Cómo manejaron las prioridades en el cronograma con solo dos
personas?**
Con un criterio simple: una tarea es de prioridad Alta si otras tareas
dependen de que esté lista primero (por ejemplo, el modelo de datos tuvo
que estar listo antes de poder construir la validación de actividades).
El detalle completo está en `CRONOGRAMA.md`.

## Sobre las pruebas

**¿Cuántas pruebas tienen y qué prueban exactamente?**
41 pruebas automatizadas (`python manage.py test`), repartidas en 4 apps:
modelos (relaciones, reglas de borrado), reglas de negocio (quién puede
validar), vistas HTTP (listados, filtros, búsqueda) y CRUD real (crear,
editar, eliminar con confirmación). El detalle con nombres y resultado
real de la corrida está en `TESTING.md`.

**¿Probaron rendimiento?**
De forma básica, no con una herramienta de carga dedicada: se verificó
que las 41 pruebas completas corren en menos de un segundo y que cada
página carga rápido con los datos de ejemplo. Una prueba de carga formal
(muchos usuarios concurrentes, miles de registros) queda declarada como
trabajo futuro, no como algo ya resuelto — ver `TESTING.md`.

## Consejo general para la presentación

Si una pregunta toca algo que **no** está implementado todavía
(Coordinador/Verificador sin funciones propias, sin login público, sin
prueba de carga formal), la mejor respuesta es decirlo con seguridad como
una decisión de alcance ya declarada en la documentación (`SEGURIDAD.md`,
`CASOS_DE_USO.md`, `CRONOGRAMA.md`), no improvisar que sí existe. El
profesor ya valoró antes la honestidad sobre el alcance real del
proyecto.
