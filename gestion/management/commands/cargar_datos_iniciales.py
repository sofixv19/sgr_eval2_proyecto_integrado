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
from django.core.management.base import BaseCommand

from delegaciones.models import Delegacion, OrganizacionComunitaria
from gestion.models import Actividad, Categoria
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

# Funcionarios: se usan los mismos nombres de ejemplo que ya existían en
# data/actividades.json (Evaluación 1 de Sofía), ahora convertidos en
# entidades reales (Funcionario) con cargo y delegación, en vez de texto
# libre. Tres de ellos coinciden con el/la encargado/a real de su
# delegación (ver data/delegaciones.json), por lo que se les asigna el
# cargo "Encargado de Delegación".
FUNCIONARIOS_SEED = [
    {'nombre': 'F. Contreras (ejemplo)', 'delegacion': 'Rural',
     'cargo': 'Encargado de Infraestructura', 'rut': '11.111.111-1',
     'email': 'f.contreras.ejemplo@laserena.cl'},
    {'nombre': 'P. Rojas (ejemplo)', 'delegacion': 'La Pampa',
     'cargo': 'Gestor Social', 'rut': '12.222.222-5',
     'email': 'p.rojas.ejemplo@laserena.cl'},
    {'nombre': 'J. Herrera (ejemplo)', 'delegacion': 'Centro',
     'cargo': 'Inspector Territorial', 'rut': '13.333.333-9',
     'email': 'j.herrera.ejemplo@laserena.cl'},
    {'nombre': 'M. Soto (ejemplo)', 'delegacion': 'Las Compañías',
     'cargo': 'Encargado Comunitario', 'rut': '14.444.444-2',
     'email': 'm.soto.ejemplo@laserena.cl'},
    {'nombre': 'R. Fuenzalida (ejemplo)', 'delegacion': 'Avenida del Mar',
     'cargo': 'Encargado de Delegación', 'rut': '15.555.555-6',
     'email': 'r.fuenzalida.ejemplo@laserena.cl', 'rol': 'Coordinador'},
    {'nombre': 'E. Villanueva (ejemplo)', 'delegacion': 'La Antena - La Florida',
     'cargo': 'Encargado de Delegación', 'rut': '16.666.666-K',
     'email': 'e.villanueva.ejemplo@laserena.cl', 'rol': 'Coordinador'},
    {'nombre': 'M. Barraza (ejemplo)', 'delegacion': 'Rural',
     'cargo': 'Encargado de Delegación', 'rut': '17.777.777-3',
     'email': 'm.barraza.ejemplo@laserena.cl', 'rol': 'Coordinador'},

    # --- Delegados: rol agregado tras la retroalimentación del profesor
    # Ciceo (Evaluación 1). El Delegado es quien valida las actividades
    # registradas por el Funcionario; no puede ser la misma persona. Se
    # siembra un Delegado por cada delegación que ya tiene actividades de
    # ejemplo, para poder demostrar la validación en los datos de prueba.
    {'nombre': 'C. Araya (Delegado, ejemplo)', 'delegacion': 'Rural',
     'cargo': 'Encargado de Delegación', 'rut': '18.888.888-7',
     'email': 'c.araya.delegado@laserena.cl', 'rol': 'Delegado'},
    {'nombre': 'N. Ortiz (Delegado, ejemplo)', 'delegacion': 'La Pampa',
     'cargo': 'Encargado de Delegación', 'rut': '19.999.999-0',
     'email': 'n.ortiz.delegado@laserena.cl', 'rol': 'Delegado'},
    {'nombre': 'S. Pizarro (Delegado, ejemplo)', 'delegacion': 'Centro',
     'cargo': 'Encargado de Delegación', 'rut': '20.000.000-5',
     'email': 's.pizarro.delegado@laserena.cl', 'rol': 'Delegado'},
]


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

        self.stdout.write('Asignando metas de ejemplo a cada funcionario (las asigna su Delegado)...')
        self._metas_demo()

        self.stdout.write('Cargando organizaciones comunitarias de ejemplo (versión 2.0)...')
        organizaciones = self._organizaciones_demo()
        self.stdout.write(f'  {organizaciones} organizaciones nuevas.')

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
        """Una Junta de Vecinos y dos organizaciones funcionales por delegación
        (RF-039, versión 2.0). Son datos de ejemplo, no el registro oficial."""
        tipos = OrganizacionComunitaria.Tipo
        ejemplos = [
            ('Junta de Vecinos {n} (ejemplo)', tipos.JUNTA_VECINOS, 85),
            ('Club de Adulto Mayor {n} (ejemplo)', tipos.ADULTO_MAYOR, 30),
            ('Club Deportivo {n} (ejemplo)', tipos.DEPORTIVA, 40),
        ]
        creadas = 0
        for delegacion in Delegacion.objects.all():
            for plantilla, tipo, socios in ejemplos:
                _, creada = OrganizacionComunitaria.objects.get_or_create(
                    delegacion=delegacion, nombre=plantilla.format(n=delegacion.nombre),
                    defaults={'tipo': tipo, 'socios_activos': socios, 'domicilio': f'Sede comunitaria, {delegacion.nombre}'},
                )
                creadas += int(creada)
        return creadas

    def _validar_actividades_demo(self):
        """Marca como validada una actividad de ejemplo por cada delegación
        que ya cuenta con un Funcionario con rol 'Delegado' sembrado más
        arriba, usando el mismo método marcar_validado() que se usaría desde
        la interfaz real (así se demuestra la regla de negocio pedida por el
        profesor Ciceo también en los datos de prueba, no solo en el código).
        """
        validadas = 0
        delegados = Funcionario.objects.filter(rol='Delegado').select_related('delegacion')
        for delegado in delegados:
            actividad = (
                Actividad.objects.filter(delegacion=delegado.delegacion, validado=False)
                .exclude(funcionario=delegado)
                .order_by('codigo')
                .first()
            )
            if actividad is None:
                continue
            try:
                actividad.marcar_validado(delegado)
                validadas += 1
            except ValueError as error:
                self.stdout.write(self.style.WARNING(f'  No se pudo validar {actividad.codigo}: {error}'))
        return validadas
