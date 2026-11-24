"""
Genera docs/pruebas/Protocolo_Pruebas_SGR_v3.xlsx (Plan y Protocolo de Pruebas, versión 3.0).

Fuentes (todas dentro del repositorio):
  - resultados_pruebas.csv ............ corrida real de `python plan_pruebas.py` (pruebas automáticas)
  - docs/pruebas/resultados_manuales.json  corrida final del protocolo manual (navegador)
  - docs/pruebas/ejecuciones/*.log ..... registro de cada ejecución
  - INCIDENCIAS.md ..................... defectos e incidencias con su corrección

Uso (desde la raíz del proyecto):
    python plan_pruebas.py                    # 1) vuelve a correr las pruebas automáticas
    python docs/pruebas/generar_protocolo.py  # 2) regenera la planilla
"""
import csv
import json
import os
import re

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.properties import PageSetupProperties

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SALIDA = os.path.join(RAIZ, 'docs', 'pruebas', 'Protocolo_Pruebas_SGR_v3.xlsx')
FECHA_AUTO = '23-11-2026'
VERSION = '3.0'

SOFIA, ELIAS, IGNACIO, DIEGO = 'Sofía Veliz', 'Elías Medina', 'Ignacio Sepúlveda', 'Diego Villalobos'

# Prefijo -> (módulo, requerimiento, prioridad, perfil, precondiciones, datos de prueba, responsable)
ESC = 'BD de prueba creada por Django; escenario base con delegaciones Rural y Centro, trimestre vigente y cuentas por rol'
GRUPOS = {
    'CP-ACC': ('Control de acceso', 'HU-26 · RF-001, RNF-004', 'Alta', 'Anónimo / Funcionario',
               ESC, 'Rutas internas, cuenta funcionario', SOFIA),
    'CP-LOGIN': ('Autenticación', 'HU-26 · RF-001, RNF-005', 'Alta', 'Todos los roles',
                 ESC, 'Usuario o correo + contraseña válidos e inválidos', SOFIA),
    'CP-ROL': ('Roles y permisos', 'HU-26 · RF-002 (configurar_roles)', 'Alta', 'Administrador',
               ESC + '; grupos creados con configurar_roles', 'Grupos Administrador, Coordinador, Delegado, Funcionario, Verificador', SOFIA),
    'CP-CLA': ('Contraseñas', 'Guía Ev. 3 · contraseña temporal, cambio y recuperación', 'Alta', 'Delegado / Funcionario',
               ESC + '; correo en modo archivo (logs/correos)', 'Cuenta nueva con clave temporal; correo registrado', SOFIA),
    'CP-PERF': ('Perfiles por rol', 'HU-26 · RNF-004 (mínimo privilegio)', 'Alta', 'Todos los roles',
                ESC, 'Actividades de dos delegaciones y dos funcionarios', SOFIA),
    'CP-SEG': ('Seguridad (OWASP)', 'RNF-006, RNF-007 · inyección SQL, XSS, CSRF, IDOR', 'Alta', 'Funcionario / atacante',
               ESC, "Texto malicioso: ' OR 1=1 --, <script>, POST sin token", SOFIA),
    'CP-AUD': ('Auditoría', 'HU-30 · RF-036, RNF-008', 'Alta', 'Verificador / Funcionario',
               ESC, 'Altas, cambios, validaciones e intentos de acceso', SOFIA),
    'CP-RES': ('Respaldo y recuperación', 'Guía Ev. 3 · respaldo de BD y archivos', 'Media', 'Administrador (consola)',
               ESC, 'Datos de ejemplo + archivo de evidencia', SOFIA),
    'CP-DEM': ('Datos de demostración', 'Soporte a la demo (cargar_datos_iniciales, reiniciar_demo)', 'Baja', 'Administrador (consola)',
               ESC, 'Equipo de ejemplo y nombres editados', SOFIA),
    'CP-VAL': ('Validadores', 'RNF-010 · RUT, teléfono, correo y textos', 'Alta', 'No aplica (función)',
               'Sin datos previos', 'RUT con y sin dígito verificador correcto; teléfonos; textos cortos', ELIAS),
    'CP-FUN': ('Funcionarios', 'HU-26 · RF-002', 'Alta', 'Administrador / Delegado',
               ESC, 'Funcionario con RUT, correo y cargo', ELIAS),
    'CP-ORG': ('Organización (funciones por cargo)', 'HU-04 · RF-003, RF-006', 'Alta', 'Coordinador',
               ESC, 'Cargos y funciones por cargo', ELIAS),
    'CP-COM': ('Comunidad (territorios, vecinos, socios, hitos)', 'HU-03 · Guía Ev. 3 · CRUD de comunidad', 'Alta', 'Delegado / Funcionario',
               ESC, 'Vecinos con RUT válido, junta de vecinos, hito, tipos y subtipos de atención', ELIAS),
    'CP-V2': ('Reglas del cliente', 'RF-039 a RF-048', 'Alta', 'Funcionario / Delegado',
              ESC, 'Actividades del día, semana anterior, felicitaciones y ausencias', ELIAS),
    'CP-EXP': ('Exportación', 'HU-20 · RF-032, RF-033', 'Media', 'Delegado / Coordinador',
               ESC, 'Actividades del trimestre', ELIAS),
    'CP-DEL': ('Delegaciones', 'HU-26 · RF-001', 'Alta', 'Administrador / Coordinador',
               ESC, 'Delegación con nombre, sector y responsable', IGNACIO),
    'CP-CAT': ('Categorías', 'HU-27 · RF-004', 'Alta', 'Administrador',
               ESC, 'Categorías con nombre único', IGNACIO),
    'CP-CAR': ('Cargos', 'HU-04 · RF-003', 'Alta', 'Administrador / Coordinador',
               ESC, 'Cargos con nombre único', IGNACIO),
    'CP-AGE': ('Tubo de seguimiento (compromisos)', 'HU-02, HU-12 a HU-15 · RF-016 a RF-021', 'Alta', 'Delegado / Funcionario',
               ESC, 'Compromisos con responsable, fecha y estado', IGNACIO),
    'CP-TUB': ('Tubo de cartas', 'Guía Ev. 3 · Tubo de cartas por delegación', 'Alta', 'Funcionario / Delegado',
               ESC, 'Cartas de dos funcionarias de la misma delegación', IGNACIO),
    'CP-FIL': ('Búsqueda y filtros', 'HU-29 · RF-032', 'Media', 'Delegado',
               ESC, 'Actividades con distintos estados y fechas', IGNACIO),
    'CP-ALE': ('Alertas', 'HU-19, HU-21, HU-31 · RF-037', 'Media', 'Delegado / Coordinador',
               ESC, 'Funcionarios sin registros y compromisos vencidos', IGNACIO),
    'CP-DAS': ('Dashboard', 'Guía Ev. 3 · dashboard con filtros y gráficos', 'Alta', 'Todos los roles',
               ESC, 'Actividades aprobadas y pendientes de varias delegaciones', IGNACIO),
    'CP-PER': ('Trimestres', 'HU-28 · RF-005', 'Alta', 'Coordinador',
               ESC, 'Trimestres con fechas de inicio y término', DIEGO),
    'CP-MET': ('Metas', 'HU-05 · RF-005 a RF-007', 'Alta', 'Coordinador / Delegado',
               ESC, 'Metas por funcionario con ponderador', DIEGO),
    'CP-ACT': ('Registro de actividades', 'HU-01 · RF-009, RF-010, RF-014', 'Alta', 'Funcionario',
               ESC, 'Actividad con fecha, categoría, vecino y teléfono', DIEGO),
    'CP-VLD': ('Validación de actividades', 'HU-11 · RF-013, RF-014', 'Alta', 'Delegado',
               ESC, 'Actividades pendientes de su delegación y de otra', DIEGO),
    'CP-VER': ('Verificación (más antecedentes, bloqueo de aprobadas)', 'Guía Ev. 3 · estados de verificación', 'Alta', 'Delegado / Funcionario / Administrador',
               ESC, 'Actividad pendiente con evidencia', DIEGO),
    'CP-GSO': ('Gestión social e ingreso al Tubo', 'HU-03 · RF-004, RF-015', 'Alta', 'Funcionario',
               ESC + '; vecino y subtipo de atención creados', 'Vecina Rosa Pérez Díaz, RUT 11.111.111-1, subtipo PGU', DIEGO),
    'CP-COD': ('Códigos verificadores', 'HU-10 · RF-011', 'Alta', 'Funcionario',
               ESC, 'Actividades de distintas áreas', DIEGO),
    'CP-EVI': ('Evidencias', 'HU-09 · RF-012, RNF-017', 'Alta', 'Funcionario',
               ESC, 'Archivos JPG, PNG, PDF y no permitidos; tamaño > 5 MB', DIEGO),
    'CP-CUM': ('Cumplimiento y semáforo', 'HU-07, HU-16, HU-17 · RF-023 a RF-027', 'Alta', 'Funcionario / Delegado',
               ESC, 'Metas y actividades aprobadas', DIEGO),
    'CP-PCE': ('Trimestre cerrado', 'HU-25, HU-28 · RN-013', 'Media', 'Funcionario',
               ESC + '; trimestre anterior cerrado', 'Actividad de un trimestre cerrado', DIEGO),
}

# Defectos encontrados (ID = INCIDENCIAS.md). caso -> defecto
DEFECTOS = [
    ('INC-16', '24-11-2026', 'Recorrido de todas las páginas con los 5 roles',
     'Las páginas "Eliminar" de territorios, vecinos, socios/dirigentes e hitos respondían error 500.', 'Alta',
     'La vista pasaba la delegación al formulario simple de confirmación de borrado.',
     'Solo los formularios de crear/editar reciben la delegación (territorio/views.py); CP-COM-001 y 004 ampliados.',
     '3.0.1', 'CP-COM-001 y CP-COM-004: Aprobado; recorrido con 0 errores', 'Corregido'),
    # id, fecha, detectado_por, descripcion, severidad, causa, correccion, version, reejecucion, estado
    ('INC-15', '23-11-2026', 'flake8 (revisión estática)', 'Línea de más de 120 caracteres en comun/auditoria.py.',
     'Baja', 'Diccionario de acciones escrito en una sola línea.', 'Se movió a la constante ACCIONES_VALIDACION.',
     '3.0', 'flake8 sin avisos', 'Corregido'),
    ('INC-14', '23-11-2026', 'Revisión visual del dashboard (CP-DAS)',
     'Los gráficos del dashboard mostraban decimales en el eje (0,5 actividades) y la línea de tendencia bajaba de 0.',
     'Baja', 'Configuración por defecto de Chart.js (curva suavizada y pasos decimales).',
     'Línea recta (tension 0), ejes con números enteros y barras horizontales para nombres largos.',
     '3.0', 'CP-DAS-001 a 003 y CP-MAN-11: Aprobado', 'Corregido'),
    ('INC-13', '23-11-2026', 'CP-MAN-08 (ejecución 3)',
     'Al pasar una gestión social al Tubo, el compromiso no se guardaba: faltaba el territorio, que es obligatorio.',
     'Alta', 'El formulario del compromiso copiaba el RUT del vecino pero no su territorio.',
     'gestion/views_agenda.py completa el territorio desde el vecino; nueva prueba CP-GSO-005 y CP-MAN-07 revisa que el compromiso se cree.',
     '3.0', 'CP-GSO-005 y CP-MAN-07/08 ejecución 4: Aprobado', 'Corregido'),
    ('INC-10', '23-11-2026', 'Regresión automática (suite completa)',
     'Con las contraseñas temporales, 180 pruebas existentes redirigían a "Cambiar contraseña".',
     'Media', 'Las cuentas del escenario de pruebas se creaban como temporales.',
     'sincronizar_cuenta(..., temporal=False) en las pruebas; la marca temporal se prueba aparte (CP-CLA-008).',
     '3.0', 'Suite completa: 217/217 aprobadas', 'Corregido'),
    ('INC-09', '23-11-2026', 'CP-VER-001',
     'La auditoría no guardaba la acción "Solicitud de antecedentes".', 'Media',
     'El campo accion admite 20 caracteres.', 'Acción "Más antecedentes" agregada a las opciones (migración comun/0002).',
     '3.0', 'CP-VER-001: Aprobado', 'Corregido'),
    ('INC-08', '23-11-2026', 'CP-GSO-001 a 004 (primera corrida)',
     'El formulario de gestión social fallaba con KeyError: organizacion.', 'Alta',
     'El formulario hijo no tiene el campo que el padre configuraba.', 'El formulario padre solo configura los campos que existen.',
     '3.0', 'CP-GSO-001 a 004: Aprobado', 'Corregido'),
    ('INC-06', '12-11-2026', 'Prueba en AWS tras actualizar',
     'Los nombres editados desde la página volvían a los de ejemplo después de cada actualización.', 'Media',
     'cargar_datos_iniciales usaba update_or_create en cada despliegue.', 'Solo crea lo que falta (busca por correo o RUT).',
     '2.2.1', 'CP-DEM-002: Aprobado', 'Corregido'),
    ('INC-07', '14-11-2026', 'pip-audit (dependencias)',
     'Django 4.2 sin soporte desde abril de 2026 (9 avisos).', 'Media',
     'Amazon Linux 2023 trae Python 3.9; Django 5.2 necesita 3.10 o más.', 'Planificado: Python 3.11 y Django 5.2 LTS (recomendación R1).',
     '—', 'Pendiente', 'Abierto'),
]
DEFECTO_DE_CASO = {
    'CP-GSO-001': 'INC-08', 'CP-GSO-002': 'INC-08', 'CP-GSO-003': 'INC-08', 'CP-GSO-004': 'INC-08',
    'CP-GSO-005': 'INC-13', 'CP-COM-001': 'INC-16', 'CP-COM-004': 'INC-16', 'CP-VER-001': 'INC-09', 'CP-CLA-008': 'INC-10', 'CP-DEM-002': 'INC-06',
}

# Protocolo manual (ejecutado en navegador Chromium con docs/pruebas/protocolo_manual.js)
MANUALES = [
    ('CP-MAN-01', 'Cada rol entra a su propio panel', 'HU-26 · RF-001', 'Alta', 'Todos', 'Datos de demostración cargados',
     'Cuentas funcionario.rural, delegado.rural, coordinador.sgr, verificador.sgr, admin.sgr',
     ['Abrir /cuentas/ingresar/', 'Ingresar con cada cuenta demo', 'Revisar el menú superior', 'Cerrar sesión y repetir con la siguiente'],
     'Cada rol ve su panel y solo su menú.', ['MAN-01_panel_delegado.png'], SOFIA),
    ('CP-MAN-02', 'Cuenta nueva con clave temporal', 'Guía Ev. 3 · contraseña temporal', 'Alta', 'Delegado → Funcionario nuevo',
     'Sesión de Delegado', 'Funcionario Paula Rivas Prueba, RUT 16.000.000-7, correo p.rivas.prueba@laserena.cl',
     ['Ir a Funcionarios › Nuevo', 'Completar nombre, RUT, correo y cargo; Guardar', 'Anotar usuario y clave temporal del mensaje',
      'Cerrar sesión e ingresar con la cuenta nueva', 'Intentar abrir /gestion/', 'Cambiar la contraseña', 'Volver a abrir /gestion/'],
     'Mientras la clave sea temporal, toda página lleva a "Cambiar contraseña"; después del cambio se accede normal.',
     ['MAN-02_cambio_obligatorio.png'], SOFIA),
    ('CP-MAN-03', 'Recuperar contraseña por correo', 'Guía Ev. 3 · recuperación de contraseña', 'Alta', 'Funcionario (sin sesión)',
     'Cuenta de CP-MAN-02; correo en modo archivo', 'Correo p.rivas.prueba@laserena.cl',
     ['En el login, clic en "¿Olvidó su contraseña?"', 'Escribir el correo y enviar', 'Abrir el enlace del correo',
      'Escribir la clave nueva dos veces', 'Volver a abrir el mismo enlace', 'Ingresar con la clave nueva'],
     'Llega el enlace, permite crear la clave una sola vez y luego queda inválido.',
     ['MAN-03_revise_correo.png', 'MAN-03_restablecida.png'], SOFIA),
    ('CP-MAN-04', 'Registrar actividad con evidencia', 'HU-01, HU-09 · RF-009 a RF-012', 'Alta', 'Funcionario',
     'Sesión de funcionario.rural', 'Fecha de hoy, vecina Rosa Pérez, +56 9 1234 5678, imagen JPG',
     ['Ir a Registrar › Actividad', 'Elegir categoría y fecha de hoy', 'Escribir descripción, nombre y teléfono',
      'Adjuntar la evidencia', 'Guardar'],
     'Se asigna código automático, queda Pendiente y muestra "Suma puntaje".', ['MAN-04_actividad_registrada.png'], DIEGO),
    ('CP-MAN-05', 'Pedir más antecedentes y aprobar', 'Guía Ev. 3 · verificación', 'Alta', 'Delegado y Funcionario',
     'Actividad de CP-MAN-04 pendiente', 'Observación "Falta la lista de asistencia"',
     ['Delegado abre la actividad', 'Elige "Pedir más antecedentes" y escribe la observación', 'Funcionario sube otra evidencia',
      'Revisar que vuelva a Pendiente', 'Delegado la aprueba'],
     'Pasa por Faltan antecedentes → Pendiente → Validada.', ['MAN-05_mas_antecedentes.png', 'MAN-05_aprobada.png'], DIEGO),
    ('CP-MAN-06', 'Lo aprobado no se modifica', 'Guía Ev. 3 · bloqueo de registros aprobados', 'Alta', 'Funcionario y Administrador',
     'Actividad aprobada en CP-MAN-05', 'URL de edición de la actividad',
     ['Funcionario abre la URL de edición', 'Administrador abre la misma URL'],
     'Ambos reciben 403 (prohibido).', ['MAN-06_aprobada_bloqueada.png'], DIEGO),
    ('CP-MAN-07', 'Gestión social con autocompletar e ingreso al Tubo', 'HU-03 · Guía Ev. 3 · autocompletar e ingreso al Tubo', 'Alta',
     'Funcionario', 'Vecinos de demostración con territorio', 'Escribir "Rosa" en el buscador de vecinos; subtipo de atención',
     ['Ir a Registrar › Gestión social', 'Elegir subtipo, fecha y descripción', 'Escribir "Rosa" y elegir la vecina de la lista',
      'Marcar "Ingresar al Tubo" y guardar', 'Revisar RUT y territorio en el compromiso', 'Poner fecha de compromiso y guardar'],
     'Los datos del vecino se completan solos y el compromiso queda en el Tubo.',
     ['MAN-07_autocompletar.png', 'MAN-07_ingreso_al_tubo.png'], DIEGO),
    ('CP-MAN-08', 'Búsqueda dinámica en el Tubo', 'Guía Ev. 3 · búsqueda dinámica', 'Media', 'Delegado',
     'Compromiso de CP-MAN-07 creado', 'Primeros 6 caracteres del RUT',
     ['Abrir Tubo › Seguimiento', 'Escribir parte del RUT en el buscador', 'Mirar el contador de filas'],
     'La lista se filtra mientras se escribe, sin recargar.', ['MAN-08_busqueda_dinamica.png'], IGNACIO),
    ('CP-MAN-09', 'Tubo de cartas por delegación', 'Guía Ev. 3 · Tubo de cartas', 'Alta', 'Funcionaria nueva y Funcionario',
     'Cuenta de CP-MAN-02/03', 'Carta de "Club Adulto Mayor (protocolo)"',
     ['Funcionaria nueva registra una carta', 'Funcionario de la misma delegación abre Tubo › Cartas'],
     'La carta se ve en el Tubo de la delegación, en solo lectura para el otro funcionario.', ['MAN-09_tubo_cartas.png'], IGNACIO),
    ('CP-MAN-10', 'Semana cerrada', 'RF-043 · cierre semanal', 'Alta', 'Funcionario',
     'Sesión de funcionario.rural', 'Fecha de hace 12 días',
     ['Ir a Registrar › Actividad', 'Poner una fecha de hace 12 días', 'Guardar'],
     'Se rechaza con el mensaje de semana cerrada.', ['MAN-10_semana_cerrada.png'], ELIAS),
    ('CP-MAN-11', 'Dashboard con filtros', 'Guía Ev. 3 · dashboard', 'Alta', 'Delegado',
     'Actividades de la delegación', 'Filtro por un funcionario',
     ['Abrir Dashboard', 'Revisar que estén los gráficos', 'Elegir un funcionario y Aplicar'],
     'Se ven los gráficos y, al filtrar, solo los datos de ese funcionario.', ['MAN-11_dashboard_filtrado.png'], IGNACIO),
    ('CP-MAN-12', 'Acceso denegado queda auditado', 'HU-30 · RNF-004, RNF-008', 'Alta', 'Funcionario y Verificador',
     'Sesión de funcionario.rural', 'URL /auditoria/',
     ['Funcionario escribe /auditoria/ en la dirección', 'Verificador abre Auditoría'],
     'El funcionario recibe 403 y el intento aparece como "Acceso denegado".', ['MAN-12_acceso_denegado_auditado.png'], SOFIA),
]

# Historial de ejecuciones del protocolo manual (docs/pruebas/ejecuciones/). Bloqueado = el caso no
# se pudo probar por un error del guion o de los datos de prueba (no del sistema).
HISTORIAL_MANUAL = {
    1: {'01': 'Aprobado', '11': 'Aprobado', '12': 'Aprobado'},
    2: {'01': 'Aprobado', '10': 'Aprobado', '11': 'Aprobado', '12': 'Aprobado'},
    3: {'02': 'Bloqueado', '08': 'Fallido'},
    4: {},
}
CAUSA_EJEC = {
    1: 'Guion: el selector del botón Guardar tomaba "Cerrar sesión"; faltaba la carpeta de correos. Casos dependientes bloqueados.',
    2: 'Datos de prueba: fecha en UTC (el sistema la vio como futura) y RUT 16.000.000-1 con dígito verificador inválido.',
    3: 'CP-MAN-02: la clave nueva de prueba se parecía al nombre y el validador la rechazó (comportamiento correcto). '
       'CP-MAN-08: defecto real INC-13 (el compromiso no se guardaba sin territorio).',
    4: 'Ejecución final después de corregir INC-13 y el guion.',
}

# ---------------------------------------------------------------- estilos
ARIAL = 'Arial'
TINTA, BORDE, CABECERA, SUAVE = '1F2A37', 'C9CED6', '24364B', 'F3F5F8'
F_CAB = Font(name=ARIAL, bold=True, color='FFFFFF', size=10)
F_NORMAL = Font(name=ARIAL, size=10, color=TINTA)
F_NEGRITA = Font(name=ARIAL, size=10, bold=True, color=TINTA)
F_TITULO = Font(name=ARIAL, size=16, bold=True, color=TINTA)
F_SUB = Font(name=ARIAL, size=11, color='4B5563')
F_NOTA = Font(name=ARIAL, size=9, italic=True, color='6B7280')
RELLENO_CAB = PatternFill('solid', fgColor=CABECERA)
RELLENO_SUAVE = PatternFill('solid', fgColor=SUAVE)
LINEA = Side(style='thin', color=BORDE)
CAJA = Border(left=LINEA, right=LINEA, top=LINEA, bottom=LINEA)
ARRIBA = Alignment(vertical='top', wrap_text=True)
CENTRO = Alignment(horizontal='center', vertical='top', wrap_text=True)

ESTADOS = {'Aprobado': ('E3F1EC', '1F5E4E'), 'Fallido': ('F8E1E1', '8A1C1C'), 'Bloqueado': ('FBEFD9', '7A5410'),
           'Corregido': ('E3F1EC', '1F5E4E'), 'Abierto': ('FBEFD9', '7A5410')}


def cabecera(ws, fila, titulos, anchos):
    for i, (t, a) in enumerate(zip(titulos, anchos), start=1):
        c = ws.cell(row=fila, column=i, value=t)
        c.font, c.fill, c.alignment, c.border = F_CAB, RELLENO_CAB, Alignment(vertical='center', wrap_text=True), CAJA
        ws.column_dimensions[get_column_letter(i)].width = a
    ws.row_dimensions[fila].height = 30


def fila_datos(ws, fila, valores, centrar=()):
    for i, v in enumerate(valores, start=1):
        c = ws.cell(row=fila, column=i, value=v)
        c.font, c.border = F_NORMAL, CAJA
        c.alignment = CENTRO if i in centrar else ARRIBA


def colorear_estado(ws, rango):
    for texto, (fondo, letra) in ESTADOS.items():
        ws.conditional_formatting.add(rango, CellIsRule(operator='equal', formula=[f'"{texto}"'],
                                                        fill=PatternFill('solid', fgColor=fondo),
                                                        font=Font(name=ARIAL, bold=True, color=letra)))


def lista_estados(ws, rango, opciones):
    dv = DataValidation(type='list', formula1='"' + ','.join(opciones) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(rango)


def nombre_desde_metodo(prueba):
    metodo = prueba.rsplit('.', 1)[-1]
    metodo = re.sub(r'^test_cp_[a-z0-9]+_\d+_', '', metodo).replace('test_', '')
    texto = metodo.replace('_', ' ').strip()
    return texto[:1].upper() + texto[1:]


def estado_en_ejecucion(n, num):
    """Ejecuciones 1 y 2 listan los aprobados (el resto quedó bloqueado); 3 y 4 listan las excepciones."""
    h = HISTORIAL_MANUAL[n]
    if n in (1, 2):
        return h.get(num, 'Bloqueado')
    return h.get(num, 'Aprobado')


def prefijo(codigo):
    return re.sub(r'-\d+$', '', codigo)


# ---------------------------------------------------------------- hojas
def hoja_resumen(wb, n_auto, n_man):
    ws = wb.active
    ws.title = 'Resumen'
    ws.sheet_view.showGridLines = False
    ws.column_dimensions['A'].width = 3
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 95
    ws['B2'] = 'Plan y Protocolo de Pruebas · SGR La Serena'
    ws['B2'].font = F_TITULO
    ws['B3'] = f'Sistema de Gestión de Registros · versión {VERSION} · Proyecto Integrado, Evaluación 3'
    ws['B3'].font = F_SUB
    filas = [
        ('Equipo', f'{SOFIA}, {ELIAS}, {IGNACIO}, {DIEGO}'),
        ('Fecha de ejecución', f'{FECHA_AUTO} (pruebas automáticas y ejecución final del protocolo manual)'),
        ('Pruebas automáticas', f'{n_auto} casos (Django TestCase). Hoja "Protocolo".'),
        ('Pruebas manuales', f'{n_man} casos de punta a punta en navegador. Hoja "Protocolo manual".'),
        ('Plan', 'Objetivo, alcance, tipos de prueba, entorno y criterios. Hoja "Plan".'),
        ('Defectos', 'Defectos encontrados, corrección y reejecución. Hoja "Defectos" (IDs de INCIDENCIAS.md).'),
        ('Indicadores', 'Planificadas, ejecutadas, aprobadas, fallidas, bloqueadas, corregidas y reejecutadas (fórmulas). Hoja "Indicadores".'),
        ('Historial', 'Cada ejecución del protocolo manual con su resultado. Hoja "Ejecuciones".'),
        ('Evidencias', 'docs/pruebas/evidencias/ (capturas) y docs/pruebas/ejecuciones/ (registros de cada corrida).'),
        ('Cómo regenerar', 'python plan_pruebas.py  →  python docs/pruebas/generar_protocolo.py'),
        ('Reejecutar un caso', 'python manage.py test <columna "Prueba (código)">   ·   manual: SGR_URL=... SGR_CLAVE_DEMO=... node docs/pruebas/protocolo_manual.js'),
        ('Estados', 'Aprobado = coincide con lo esperado · Fallido = no coincide (defecto) · Bloqueado = no se pudo probar (guion o datos de prueba).'),
    ]
    for i, (k, v) in enumerate(filas, start=5):
        ws.cell(row=i, column=2, value=k).font = F_NEGRITA
        c = ws.cell(row=i, column=3, value=v)
        c.font, c.alignment = F_NORMAL, ARRIBA
    ws.cell(row=5 + len(filas) + 1, column=2,
            value='Las contraseñas de las cuentas de prueba no se guardan en esta planilla ni en el repositorio.').font = F_NOTA


def hoja_plan(wb):
    ws = wb.create_sheet('Plan')
    ws.sheet_view.showGridLines = False
    cabecera(ws, 1, ['Elemento', 'Definición'], [28, 110])
    filas = [
        ('Objetivo', 'Comprobar que la versión 3.0 cumple los requerimientos de la Guía de la Evaluación 3 y las HU del cliente, '
                     'sin romper lo que ya funcionaba (regresión).'),
        ('Alcance', 'Autenticación, roles, contraseñas temporales y recuperación; delegaciones, funcionarios, cargos, metas y trimestres; '
                    'comunidad (territorios, vecinos, socios, hitos, tipos de atención); actividades, gestiones sociales, evidencias '
                    'y verificación; Tubo de seguimiento y de cartas; dashboard; auditoría; respaldo y recuperación; seguridad OWASP.'),
        ('Fuera de alcance', 'Pruebas de carga y estrés; navegadores distintos de Chromium; envío de correo real (se usa modo archivo).'),
        ('Tipos de prueba', '1) Unitarias y de integración automáticas (Django TestCase, BD en memoria). '
                            '2) Funcionales de punta a punta en navegador (Playwright + Chromium) siguiendo el protocolo manual. '
                            '3) Seguridad: inyección SQL, XSS, CSRF y acceso a datos ajenos (CP-SEG). '
                            '4) Regresión: la suite completa se ejecuta después de cada corrección. '
                            '5) Revisión estática con flake8.'),
        ('Entornos', 'Desarrollo: SQLite. Pruebas automáticas: BD temporal en memoria. Protocolo manual: servidor local con datos de demostración. '
                     'Producción de la demo: AWS EC2 (Amazon Linux 2023) con MariaDB, servicio sgr.'),
        ('Datos de prueba', 'Escenario base creado en setUp de cada prueba; datos de demostración (cargar_datos_iniciales). '
                            'RUT con dígito verificador válido; ningún dato real de vecinos.'),
        ('Criterio de entrada', 'Código en la rama de la versión, migraciones aplicadas y python manage.py check sin errores.'),
        ('Criterio de salida', '100 % de los casos de prioridad Alta aprobados; ningún defecto Alto abierto; flake8 sin avisos.'),
        ('Criterio de suspensión', 'Si un error del guion o de los datos impide probar, el caso queda Bloqueado y se reejecuta tras corregirlo.'),
        ('Gestión de defectos', 'Cada defecto se registra en INCIDENCIAS.md y en la hoja Defectos con causa, corrección y reejecución.'),
        ('Responsables', f'{SOFIA}: acceso, roles, contraseñas, seguridad, auditoría, respaldo. {ELIAS}: validadores, funcionarios, '
                         f'organización, comunidad, reglas del cliente. {IGNACIO}: delegaciones, categorías, cargos, Tubos, dashboard. '
                         f'{DIEGO}: trimestres, metas, actividades, verificación, gestión social, evidencias, cumplimiento.'),
        ('Herramientas', 'python manage.py test, plan_pruebas.py (matriz CSV), Playwright (protocolo_manual.js), flake8, pip-audit.'),
    ]
    for i, (k, v) in enumerate(filas, start=2):
        fila_datos(ws, i, [k, v])
        ws.cell(row=i, column=1).font = F_NEGRITA
    ws.freeze_panes = 'A2'


def hoja_protocolo(wb, resultados):
    ws = wb.create_sheet('Protocolo')
    titulos = ['Código', 'Nombre del caso', 'Requerimiento', 'Módulo', 'Prioridad', 'Precondiciones', 'Perfil', 'Datos de prueba',
               'Pasos', 'Resultado esperado', 'Resultado obtenido', 'Estado', 'Responsable', 'Fecha', 'Evidencia', 'Defecto',
               'Corrección', 'Reejecución', 'Prueba (código)']
    anchos = [13, 30, 26, 22, 10, 34, 18, 30, 44, 44, 30, 12, 17, 11, 30, 10, 36, 26, 48]
    cabecera(ws, 1, titulos, anchos)
    correccion = {d[0]: d[6] for d in DEFECTOS}
    for i, r in enumerate(resultados, start=2):
        g = GRUPOS[prefijo(r['id'])]
        modulo, req, prio, perfil, prec, datos, resp = g
        pasos = ('1. Crear la BD de prueba y el escenario (setUp).\n'
                 f'2. Ejecutar la acción del caso como {perfil}.\n'
                 '3. Comparar el resultado con lo esperado (assert).\n'
                 '4. Registrar el resultado en resultados_pruebas.csv.')
        estado = r['estado']
        obtenido = (f'Igual al esperado (prueba OK en {float(r["segundos"]):.2f} s).'.replace('.', ',', 1)
                    if estado == 'Aprobado' else (r['detalle'] or 'Distinto al esperado'))
        defecto = DEFECTO_DE_CASO.get(r['id'], '')
        reejec = (f'Sí · {FECHA_AUTO}: Aprobado' if defecto else f'Regresión {FECHA_AUTO}: Aprobado')
        fila_datos(ws, i, [r['id'], nombre_desde_metodo(r['prueba']), req, modulo, prio, prec, perfil, datos, pasos,
                           r['descripcion'], obtenido, estado, resp, FECHA_AUTO,
                           'resultados_pruebas.csv; ejecuciones/pruebas_automaticas_v3.log', defecto,
                           correccion.get(defecto, ''), reejec, r['prueba']],
                   centrar=(5, 12, 14, 16))
    ultima = len(resultados) + 1
    ws.freeze_panes = 'C2'
    ws.auto_filter.ref = f'A1:S{ultima}'
    colorear_estado(ws, f'L2:L{ultima}')
    lista_estados(ws, f'L2:L{ultima}', ['Aprobado', 'Fallido', 'Bloqueado'])
    return ultima


def hoja_manual(wb, finales):
    ws = wb.create_sheet('Protocolo manual')
    titulos = ['Código', 'Nombre del caso', 'Requerimiento', 'Prioridad', 'Precondiciones', 'Perfil', 'Datos de prueba', 'Pasos',
               'Resultado esperado', 'Resultado obtenido', 'Estado', 'Responsable', 'Fecha', 'Evidencia', 'Defecto', 'Corrección',
               'Reejecución']
    anchos = [12, 28, 26, 10, 26, 20, 30, 46, 34, 40, 12, 17, 11, 34, 10, 34, 30]
    cabecera(ws, 1, titulos, anchos)
    correccion = {d[0]: d[6] for d in DEFECTOS}
    for i, (cod, nombre, req, prio, perfil, prec, datos, pasos, esperado, evid, resp) in enumerate(MANUALES, start=2):
        fin = finales[cod]
        num = cod[-2:]
        intentos = [n for n in sorted(HISTORIAL_MANUAL) if estado_en_ejecucion(n, num) != 'Aprobado']
        defecto = 'INC-13' if cod in ('CP-MAN-07', 'CP-MAN-08') else ''
        reejec = ('No requerida (aprobado en todas las ejecuciones)' if not intentos else
                  f'Sí · ejecuciones {", ".join(str(n) for n in intentos)} sin aprobar; ejecución 4: {fin["estado"]}')
        texto_pasos = '\n'.join(f'{n}. {p}' for n, p in enumerate(pasos, start=1))
        fila_datos(ws, i, [cod, nombre, req, prio, prec, perfil, datos, texto_pasos, esperado, fin['obtenido'], fin['estado'],
                           resp, FECHA_AUTO, '\n'.join('evidencias/' + e for e in evid), defecto, correccion.get(defecto, ''),
                           reejec], centrar=(4, 11, 13, 15))
    ultima = len(MANUALES) + 1
    ws.freeze_panes = 'C2'
    ws.auto_filter.ref = f'A1:Q{ultima}'
    colorear_estado(ws, f'K2:K{ultima}')
    lista_estados(ws, f'K2:K{ultima}', ['Aprobado', 'Fallido', 'Bloqueado'])
    return ultima


def hoja_defectos(wb):
    ws = wb.create_sheet('Defectos')
    titulos = ['ID', 'Fecha', 'Detectado por', 'Descripción', 'Severidad', 'Causa', 'Corrección', 'Versión', 'Reejecución', 'Estado']
    cabecera(ws, 1, titulos, [9, 11, 24, 44, 10, 36, 44, 9, 28, 12])
    for i, d in enumerate(DEFECTOS, start=2):
        fila_datos(ws, i, list(d), centrar=(1, 2, 5, 8, 10))
    ultima = len(DEFECTOS) + 1
    ws.freeze_panes = 'B2'
    ws.auto_filter.ref = f'A1:J{ultima}'
    colorear_estado(ws, f'J2:J{ultima}')
    return ultima


def hoja_ejecuciones(wb):
    ws = wb.create_sheet('Ejecuciones')
    titulos = ['Ejecución', 'Tipo', 'Fecha', 'Planificadas', 'Ejecutadas', 'Aprobadas', 'Fallidas', 'Bloqueadas', 'Causa / observación',
               'Registro']
    cabecera(ws, 1, titulos, [11, 14, 11, 12, 11, 11, 10, 11, 70, 40])
    fila = 2
    for n in sorted(HISTORIAL_MANUAL):
        estados = [estado_en_ejecucion(n, f'{k:02d}') for k in range(1, 13)]
        apr, fal, blo = (estados.count(x) for x in ('Aprobado', 'Fallido', 'Bloqueado'))
        log = f'ejecuciones/protocolo_manual_ejecucion{n}{"_final" if n == 4 else ""}.log'
        fila_datos(ws, fila, [n, 'Manual (navegador)', FECHA_AUTO, 12, None, apr, fal, blo, CAUSA_EJEC[n], log], centrar=(1, 3, 4, 5, 6, 7, 8))
        ws.cell(row=fila, column=5, value=f'=F{fila}+G{fila}')
        fila += 1
    fila_datos(ws, fila, ['Final', 'Automática', FECHA_AUTO, "=COUNTA(Protocolo!A:A)-1", None,
                          '=COUNTIF(Protocolo!L:L,"Aprobado")', '=COUNTIF(Protocolo!L:L,"Fallido")',
                          '=COUNTIF(Protocolo!L:L,"Bloqueado")', 'Suite completa después de todas las correcciones (regresión).',
                          'ejecuciones/pruebas_automaticas_v3.log'], centrar=(1, 3, 4, 5, 6, 7, 8))
    ws.cell(row=fila, column=5, value=f'=F{fila}+G{fila}')
    ws.cell(row=fila + 2, column=1,
            value='Ejecutadas = aprobadas + fallidas. Un caso bloqueado no se pudo probar y no cuenta como ejecutado. '
                  'Fuente: registros en docs/pruebas/ejecuciones/.').font = F_NOTA
    ws.freeze_panes = 'A2'
    return fila


def hoja_indicadores(wb, ult_auto, ult_man, ult_def, ult_ej):
    ws = wb.create_sheet('Indicadores')
    ws.sheet_view.showGridLines = False
    cabecera(ws, 1, ['Indicador', 'Automáticas', 'Manuales', 'Total', 'Cómo se calcula'], [22, 14, 14, 12, 70])
    A, M = f'Protocolo!L2:L{ult_auto}', f"'Protocolo manual'!K2:K{ult_man}"
    filas = [
        ('Planificadas', f'=COUNTA(Protocolo!A2:A{ult_auto})', f"=COUNTA('Protocolo manual'!A2:A{ult_man})",
         'Casos definidos en el protocolo.'),
        ('Ejecutadas', '=B4+B5', '=C4+C5', 'Aprobadas + fallidas de la ejecución final.'),
        ('Aprobadas', f'=COUNTIF({A},"Aprobado")', f'=COUNTIF({M},"Aprobado")', 'Estado final "Aprobado".'),
        ('Fallidas', f'=COUNTIF({A},"Fallido")', f'=COUNTIF({M},"Fallido")', 'Estado final "Fallido" (defecto sin corregir).'),
        ('Bloqueadas', f'=COUNTIF({A},"Bloqueado")', f'=COUNTIF({M},"Bloqueado")', 'Estado final "Bloqueado".'),
        ('Bloqueadas en el ciclo', 0, f'=SUM(Ejecuciones!H2:H{ult_ej - 1})',
         'Casos bloqueados sumando todas las ejecuciones manuales (guion o datos de prueba).'),
        ('Defectos corregidos', f'=COUNTIF(Defectos!J2:J{ult_def},"Corregido")', None,
         'Defectos de la hoja Defectos con estado "Corregido" (total del proyecto).'),
        ('Defectos abiertos', f'=COUNTIF(Defectos!J2:J{ult_def},"Abierto")', None, 'Pendientes con plan de acción.'),
        ('Reejecutadas', f'=COUNTIF(Protocolo!R2:R{ult_auto},"Sí*")', f"=COUNTIF('Protocolo manual'!Q2:Q{ult_man},\"Sí*\")",
         'Casos que se volvieron a ejecutar por un defecto o un bloqueo (además de la regresión completa).'),
        ('% de aprobación', '=IF(B3=0,0,B4/B3)', '=IF(C3=0,0,C4/C3)', 'Aprobadas / ejecutadas.'),
    ]
    for i, (k, a, m, nota) in enumerate(filas, start=2):
        total = None if m is None else ('=IF(D3=0,0,D4/D3)' if k == '% de aprobación' else f'=B{i}+C{i}')
        if k in ('Defectos corregidos', 'Defectos abiertos'):
            total = f'=B{i}'
        fila_datos(ws, i, [k, a, m, total, nota], centrar=(2, 3, 4))
        ws.cell(row=i, column=1).font = F_NEGRITA
        if k == '% de aprobación':
            for col in (2, 3, 4):
                ws.cell(row=i, column=col).number_format = '0.0%'
    for i in (8, 9):  # defectos: sin columna manual
        ws.cell(row=i, column=3, value='—').alignment = CENTRO
    ws.cell(row=len(filas) + 3, column=1,
            value='Todas las cifras son fórmulas sobre las otras hojas: si cambia un estado, el indicador se actualiza.').font = F_NOTA
    ws.freeze_panes = 'A2'


def main():
    with open(os.path.join(RAIZ, 'resultados_pruebas.csv'), encoding='utf-8') as f:
        resultados = sorted(csv.DictReader(f), key=lambda r: (prefijo(r['id']), r['id']))
    faltan = sorted({prefijo(r['id']) for r in resultados} - set(GRUPOS))
    if faltan:
        raise SystemExit(f'Prefijos sin datos en GRUPOS: {faltan}')
    with open(os.path.join(RAIZ, 'docs', 'pruebas', 'resultados_manuales.json'), encoding='utf-8') as f:
        finales = {r['id']: r for r in json.load(f)}
    wb = Workbook()
    hoja_resumen(wb, len(resultados), len(MANUALES))
    hoja_plan(wb)
    ult_auto = hoja_protocolo(wb, resultados)
    ult_man = hoja_manual(wb, finales)
    ult_def = hoja_defectos(wb)
    ult_ej = hoja_ejecuciones(wb)
    hoja_indicadores(wb, ult_auto, ult_man, ult_def, ult_ej)
    wb.move_sheet('Indicadores', offset=-4)
    for ws in wb.worksheets:
        ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
        ws.page_setup.fitToHeight = 0
        ws.page_setup.orientation = 'landscape'
        ws.page_setup.fitToWidth = 1
    wb.save(SALIDA)
    print(f'Planilla guardada en {os.path.relpath(SALIDA, RAIZ)}: {len(resultados)} automáticas, {len(MANUALES)} manuales, '
          f'{len(DEFECTOS)} defectos.')


if __name__ == '__main__':
    main()
