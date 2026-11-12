"""
Comando de gestión: migra los datos de la Evaluación Sumativa 1 (archivos
JSON en data/) hacia la base de datos relacional de la Evaluación 2, y
siembra además el catálogo de cargos/funcionarios/metas incorporado al
fusionar el proyecto con el del compañero de equipo (ramo de Alex).

Uso:
    python manage.py cargar_datos_iniciales

Es idempotente: se puede ejecutar varias veces sin duplicar registros,
usando update_or_create() / get_or_create() según la clave natural de
cada modelo.
"""
import datetime
import json
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from delegaciones.models import Delegacion, OrganizacionComunitaria
from gestion.models import Actividad, Categoria, Compromiso, Evidencia
from organizacion.models import CargoFuncion, Funcionario, MetaProyecto, Periodo

# ---------------------------------------------------------------------------
# Catálogo de cargos (diseño original: compañero, app 'gestionCargosApp').
# ---------------------------------------------------------------------------
CARGOS_SEED = [
    'Encargado de Delegación',
    'Encargado de Infraestructura',
    'Gestor Social',
    'Inspector Territorial',
    'Encargado Comunitario',
]

# Metas de ejemplo por cargo (diseño original: compañero).
METAS_SEED = [
    {'cargo': 'Encargado de Delegación', 'item_medible': 'Actividades registradas por mes',
     'valor_objetivo': '20', 'unidad': 'Cantidad', 'ponderador': 40},
    {'cargo': 'Gestor Social', 'item_medible': 'Solicitudes sociales resueltas',
     'valor_objetivo': '90', 'unidad': 'Porcentaje', 'ponderador': 30},
    {'cargo': 'Inspector Territorial', 'item_medible': 'Visitas de terreno realizadas',
     'valor_objetivo': '15', 'unidad': 'Cantidad', 'ponderador': 25},
]

# Equipo de demostración (versión 2.1.2). Es pequeño a propósito: dos
# delegaciones con su equipo completo bastan para mostrar cada rol.
# - Rural: un Delegado y dos funcionarios (validación, reasignación en la
#   agenda y resumen por responsable).
# - Centro: un Delegado y un funcionario (muestra que una delegación no ve
#   lo de la otra).
# Las otras cuatro delegaciones quedan sin equipo, listas para usarse.
# Todos los datos son ficticios, marcados "(ejemplo)".
FUNCIONARIOS_SEED = [
    {'nombre': 'C. Araya (Delegado, ejemplo)', 'delegacion': 'Rural',
     'cargo': 'Encargado de Delegación', 'rut': '18.888.888-7',
     'email': 'c.araya.delegado@laserena.cl', 'rol': 'Delegado'},
    {'nombre': 'F. Contreras (ejemplo)', 'delegacion': 'Rural',
     'cargo': 'Encargado de Infraestructura', 'rut': '11.111.111-1',
     'email': 'f.contreras.ejemplo@laserena.cl'},
    {'nombre': 'L. Tapia (ejemplo)', 'delegacion': 'Rural',
     'cargo': 'Gestor Social', 'rut': '21.111.111-9',
     'email': 'l.tapia.ejemplo@laserena.cl'},
    {'nombre': 'S. Pizarro (Delegado, ejemplo)', 'delegacion': 'Centro',
     'cargo': 'Encargado de Delegación', 'rut': '20.000.000-5',
     'email': 's.pizarro.delegado@laserena.cl', 'rol': 'Delegado'},
    {'nombre': 'J. Herrera (ejemplo)', 'delegacion': 'Centro',
     'cargo': 'Inspector Territorial', 'rut': '13.333.333-9',
     'email': 'j.herrera.ejemplo@laserena.cl'},
]


def _pdf_ejemplo(texto):
    """PDF mínimo de una página con un texto, sin librerías externas."""
    texto = texto.encode('latin-1', 'replace').decode('latin-1')
    texto = texto.replace('\\', ' ').replace('(', '[').replace(')', ']')[:90]
    contenido = (f'BT /F1 18 Tf 50 760 Td (Evidencia de ejemplo - SGR La Serena) Tj ET\n'
                 f'BT /F1 11 Tf 50 730 Td ({texto}) Tj ET\n'
                 f'BT /F1 11 Tf 50 710 Td (Documento ficticio para la demostracion.) Tj ET').encode('latin-1')
    objetos = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R '
        b'/Resources << /Font << /F1 5 0 R >> >> >>',
        b'<< /Length ' + str(len(contenido)).encode() + b' >>\nstream\n' + contenido + b'\nendstream',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    ]
    salida = bytearray(b'%PDF-1.4\n')
    posiciones = []
    for numero, cuerpo in enumerate(objetos, start=1):
        posiciones.append(len(salida))
        salida += f'{numero} 0 obj\n'.encode() + cuerpo + b'\nendobj\n'
    inicio_xref = len(salida)
    salida += f'xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n'.encode()
    for posicion in posiciones:
        salida += f'{posicion:010d} 00000 n \n'.encode()
    salida += f'trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF\n'.encode()
    return bytes(salida)


class Command(BaseCommand):
    help = (
        'Carga delegaciones.json y actividades.json (Evaluación 1) y el '
        'catálogo de cargos/funcionarios/metas en la base de datos.'
    )

    def handle(self, *args, **options):
        data_dir = Path(settings.BASE_DIR) / 'data'

        self.stdout.write('Cargando delegaciones...')
        delegaciones_creadas = self._cargar_delegaciones(data_dir / 'delegaciones.json')

        self.stdout.write('Cargando cargos, funcionarios y metas...')
        funcionarios_creados = self._cargar_organizacion()

        self.stdout.write('Cargando categorías y actividades...')
        actividades_creadas = self._cargar_actividades(data_dir / 'actividades.json')

        self.stdout.write('Validando actividades de ejemplo (rol Delegado)...')
        validadas = self._validar_actividades_demo()

        self.stdout.write('Adjuntando evidencias de ejemplo a las actividades pendientes...')
        self.stdout.write(f'  {self._evidencias_demo()} evidencias nuevas.')

        self.stdout.write('Asignando metas de ejemplo a cada funcionario (las asigna su Delegado)...')
        self._metas_demo()

        self.stdout.write('Cargando organizaciones comunitarias de ejemplo (versión 2.0)...')
        organizaciones = self._organizaciones_demo()
        self.stdout.write(f'  {organizaciones} organizaciones nuevas.')

        self.stdout.write('Cargando compromisos de ejemplo en la agenda colectiva (versión 2.1)...')
        self.stdout.write(f'  {self._compromisos_demo()} compromisos nuevos.')

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {delegaciones_creadas} delegaciones, '
            f'{funcionarios_creados} funcionarios, '
            f'{actividades_creadas} actividades y '
            f'{validadas} actividades ya validadas por su Delegado disponibles en la base de datos.'
        ))

    def _cargar_delegaciones(self, ruta):
        with open(ruta, encoding='utf-8') as archivo:
            delegaciones = json.load(archivo)

        for item in delegaciones:
            Delegacion.objects.update_or_create(
                nombre=item['nombre'],
                defaults={
                    'encargado': item['encargado'],
                    'direccion': item['direccion'],
                    'telefono': item['telefono'],
                    'email': item['email'],
                    'territorio': item['territorio'],
                    'enfoque': item['enfoque'],
                },
            )
        return Delegacion.objects.count()

    def _cargar_organizacion(self):
        for nombre_cargo in CARGOS_SEED:
            CargoFuncion.objects.get_or_create(nombre_cargo=nombre_cargo)

        # Período de medición vigente (tabla 'periodo' del MER de la Evaluación 1).
        periodo, _ = Periodo.objects.get_or_create(
            nombre='Segundo semestre 2026',
            defaults={'fecha_inicio': datetime.date(2026, 7, 1), 'fecha_fin': datetime.date(2026, 12, 31),
                      'estado': Periodo.Estado.ABIERTO},
        )
        for meta in METAS_SEED:
            cargo = CargoFuncion.objects.get(nombre_cargo=meta['cargo'])
            MetaProyecto.objects.update_or_create(
                cargo=cargo, item_medible=meta['item_medible'],
                defaults={
                    'periodo': periodo,
                    'valor_objetivo': meta['valor_objetivo'],
                    'unidad': meta['unidad'],
                    'ponderador': meta['ponderador'],
                },
            )

        for item in FUNCIONARIOS_SEED:
            try:
                delegacion = Delegacion.objects.get(nombre=item['delegacion'])
            except Delegacion.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"  Delegación '{item['delegacion']}' no encontrada; "
                    f"se omite el funcionario {item['nombre']}."
                ))
                continue

            cargo = CargoFuncion.objects.get(nombre_cargo=item['cargo'])
            Funcionario.objects.update_or_create(
                email=item['email'],
                defaults={
                    'rut': item['rut'],
                    'nombre': item['nombre'],
                    'delegacion': delegacion,
                    'cargo': cargo,
                    'rol': item.get('rol', 'Funcionario'),
                    'activo': True,
                },
            )
        return Funcionario.objects.count()

    def _cargar_actividades(self, ruta):
        with open(ruta, encoding='utf-8') as archivo:
            actividades = json.load(archivo)

        for item in actividades:
            categoria, _ = Categoria.objects.get_or_create(nombre=item['categoria'])

            try:
                delegacion = Delegacion.objects.get(nombre=item['delegacion'])
            except Delegacion.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"  Delegación '{item['delegacion']}' no encontrada; "
                    f"se omite la actividad {item['codigo']}."
                ))
                continue

            try:
                funcionario = Funcionario.objects.get(nombre=item['funcionario'])
            except Funcionario.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"  Funcionario '{item['funcionario']}' no encontrado; "
                    f"se omite la actividad {item['codigo']}."
                ))
                continue

            actividad, creada = Actividad.objects.update_or_create(
                codigo=item['codigo'],
                defaults={
                    'fecha': item['fecha'],
                    'delegacion': delegacion,
                    'categoria': categoria,
                    'descripcion': item['descripcion'],
                    'funcionario': funcionario,
                    'estado': item['estado'],
                },
            )
            if creada:
                # Datos históricos de la versión 1.x: las reglas de puntaje
                # de la 2.0 no se les aplican hacia atrás.
                actividad.version_reglas = '1.0'
                actividad.save(update_fields=['version_reglas'])
        return Actividad.objects.count()

    def _evidencias_demo(self):
        """Un PDF de ejemplo en cada actividad pendiente que aún no tiene
        evidencia, para que el Delegado tenga algo que revisar y validar."""
        creadas = 0
        pendientes = Actividad.objects.filter(validado=False, evidencias__isnull=True, version_reglas='1.0')
        for actividad in pendientes.select_related('funcionario__usuario'):
            Evidencia.objects.create(
                actividad=actividad, descripcion='Evidencia de ejemplo (PDF ficticio)',
                subida_por=actividad.funcionario.usuario,
                archivo=ContentFile(_pdf_ejemplo(f'{actividad.codigo}: {actividad.descripcion}'), name='ejemplo.pdf'))
            creadas += 1
        return creadas

    def _metas_demo(self):
        """Dos metas por funcionario en el período abierto (60 % y 40 %), si
        todavía no tiene: una de la categoría de sus actividades y otra de
        Organizaciones Comunitarias. Así los paneles muestran cumplimiento."""
        periodo = Periodo.objects.filter(estado=Periodo.Estado.ABIERTO).first()
        if periodo is None:
            return
        comunitarias, _ = Categoria.objects.get_or_create(nombre='Organizaciones Comunitarias')
        for funcionario in Funcionario.objects.filter(rol='Funcionario', activo=True):
            if MetaProyecto.objects.filter(funcionario=funcionario, periodo=periodo).exists():
                continue
            primera = Actividad.objects.filter(funcionario=funcionario).select_related('categoria').first()
            principal = primera.categoria if primera else comunitarias
            metas = [(principal, '4', 60)]
            if principal != comunitarias:
                metas.append((comunitarias, '3', 40))
            for categoria, objetivo, ponderador in metas:
                MetaProyecto.objects.create(
                    cargo=funcionario.cargo, funcionario=funcionario, periodo=periodo, categoria=categoria,
                    item_medible=categoria.nombre, valor_objetivo=objetivo, unidad='Cantidad', ponderador=ponderador,
                )

    def _organizaciones_demo(self):
        """Una Junta de Vecinos y dos organizaciones funcionales por cada
        delegación con equipo (RF-039, versión 2.0). Son datos de ejemplo, no el registro oficial."""
        tipos = OrganizacionComunitaria.Tipo
        ejemplos = [
            ('Junta de Vecinos {n} (ejemplo)', tipos.JUNTA_VECINOS, 85),
            ('Club de Adulto Mayor {n} (ejemplo)', tipos.ADULTO_MAYOR, 30),
            ('Club Deportivo {n} (ejemplo)', tipos.DEPORTIVA, 40),
        ]
        creadas = 0
        for delegacion in Delegacion.objects.filter(funcionarios__isnull=False).distinct():
            for plantilla, tipo, socios in ejemplos:
                _, creada = OrganizacionComunitaria.objects.get_or_create(
                    delegacion=delegacion, nombre=plantilla.format(n=delegacion.nombre),
                    defaults={'tipo': tipo, 'socios_activos': socios, 'domicilio': f'Sede comunitaria, {delegacion.nombre}'},
                )
                creadas += int(creada)
        return creadas

    def _compromisos_demo(self):
        """Tres compromisos por delegación para mostrar la agenda: uno vencido,
        uno próximo a vencer y uno realizado (RF-016 a RF-019)."""
        hoy = datetime.date.today()
        ejemplos = [
            ('Junta de Vecinos {n} (ejemplo)', 'Poda de árboles en la plaza principal', -3, 'Pendiente'),
            ('Club de Adulto Mayor {n} (ejemplo)', 'Taller de alfabetización digital', 2, 'En proceso'),
            ('Vecina del sector (ejemplo)', 'Retiro de microbasural en el pasaje', 10, 'Realizado'),
        ]
        creados = 0
        for delegacion in Delegacion.objects.all():
            equipo = list(delegacion.funcionarios.filter(rol='Funcionario', activo=True).order_by('pk'))
            if not equipo or delegacion.compromisos.exists():
                continue
            for numero, (solicitante, descripcion, dias, estado) in enumerate(ejemplos):
                responsable = equipo[numero % len(equipo)]
                Compromiso.objects.create(
                    delegacion=delegacion, solicitante=solicitante.format(n=delegacion.nombre),
                    organizacion=delegacion.organizaciones.filter(nombre=solicitante.format(n=delegacion.nombre)).first(),
                    territorio=f'Sector {delegacion.nombre}', descripcion=descripcion, responsable=responsable,
                    area_apoyo='Diserco', fecha_solicitud=hoy - datetime.timedelta(days=7),
                    fecha_compromiso=hoy + datetime.timedelta(days=dias), estado=estado,
                    fecha_cierre=hoy if estado == 'Realizado' else None,
                    observacion='Dato de ejemplo para la demostración.')
                creados += 1
        return creados

    def _validar_actividades_demo(self):
        """El Delegado de cada delegación valida las actividades de ejemplo
        ya realizadas de su equipo, usando el mismo método marcar_validado() que se usaría desde
        la interfaz real (así se demuestra la regla de negocio pedida por el
        profesor Ciceo también en los datos de prueba, no solo en el código).
        """
        validadas = 0
        delegados = Funcionario.objects.filter(rol='Delegado').select_related('delegacion')
        for delegado in delegados:
            pendientes = (
                Actividad.objects.filter(delegacion=delegado.delegacion, validado=False, estado='Realizado')
                .exclude(funcionario=delegado)
                .order_by('codigo')
            )
            for actividad in pendientes:
                try:
                    actividad.marcar_validado(delegado)
                    validadas += 1
                except ValueError as error:
                    self.stdout.write(self.style.WARNING(f'  No se pudo validar {actividad.codigo}: {error}'))
        return validadas
