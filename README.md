# SGR La Serena — Evaluación Sumativa 2 (Programación Back End)

Continuación del proyecto desarrollado en la **Evaluación Sumativa 1**: el mismo
caso "Sistema de Gestión de Resultados (SGR)" de las delegaciones de la
Municipalidad de La Serena, ahora migrado desde archivos JSON hacia una
**base de datos relacional**, administrable desde **Django Admin** y pensado
para desplegarse en una instancia **AWS EC2** con control de versiones en
**GitHub**.

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

## Estructura del proyecto

```
sgr_evaluacion/      # Configuración del proyecto (settings, urls raíz)
delegaciones/        # Aplicación 1: información institucional de las delegaciones
  models.py           #   Delegacion
  admin.py            #   Administración de Delegacion
gestion/             # Aplicación 2: actividades / solicitudes registradas
  models.py           #   Categoria, Actividad (FK a Delegacion y Categoria)
  admin.py            #   Administración de Categoria y Actividad
  services.py          #   Agregaciones ORM (resumen por estado, donut)
  management/commands/cargar_datos_iniciales.py  # Migra los JSON de Eval. 1 a la BD
data/                # JSON originales de la Evaluación 1 (fuente para el seed)
static/              # Bootstrap local, CSS propio e imágenes
templates/           # Plantilla base compartida + pantalla "en construcción"
.env.example         # Plantilla de variables de entorno (copiar a .env)
```

## Modelo de datos

- **Delegacion** (`delegaciones`): nombre, slug, encargado, dirección, teléfono,
  correo, territorio, enfoque.
- **Categoria** (`gestion`): catálogo de categorías de actividad (Diserco,
  Social, Seguridad, Organizaciones Comunitarias, etc.).
- **Actividad** (`gestion`): código, fecha, descripción, funcionario, estado
  (Pendiente / En proceso / Realizado), con **ForeignKey** hacia `Delegacion`
  y hacia `Categoria`.

Ambas relaciones (`Actividad → Delegacion`, `Actividad → Categoria`) se
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
5. Cargar los datos de la Evaluación 1 (delegaciones y actividades) en la base
   de datos:
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

El archivo `.gitignore` incluido excluye `venv/`, `.env`, `db.sqlite3` y los
archivos de caché de Python, tal como exige la pauta.

## Botones de acción (Agregar / Modificar / Eliminar / Buscar)

Cada listado (`delegaciones` y `gestion`) incluye los 4 controles pedidos:

- **Buscar**: funcional, filtra los resultados mediante consultas ORM
  (`icontains` / `Q`) mientras se escribe y se envía el formulario.
- **Agregar / Modificar / Eliminar**: enlazan a rutas reales del proyecto
  (`.../nueva/`, `.../<id>/editar/`, `.../<id>/eliminar/`) que hoy muestran
  una pantalla informativa. Su implementación funcional (formularios que
  efectivamente escriban en la base de datos desde la interfaz pública) es
  el alcance de la **Evaluación Sumativa N.º 3**; toda la administración de
  datos (crear, modificar, eliminar) ya está disponible y operativa desde
  **Django Admin**.

## Notas

- Los datos de `data/actividades.json` y `data/delegaciones.json` se
  conservan solo como fuente para el comando `cargar_datos_iniciales`; la
  aplicación ya no los lee en tiempo de ejecución.
- Los datos de `actividades.json` son ficticios (funcionarios marcados como
  "(ejemplo)"); los de `delegaciones.json` corresponden a información
  institucional pública de la Municipalidad de La Serena.
- Uso de IA (Claude) documentado en la carpeta `docs_ia/` (prompts
  utilizados, respuestas obtenidas y su aplicación en el desarrollo).
