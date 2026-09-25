# Uso de IA — Evaluación Sumativa 2 (Programación Back End)

Herramienta utilizada: **Claude** (Anthropic), a través de Claude en modo
Cowork. Este documento resume, por etapa, los prompts utilizados, el tipo de
respuesta obtenida y cómo se aplicó en el desarrollo del proyecto.
Complementa (no reemplaza) los 5 documentos de prompts de la Evaluación 1.

## 1. Punto de partida

**Prompt utilizado (resumen):**
> "Este vendría siendo lo que es la evaluación 1 [se adjuntó el proyecto
> `eval1.zip` y la pauta `Evaluación Sumativa 2.pdf`]. Ahora necesito que me
> hagas la 2 siguiendo casi la misma estructura pero con los cambios que
> pide la evaluación 2."

**Respuesta obtenida / aplicación:** Claude leyó la pauta completa de la
Evaluación 2 y el código de la Evaluación 1 (modelos, vistas, urls, admin,
templates y JSON), identificó los requisitos nuevos (base de datos
relacional, Django Admin, variables de entorno, botones CRUD visuales,
despliegue en EC2, GitHub) y propuso conservar la misma estructura de dos
aplicaciones, mismas rutas y mismo diseño visual, agregando solo lo
necesario para cumplir la nueva pauta.

## 2. Modelado de datos (Django ORM)

**Prompt utilizado (resumen):** se le pidió a Claude diseñar los modelos
Django que reemplazaran los archivos `delegaciones.json` y
`actividades.json`, "considerando todas las entidades necesarias" y
relaciones con `ForeignKey` cuando correspondiera.

**Respuesta obtenida:** Claude propuso 3 modelos: `Delegacion` (app
`delegaciones`), y `Categoria` + `Actividad` (app `gestion`), con
`Actividad.delegacion` y `Actividad.categoria` como `ForeignKey`, y un
`TextChoices` para el campo `estado` (Pendiente / En proceso / Realizado).

**Aplicación:** se implementó tal cual en `delegaciones/models.py` y
`gestion/models.py`, y se generaron las migraciones reales con
`python manage.py makemigrations`.

## 3. Variables de entorno y base de datos

**Prompt utilizado (resumen):** se solicitó que la configuración sensible
(SECRET_KEY, credenciales de base de datos) no quedara escrita en el código,
y que la base de datos fuera relacional y verificable desde phpMyAdmin
(MySQL en EC2), pero que también pudiera probarse en un computador local sin
instalar MySQL.

**Respuesta obtenida:** Claude sugirió usar `python-decouple` con un archivo
`.env` (y su plantilla `.env.example`), y un `DB_ENGINE` configurable entre
`sqlite` (desarrollo local) y `mysql` (EC2 + phpMyAdmin), usando `PyMySQL`
como driver para evitar problemas al compilar `mysqlclient`.

**Aplicación:** se implementó en `sgr_evaluacion/settings.py`,
`sgr_evaluacion/__init__.py` (registro de PyMySQL), `.env.example` y
`.gitignore` (excluyendo `.env` del repositorio).

## 4. Django Admin

**Prompt utilizado (resumen):** se pidió que todas las entidades quedaran
"registradas y operativas" en Django Admin, permitiendo crear, modificar,
eliminar, buscar y navegar entre entidades relacionadas.

**Respuesta obtenida:** Claude propuso `ModelAdmin` personalizados para las
3 entidades, con `list_display`, `search_fields`, `list_filter`,
`prepopulated_fields` (slug de Delegación) y `autocomplete_fields` para
navegar la relación Actividad → Delegación/Categoría.

**Aplicación:** implementado en `delegaciones/admin.py` y
`gestion/admin.py`. Se verificó manualmente (crear, editar y eliminar un
registro de prueba) que el CRUD completo funciona antes de entregar el
proyecto.

## 5. Vistas con ORM y botones de acción

**Prompt utilizado (resumen):** se pidió reemplazar las funciones que leían
los JSON por consultas Django ORM, y agregar a cada listado los botones
"Agregar", "Modificar", "Eliminar" y "Buscar" exigidos por la pauta,
aclarando que solo "Buscar" debía quedar operativo en esta etapa.

**Respuesta obtenida:** Claude reescribió `views.py` de ambas apps usando
`Model.objects`, `select_related`, `Q` (para la búsqueda) y agregó rutas y
vistas "placeholder" para crear/editar/eliminar, que muestran una pantalla
informativa reutilizable (`templates/en_construccion.html`) en vez de dejar
los botones sin destino.

**Aplicación:** implementado en `delegaciones/views.py`, `gestion/views.py`,
sus respectivos `urls.py`, y en los templates de listado (botones + barra de
búsqueda).

## 6. Migración de los datos JSON → base de datos

**Prompt utilizado (resumen):** se solicitó una forma de migrar
completamente la información ya cargada en los JSON de la Evaluación 1
hacia la nueva base de datos, sin perder la relación entre actividades y
delegaciones.

**Respuesta obtenida:** Claude propuso un comando de gestión de Django
(`cargar_datos_iniciales`) que lee ambos JSON y crea/actualiza los registros
correspondientes con `update_or_create`, siendo seguro de ejecutar más de
una vez.

**Aplicación:** implementado en
`gestion/management/commands/cargar_datos_iniciales.py`. Se probó localmente
con SQLite, confirmando la carga de las 6 delegaciones y las 8 actividades.

---

*Este documento fue redactado a partir del trabajo real realizado junto a
Claude durante esta etapa; se recomienda completar con capturas de pantalla
propias (terminal, phpMyAdmin, GitHub, EC2) para el Documento Técnico final.*
