# Cómo trabaja el equipo en el repositorio

La Guía de la Evaluación 3 pide que la colaboración se pueda verificar en el repositorio: ramas, commits identificables, revisión o integración de cambios y distribución de tareas.

## 1. Cada integrante con su propia cuenta

Cada uno configura su nombre y correo **una vez** en su computador, para que sus commits queden a su nombre:

```bash
git config --global user.name "Nombre Apellido"
git config --global user.email "correo@inacapmail.cl"
```

## 2. Una rama por tarea

La rama `main` siempre funciona. Cada tarea del tablero (Jira) se trabaja en su propia rama:

```bash
git checkout main
git pull pi main
git checkout -b HU-25-tubo-de-cartas     # código de la historia + descripción corta
# ... cambios ...
python manage.py test                     # todas las pruebas deben pasar
flake8                                    # sin observaciones
git add -A
git commit -m "HU-25: Tubo de cartas por delegación"
git push pi HU-25-tubo-de-cartas
```

**Nunca** usar `git push` sin indicar el remoto: el remoto del Proyecto Integrado es `pi`.

## 3. Pull request y revisión

1. En GitHub se abre un *pull request* de la rama hacia `main`.
2. Otro integrante lo revisa (que las pruebas pasen y que cumpla la Definición de Terminado) y lo aprueba con un comentario.
3. Se integra con "Merge" y se borra la rama.

## 4. Distribución de tareas

| Integrante | Módulos a cargo (código y pruebas) |
|---|---|
| Sofía Veliz | Autenticación, control de acceso, roles, cambio y recuperación de contraseña (CP-LOGIN, CP-ACC, CP-ROL, CP-CLA), perfiles, seguridad, auditoría y respaldo (CP-PERF, CP-SEG, CP-AUD, CP-RES, CP-DEM), despliegue en AWS |
| Elías Medina | Validadores, funcionarios, organización, comunidad: vecinos, socios y dirigentes (CP-VAL, CP-FUN, CP-ORG, CP-COM), reglas del cliente y exportación (CP-V2, CP-EXP) |
| Ignacio Sepúlveda | Delegaciones, categorías, cargos, Tubo de seguimiento y Tubo de cartas (CP-DEL, CP-CAT, CP-CAR, CP-AGE, CP-TUB), filtros, alertas y dashboard (CP-FIL, CP-ALE, CP-DAS) |
| Diego Villalobos | Trimestres, metas, actividades, verificación y gestiones sociales (CP-PER, CP-MET, CP-ACT, CP-VLD, CP-VER, CP-GSO), códigos, evidencias y cumplimiento (CP-COD, CP-EVI, CP-CUM, CP-PCE) |

La distribución de las versiones 1.0 a 2.2 sigue el Plan de Pruebas de la Evaluación 2. El equipo ajusta esta tabla si cambia algún responsable.

## 5. Versiones

Al cerrar un sprint se actualiza `SGR_VERSION`, el `CHANGELOG.md` y se crea el tag (`git tag v3.0`), que se sube con `git push pi --tags`.
