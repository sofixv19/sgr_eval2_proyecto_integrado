\### Elias Medina — Mi parte en el SGR



\## Módulos a cargo

\- Validadores: revisan el RUT (dígito verificador), el teléfono y los nombres antes de guardar.

\- Funcionarios: crear, modificar y eliminar funcionarios, cada uno con su cuenta de acceso y una contraseña temporal.

\- Organización: los cargos y las funciones de cada cargo.

\- Comunidad: territorios, vecinos, socios y dirigentes de las juntas de vecinos, hitos y tipos de atención.

\- Reglas del cliente: sin nombre y teléfono no hay puntaje, máximo 7 registros por día y cierre semanal.



\## Pruebas que reviso

\- CP-VAL (10), CP-FUN (11), CP-ORG (7), CP-COM (10), CP-V2 (16) y CP-EXP (2).

\- Ejemplo: CP-COM-003 rechaza un vecino con RUT inválido o repetido.



\## Archivos principales

comun/validadores.py, organizacion/forms.py, territorio/models.py



