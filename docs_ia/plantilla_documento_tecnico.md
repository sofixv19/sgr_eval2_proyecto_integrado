# Documento Técnico — Evaluación Sumativa 2

> Plantilla para completar y exportar como PDF o Word antes de la entrega.
> Reemplazar cada sección `[COMPLETAR]` con la información real del proyecto
> y las capturas de pantalla propias (EC2, GitHub, phpMyAdmin).

## 1. Descripción del proyecto

- **Objetivo:** Transformar el prototipo de la Evaluación 1 (SGR La Serena)
  en una aplicación web funcional, con persistencia en base de datos,
  administrable desde Django Admin y desplegada en AWS EC2.
- **Temática elegida:** Delegaciones municipales y gestión de actividades
  territoriales, Municipalidad de La Serena.
- **Funcionalidades implementadas:**
  - Modelos Django (`Delegacion`, `Categoria`, `Actividad`) con relaciones
    `ForeignKey`.
  - Migración completa de los datos desde JSON hacia la base de datos
    (comando `cargar_datos_iniciales`).
  - Django Admin con CRUD completo (crear, modificar, eliminar, buscar,
    navegar relaciones) para las 3 entidades.
  - Vistas públicas que consultan la información mediante Django ORM.
  - Botones "Agregar / Modificar / Eliminar / Buscar" en los listados
    (Buscar operativo; el resto enlaza a rutas reales, listas para su
    implementación funcional en la Evaluación 3).
  - Configuración sensible cargada desde variables de entorno (`.env`).
  - [COMPLETAR: agregar cualquier funcionalidad adicional implementada]

## 2. Arquitectura

- **Estructura de carpetas:** ver `README.md` del proyecto.
- **Aplicaciones desarrolladas:** `delegaciones` (institucional) y `gestion`
  (actividades), ambas incluidas desde `sgr_evaluacion/urls.py`.
- **Base de datos utilizada:** MySQL (instancia EC2, administrada también
  desde phpMyAdmin). SQLite se usa solo como alternativa de desarrollo
  local.

## 3. Evidencia AWS

- [COMPLETAR: captura de la instancia EC2 en la consola de AWS]
- [COMPLETAR: captura de la terminal Linux conectada a la instancia]
- [COMPLETAR: captura del proyecto ejecutándose (`runserver` o servidor web)
  accedido desde el navegador]

## 4. Evidencia GitHub

- [COMPLETAR: captura del repositorio en GitHub]
- [COMPLETAR: captura del historial de commits]
- [COMPLETAR: captura de `git clone URL_DEL_REPOSITORIO` ejecutado en la
  instancia EC2]

## 5. Evidencia de Base de Datos (Django)

- [COMPLETAR: captura de `models.py` de ambas apps]
- [COMPLETAR: captura de la carpeta `migrations/` y/o de la salida de
  `python manage.py showmigrations`]
- [COMPLETAR: captura de `python manage.py migrate` ejecutado en EC2]

## 6. Evidencia phpMyAdmin

- [COMPLETAR: captura mostrando las tablas `delegaciones_delegacion`,
  `gestion_categoria`, `gestion_actividad`, etc.]
- [COMPLETAR: captura de la estructura de alguna tabla (columnas, llaves)]
- [COMPLETAR: captura de registros almacenados]
- [COMPLETAR: captura evidenciando la relación (clave foránea) entre
  `gestion_actividad` y `delegaciones_delegacion`]

## 7. Evidencia de uso de IA

Ver detalle completo en `docs_ia/prompts_utilizados_evaluacion_2.md`
(prompts utilizados, respuestas obtenidas y su aplicación en el desarrollo).

- [COMPLETAR: agregar capturas propias de la conversación con la IA si el
  profesor las solicita explícitamente]
