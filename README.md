# SGR La Serena — Sistema de Gestión de Resultados

> **Versión actual: 2.1.0** (Nuevos requerimientos, octubre 2026 + alcance mínimo completo de la Guía SGR) · Historial completo en [`CHANGELOG.md`](CHANGELOG.md) · Requisitos por versión en [`REQUISITOS_V2.md`](REQUISITOS_V2.md)

| Versión | Qué trae | Pruebas |
|---|---|---|
| **2.1.0** | Completa el alcance mínimo de la Guía SGR: **agenda colectiva** con historial, **auditoría**, **exportación a Excel**, filtros por período y fechas, períodos cerrados protegidos, actividad reciente y **alertas** | 174 |
| 2.0.0 | Nuevos requerimientos de la Coordinación de Delegaciones: organizaciones comunitarias, reglas de puntaje (solicitante, nombre y teléfono, gestión previa), máximo 7 ingresos diarios, cierre semanal, tope de 120 % por ítem, felicitaciones y reclamos, y ausencias que ajustan el semáforo | 156 |
| 1.1.0 | Correcciones de la revisión de la Evaluación 2: ámbito por rol, cuentas ligadas a funcionarios, código automático por área, evidencias, validación del Delegado, metas y paneles por rol | 140 |
| 1.0.0 | Evaluación 2 de Proyecto Integrado: login, mantenedores, roles y despliegue en AWS | 118 |

### Novedades de la versión 2.1

- **Agenda colectiva** (menú *Agenda*): compromisos con responsable, plazo, estados e historial, alertas de vencimiento, reasignación y resumen por responsable.
- **Auditoría** (menú *Auditoría* o *Más → Auditoría*): quién cambió qué y cuándo, en solo lectura.
- **Exportar a Excel** en Actividades, Agenda y Panel de coordinación.
- **Paneles** con selector de período, alertas y actividad reciente de cada funcionario.
- **Períodos cerrados**: no se pueden alterar sin reabrirlos.
- Documentos nuevos: [`MANUAL_USUARIO.md`](MANUAL_USUARIO.md) y [`MATRIZ_TRAZABILIDAD.md`](MATRIZ_TRAZABILIDAD.md).

### Novedades de la versión 2.0

- **Cada actividad muestra si suma puntaje y por qué.** No suman:
  - las gestiones previas (coordinar, enviar correos, invitar);
  - las que pidió el propio Delegado;
  - las que no tienen nombre y teléfono del usuario.
- **Máximo 7 ingresos por día** y **cierre semanal**: la semana se ingresa hasta el lunes siguiente.
- **Tope de 120 % por ítem.** El total del colaborador, con felicitaciones, llega como máximo a 150 %.
- **Menú "Mi equipo" del Delegado**:
  - *Felicitaciones y reclamos*: +10 cada una, máximo 3; −20 cada reclamo.
  - *Ausencias*: se descuentan del período en el semáforo.
  - *Organizaciones comunitarias*: territoriales y funcionales.
- **Las actividades anteriores a la 2.0 conservan su puntaje** (`version_reglas = "1.0"`).

### Actualizar un servidor que ya tenía una versión anterior

```bash
python manage.py migrate                 # tablas nuevas (2.0: organizaciones, felicitaciones, ausencias; 2.1: agenda y auditoría)
python manage.py configurar_roles        # agrega los permisos nuevos a cada rol
python manage.py cargar_datos_iniciales  # (opcional) organizaciones y compromisos de ejemplo
python manage.py collectstatic --noinput
sudo systemctl restart sgr
```

---

## Proyecto base — Evaluación Sumativa 2 (Programación Back End)

Sistema de Gestión de Resultados (SGR) de las delegaciones de la
I. Municipalidad de La Serena. Proyecto Django con base de datos MariaDB,
desplegado en AWS EC2 (http://184.194.243.125:8000/).

Es la continuación de la Evaluación 1 de Proyecto Integrado y comparte
la base del proyecto del ramo de Programación Back End.

## Novedades Evaluación 2 de Proyecto Integrado (octubre 2026)

- **Inicio de sesión obligatorio** en todo el sitio (`/cuentas/ingresar/`), con bloqueo temporal tras 5 intentos fallidos y cierre de sesión por POST.
- **Mantenedores (CRUD) de todas las tablas maestras**, con validaciones y permisos por rol:
  - Delegaciones (`/delegaciones/`)
  - Funcionarios (`/organizacion/funcionarios/`)
  - Cargos (`/organizacion/cargos/`)
  - Metas (`/organizacion/metas/`)
  - Categorías (`/gestion/categorias/`)
  - Períodos de medición (`/organizacion/periodos/`), que es la tabla `periodo` del MER de la Evaluación 1. Las metas ahora pertenecen a un cargo **y a un período**.
- **Roles con permisos**: `python manage.py configurar_roles` crea los grupos Administrador, Coordinador, Delegado, Funcionario y Verificador. Con `--usuarios-demo --clave "..."` crea además un usuario de prueba por rol.
- **118 pruebas unitarias** en la versión 1.0 (hoy son 174): `python plan_pruebas.py` las ejecuta y genera la matriz `resultados_pruebas.csv` con el ID de cada caso del plan.
- **Estándares** de construcción y de seguridad documentados en `ESTANDARES.md`. El estilo se revisa con `flake8`.

## Qué cambió respecto a la Evaluación 1

| Evaluación 1 | Evaluación 2 |
|---|---|
| Sin base de datos (`DATABASES = {}`) | Base de datos relacional (SQLite en desarrollo / MySQL en EC2) |
| Datos en `data/*.json`, leídos con funciones propias (`data.py`) | Datos en modelos Django (`models.py`), leídos con el ORM |
| Sin Django Admin | Django Admin con CRUD completo para todas las entidades |
| Configuración en `settings.py` | Configuración sensible en `.env` (python-decouple) |
| Sin botones de acción | Botones **Agregar / Modificar / Eliminar / Buscar** en los listados |
| Ejecución solo local | Pensado para ejecutarse en una instancia EC2, clonado desde GitHub |

Las 2 aplicaciones (`delegaciones` y `gestion`), sus rutas y su diseño visual
(Bootstrap local, paleta institucional, gráficos) se mantienen tal como en la
Evaluación 1.

## Proyecto fusionado (equipo)

Esta versión integra en **un solo proyecto** el trabajo de ambos integrantes
del equipo para esta evaluación:

- **delegaciones** y **gestion**: desarrollados originalmente por Sofía.
- **organizacion** (`CargoFuncion`, `Funcionario`, `MetaProyecto`): diseño
  original del compañero de equipo (antes en apps separadas
  `gestionCargosApp` / `registroActividadesApp`), incorporado aquí para que
  `Actividad.funcionario` sea una relación real hacia un `Funcionario` con
  cargo y delegación, en vez de un simple texto libre.

No se duplicó la tabla de `Delegacion` (el compañero también tenía una
propia): se usa una única `Delegacion`, la de la app `delegaciones`. Tampoco
se duplicó `Actividad`: a la de `gestion` se le agregaron los campos de
"solicitud vecinal" (`solicitud_problema`, `contacto`, `telefono_contacto`)
que el compañero había modelado en su propia versión.

## Jerarquía de roles y validación de actividades

Tras la retroalimentación del profesor Ciceo en la primera prueba de
Proyecto Integrado, se incorporó al proyecto la jerarquía de roles que
pidió, y la regla de que **el Delegado valida, no el propio Funcionario**:

```
Administrador (staff/superuser de Django)
        │
   Coordinador (rol 'Coordinador')
        │
    Delegado (rol 'Delegado' — uno por delegación, valida actividades)
        │
Funcionario Operativo (rol 'Funcionario' — registra actividades y evidencia)
```

- Un **Funcionario Operativo** registra una actividad (`gestion:crear`).
- Solo un **Delegado** puede marcarla como validada, desde el formulario
  que aparece en la ficha de la actividad (`gestion:detalle`) mientras no
  esté validada. El Delegado **no puede ser la misma persona** que
  registró la actividad, ni puede validar un par del mismo nivel
  jerárquico: esta regla está aplicada dos veces —en
  `Actividad.clean()` (modelo, válida también desde Django Admin) y en
  `Actividad.marcar_validado()` (método usado por el formulario y por el
  seed de datos)— y cubierta por pruebas automatizadas (ver `TESTING.md`).
- El detalle del diagrama de clases, incluidos estos campos de
  validación, está en `DIAGRAMA_CLASES.md`.
- La tabla de trazabilidad de todos los casos de uso (actor, ruta,
  estado, prueba que lo cubre) está en `CASOS_DE_USO.md`.

## Estructura del proyecto

```
sgr_evaluacion/      # Configuración del proyecto (settings, urls raíz)
delegaciones/        # Aplicación 1: información institucional de las delegaciones
  models.py           #   Delegacion, OrganizacionComunitaria (v2.0)
  admin.py            #   Administración de Delegacion
organizacion/        # Aplicación de cargos/funcionarios (diseño: compañero de equipo)
  models.py            #   CargoFuncion, Funcionario, MetaProyecto, Periodo, Reconocimiento y Ausencia (v2.0)
  admin.py             #   Administración de las 3 entidades (con metas inline)
gestion/             # Aplicación 2: actividades / solicitudes registradas
  models.py           #   Categoria, Actividad (FK a Delegacion, Categoria y Funcionario)
  admin.py            #   Administración de Categoria y Actividad
  services.py          #   Agregaciones ORM (resumen por estado, donut)
  indicadores.py       #   Cumplimiento, semáforo, tope por ítem, felicitaciones y ausencias
  tests_roles.py       #   Pruebas de la versión 1.1 (CP-PERF, CP-COD, CP-EVI, CP-CUM)
  tests_v2.py          #   Pruebas de la versión 2.0 (CP-V2-001 a CP-V2-016)
  views_agenda.py      #   Agenda colectiva (v2.1)
  exportar.py          #   Exportación a Excel/CSV (v2.1)
  alertas.py           #   Alertas y actividad reciente (v2.1)
  tests_v21.py         #   Pruebas de la versión 2.1 (CP-AGE, CP-AUD, CP-EXP, CP-PCE, CP-FIL, CP-ALE)
comun/               # Componentes comunes: mantenedores genéricos, validadores y auditoría (v2.1)
  management/commands/cargar_datos_iniciales.py  # Migra los JSON + siembra cargos/funcionarios
data/                # JSON originales de la Evaluación 1 (fuente para el seed)
static/              # Bootstrap local, CSS propio e imágenes
templates/           # Plantilla base + formulario genérico + confirmación de borrado
.env.example         # Plantilla de variables de entorno (copiar a .env)
CHANGELOG.md         # Historial de versiones (1.0, 1.1, 2.0)
REQUISITOS_V2.md     # Requerimientos por versión y cobertura de la Guía (RF-001 a RF-048)
MATRIZ_TRAZABILIDAD.md  # HU → requisito → código → pruebas → resultado → evidencia
MANUAL_USUARIO.md    # Manual breve de usuario por rol
DIAGRAMA_CLASES.md   # Diagrama de clases (Mermaid + PNG), 13 clases, estructura de Eval. 1
TESTING.md           # Plan de pruebas: automatizadas + manuales + rendimiento, con evidencia
CASOS_DE_USO.md       # Matriz de trazabilidad: caso de uso -> ruta -> prueba
CRONOGRAMA.md         # Metodología Scrum y cronograma del equipo (Eval. 2, 2.1.1)
ARQUITECTURA.md       # Vistas 4+1 y tabla de tecnologías (Eval. 2, 2.1.2)
PROTOTIPO.md          # Prototipo interactivo, adaptabilidad y retroalimentación (Eval. 2, 2.1.3)
MODELO_DATOS.md       # Modelo relacional real + datos estructurados/no estructurados (Eval. 2, 2.1.4)
SEGURIDAD.md          # Autenticación/autorización, amenazas y estándares (Eval. 2, 2.1.5)
PREGUNTAS_FRECUENTES.md  # Preparación de preguntas orales (Eval. 2, 2.1.6.15)
GUIA_DESPLIEGUE.md    # Paso a paso para correr con MySQL local y desplegar en AWS EC2
```

> Los 6 archivos marcados "(Eval. 2, ...)" cubren, en conjunto, las 15
> secciones de la rúbrica de Evaluación 2 del ramo de Caiceo (Proyecto
> Integrado), siguiendo la misma estructura corregida de la Evaluación 1.

## Pruebas automatizadas

El proyecto incluye **174 pruebas** (`python manage.py test`) en la versión 2.1
(41 en la primera versión de la Evaluación 2). Abarcan las cuatro
apps: unitarias de modelo (slugs, unicidad, relaciones y restricciones de
borrado), unitarias de la regla de validación (solo un Delegado valida, no
autovalidación), e integrales de vista (listados, filtros, búsqueda, 404,
CRUD real de Delegación y Actividad, flujo de validación). Todas corren
contra la misma base de datos configurada en `.env` (MySQL o SQLite) y
pasan sin errores. Detalle completo y evidencia de una corrida real en
`TESTING.md`.

## Modelo de datos

- **Delegacion** (`delegaciones`): nombre, slug, encargado, dirección, teléfono,
  correo, territorio, enfoque.
- **Categoria** (`gestion`): catálogo de categorías de actividad (Diserco,
  Social, Seguridad, Organizaciones Comunitarias, etc.).
- **CargoFuncion** (`organizacion`): catálogo de cargos municipales (nombre,
  descripción, vigencia).
- **Funcionario** (`organizacion`): nombre, RUT, correo, rol de sistema, con
  **ForeignKey** hacia `Delegacion` y hacia `CargoFuncion`.
- **MetaProyecto** (`organizacion`): meta medible asociada a un `CargoFuncion`
  (valor objetivo, unidad, ponderador).
- **Actividad** (`gestion`): código, fecha, descripción, estado (Pendiente /
  En proceso / Realizado), con **ForeignKey** hacia `Delegacion`, `Categoria`
  y `Funcionario`, más los campos opcionales de solicitud vecinal
  (`solicitud_problema`, `contacto`, `telefono_contacto`), y los campos de
  validación `validado`, `validado_por` (FK a `Funcionario`, solo con rol
  Delegado) y `fecha_validacion`.

Todas estas relaciones (`Actividad → Delegacion/Categoria/Funcionario`,
`Funcionario → Delegacion/CargoFuncion`, `MetaProyecto → CargoFuncion`) se
navegan desde Django Admin mediante `autocomplete_fields`.

## Cómo ejecutar el proyecto en local (desarrollo)

Por defecto el proyecto usa **SQLite**, para poder probarlo sin instalar
MySQL.

1. Crear y activar un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate      # En Windows: venv\Scripts\activate
   ```
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Copiar el archivo de variables de entorno:
   ```bash
   cp .env.example .env
   ```
   (con `DB_ENGINE=sqlite` no es necesario tocar nada más para probar en local).
4. Aplicar las migraciones:
   ```bash
   python manage.py migrate
   ```
5. Cargar los datos de la Evaluación 1 (delegaciones y actividades), el
   catálogo de cargos/funcionarios (incluyendo Funcionarios con rol
   Delegado) y algunas actividades ya validadas de ejemplo:
   ```bash
   python manage.py cargar_datos_iniciales
   ```
6. Crear un superusuario para entrar a Django Admin:
   ```bash
   python manage.py createsuperuser
   ```
7. Levantar el servidor:
   ```bash
   python manage.py runserver
   ```
8. Abrir en el navegador:
   - Sitio: `http://127.0.0.1:8000/`
   - Django Admin: `http://127.0.0.1:8000/admin/`

## Cómo pasar a MySQL (requisito de la Evaluación 2)

1. Crear la base de datos y el usuario en MySQL (local o en la instancia EC2):
   ```sql
   CREATE DATABASE sgr_evaluacion CHARACTER SET utf8mb4;
   CREATE USER 'sgr_user'@'localhost' IDENTIFIED BY 'una_clave_segura';
   GRANT ALL PRIVILEGES ON sgr_evaluacion.* TO 'sgr_user'@'localhost';
   FLUSH PRIVILEGES;
   ```
2. En el archivo `.env`, cambiar:
   ```
   DB_ENGINE=mysql
   DB_NAME=sgr_evaluacion
   DB_USER=sgr_user
   DB_PASSWORD=una_clave_segura
   DB_HOST=localhost
   DB_PORT=3306
   ```
3. Repetir los pasos 4 a 8 de la sección anterior (`migrate`,
   `cargar_datos_iniciales`, `createsuperuser`, `runserver`).
4. Verificar la estructura de tablas y los registros desde **phpMyAdmin**
   (apuntando a la misma base de datos `sgr_evaluacion`).

El proyecto usa **PyMySQL** como driver (registrado en
`sgr_evaluacion/__init__.py`) para no depender de compilar `mysqlclient`.

## Despliegue en AWS EC2 (resumen)

1. Crear una instancia EC2 con Linux (por ejemplo, Ubuntu Server) y conectarse
   por SSH.
2. Instalar dependencias del sistema:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv git mysql-server phpmyadmin
   ```
3. Configurar MySQL (crear base de datos y usuario, igual que en la sección
   anterior) y anotar las credenciales.
4. Clonar el repositorio desde GitHub:
   ```bash
   git clone URL_DEL_REPOSITORIO
   cd sgr_evaluacion   # o el nombre de la carpeta clonada
   ```
5. Crear el entorno virtual, instalar dependencias y configurar `.env` con
   `DB_ENGINE=mysql` y las credenciales de la instancia:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env   # editar con nano/vim
   ```
6. Aplicar migraciones y cargar los datos:
   ```bash
   python manage.py migrate
   python manage.py cargar_datos_iniciales
   python manage.py createsuperuser
   python manage.py collectstatic --noinput
   ```
7. Levantar el servidor de forma accesible desde fuera de la instancia
   (agregar la IP/DNS pública a `ALLOWED_HOSTS` en `.env`, y abrir el puerto
   en el Security Group de EC2):
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
   Para un despliegue más robusto (recomendado, no obligatorio para la
   evaluación) se puede reemplazar `runserver` por **Gunicorn** detrás de
   **Nginx**.
8. Verificar en el navegador: `http://IP_PUBLICA_EC2:8000/` y
   `http://IP_PUBLICA_EC2:8000/admin/`.

## Control de versiones (Git y GitHub)

```bash
git init
git add .
git commit -m "Evaluación Sumativa 2: migración a base de datos y Django Admin"
git branch -M main
git remote add origin URL_DEL_REPOSITORIO
git push -u origin main
```

Cada versión se marca con un *tag* de Git, para poder volver a cualquiera de ellas:

```bash
git tag -a v2.0 -m "Versión 2.0: nuevos requerimientos octubre 2026"
git push origin --tags
git checkout v1.1      # ver cómo estaba la versión 1.1 (volver con: git checkout main)
```

El archivo `.gitignore` incluido excluye `venv/`, `.env`, `db.sqlite3` y los
archivos de caché de Python, tal como exige la pauta.

## Botones de acción (Agregar / Modificar / Eliminar / Buscar)

Cada listado (`delegaciones`, `gestion` y `organizacion`) incluye los
controles pedidos, y **ya son funcionales de extremo a extremo** (antes
"Agregar/Modificar/Eliminar" solo mostraban una pantalla informativa; esto
se implementó junto con el resto de los cambios de esta sección):

- **Buscar**: filtra los resultados mediante consultas ORM (`icontains` /
  `Q`) al enviar el formulario.
- **Agregar / Modificar**: formularios reales (`ModelForm`) que validan y
  escriben en la base de datos, con mensajes de confirmación.
- **Eliminar**: pide confirmación explícita antes de borrar (y avisa si el
  borrado arrastra registros relacionados, por ejemplo las actividades de
  una delegación).

Toda la administración de datos también sigue disponible desde **Django
Admin**, incluida la acción masiva "Marcar como validadas" sobre
actividades.

## Página pública de Funcionarios

`organizacion:listado` (`/organizacion/funcionarios/`) lista los
funcionarios municipales con su cargo, delegación y rol de acceso
(Funcionario Operativo, Delegado de Delegación, Coordinador Estratégico o
Verificador/Auditor), con búsqueda por nombre, cargo o delegación.

## Notas

- Los datos de `data/actividades.json` y `data/delegaciones.json` se
  conservan solo como fuente para el comando `cargar_datos_iniciales`; la
  aplicación ya no los lee en tiempo de ejecución.
- Los datos de `actividades.json` son ficticios (funcionarios marcados como
  "(ejemplo)"); los de `delegaciones.json` corresponden a información
  institucional pública de la Municipalidad de La Serena.
- Uso de IA (Claude) documentado en la carpeta `docs_ia/` (prompts
  utilizados, respuestas obtenidas y su aplicación en el desarrollo).
