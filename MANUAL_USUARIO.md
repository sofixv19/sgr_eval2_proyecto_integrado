# Manual breve de usuario — SGR La Serena (versión 2.1.1)

**Dirección:** http://184.194.243.125:8000 (Firefox, Edge o Chrome).

Al entrar se pide usuario y contraseña. Después de 5 intentos fallidos la cuenta se bloquea 15 minutos. Cada persona ve **solo lo que corresponde a su rol y a su delegación**. El número de versión aparece en el pie de cada página.

## Cuentas de demostración

| Usuario | Rol | Qué ve |
|---|---|---|
| `funcionario.rural` | Funcionario | Sus actividades, sus metas y la agenda de su delegación |
| `delegado.rural` | Delegado | Su delegación Rural y su equipo |
| `coordinador.sgr` | Coordinador | Todas las delegaciones |
| `admin.sgr` | Administrador | Todo el sistema |
| `verificador.sgr` | Verificador | Todo, solo lectura |

Todos los datos son ficticios, marcados "(ejemplo)". La contraseña de demostración la entrega el equipo.

---

## 1. Funcionario

**Mi panel**
- Un círculo muestra el cumplimiento del período. La marca negra es lo esperado a la fecha.
- Las tarjetas muestran actividades registradas, validadas, esperando validación y sin evidencia.
- *Mis metas*: cada ítem con su avance (por ejemplo, 2/4) y su color de semáforo.
- *Mis compromisos abiertos* y *Últimas actividades*.
- *Alertas*: compromisos vencidos o por vencer, actividades rechazadas, días sin registrar y avance bajo lo esperado.
- El selector de arriba a la derecha permite **ver un período anterior**.

**Registrar actividad**
1. Elija la fecha. Solo se aceptan fechas de la semana en curso; el lunes también se acepta la semana anterior.
2. Elija el ítem o categoría y si es la **realización** de la acción o una **gestión previa**. La gestión previa no suma puntaje.
3. Indique quién solicita: vecino, organización o el propio Delegado. Si la pidió el Delegado, no suma.
4. Escriba el **nombre y teléfono del usuario**. Sin ellos la actividad no suma.
5. Adjunte la foto o el PDF de evidencia (de hasta 5 MB). También se puede subir después.
6. Guarde. El sistema asigna el código (por ejemplo, DI-0001) y la actividad queda *Pendiente* de validación.

Se pueden ingresar como máximo **7 actividades por día**. En la ficha de cada actividad se indica si **suma puntaje** y por qué.

**Agenda colectiva:** "Agenda" → "+ Nuevo compromiso". En la ficha del compromiso se actualiza su estado, siempre con una observación. Con "Registrar la actividad que lo cumple" el compromiso queda *Realizado*.

## 2. Delegado

**Mi delegación**
- Cumplimiento de la delegación, evidencias por validar y alertas.
- *Cumplimiento por funcionario*: cada uno con su último ingreso, sus registros y su promedio diario.

**Validar actividades**
1. Abra la actividad.
2. Revise la evidencia.
3. Elija **Aprobar** o **Rechazar**. Para rechazar hay que escribir una observación.

Solo las actividades aprobadas que suman puntaje cuentan para la meta. El Delegado no puede validar sus propias actividades.

**Menú "Mi equipo"**
- *Mis funcionarios*: crear funcionarios de su delegación. Al guardar se muestran el usuario y la contraseña temporal para entregárselos.
- *Metas*: asignar metas por funcionario, período e ítem. La suma de los ponderadores no puede superar 100 %.
- *Felicitaciones y reclamos*: con respaldo formal. Cada felicitación suma +10 (máximo 3) y cada reclamo resta −20.
- *Ausencias*: licencias, vacaciones y días administrativos o libres. Ajustan la meta esperada en el semáforo.
- *Organizaciones comunitarias*: juntas de vecinos y organizaciones funcionales de su territorio.

**Agenda**
- Ve los compromisos de toda la delegación, con filtros y el resumen por responsable.
- Puede **reasignar** un compromiso indicando el motivo.

## 3. Coordinador

- **Panel de coordinación**:
  - Cumplimiento promedio de la comuna y tabla por delegación (semáforo, compromisos vencidos, umbral colectivo de 80 %).
  - Alertas y botón **Exportar cumplimiento**.
- **Delegaciones**: crear, modificar, activar y desactivar.
- **Delegados**: crear al Delegado de cada delegación.
- **Más**:
  - Períodos de medición (abrir y cerrar; un período cerrado ya no se puede modificar).
  - Organizaciones comunitarias y **auditoría**.

## 4. Administrador y Verificador

- **Mantenedores**: todas las tablas maestras.
- **Auditoría**: quién cambió qué dato y cuándo, con el valor anterior y el nuevo. Es de solo lectura.
- El Verificador puede consultar todo, pero no puede modificar nada.

## 5. Exportar a Excel

En **Actividades**, **Agenda** y **Panel de coordinación** hay botones *Exportar (CSV)*.

- El archivo se abre con Excel.
- Respeta los filtros aplicados en pantalla.
- Indica la fecha de generación y el usuario que lo generó.

## 6. Colores del semáforo

| Color | Significado |
|---|---|
| 🟢 Verde | El avance alcanza lo esperado a la fecha |
| 🟡 Ámbar | El avance está entre el 60 % y el 100 % de lo esperado |
| 🔴 Rojo | El avance está bajo el 60 % de lo esperado |

En la agenda, el **amarillo** marca los compromisos que vencen en 3 días o menos, y el **rojo** los vencidos sin realizar.
