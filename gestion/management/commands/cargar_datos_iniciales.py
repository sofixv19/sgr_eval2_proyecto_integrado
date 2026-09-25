"""
Comando de gestión: migra los datos de la Evaluación Sumativa 1 (archivos
JSON en data/) hacia la base de datos relacional de la Evaluación 2.

Uso:
    python manage.py cargar_datos_iniciales

Es idempotente: se puede ejecutar varias veces sin duplicar registros,
usando update_or_create() según la clave natural de cada modelo
(nombre de la delegación, nombre de la categoría, código de la actividad).
"""
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from delegaciones.models import Delegacion
from gestion.models import Actividad, Categoria


class Command(BaseCommand):
    help = 'Carga delegaciones.json y actividades.json (Evaluación 1) en la base de datos.'

    def handle(self, *args, **options):
        data_dir = Path(settings.BASE_DIR) / 'data'

        self.stdout.write('Cargando delegaciones...')
        delegaciones_creadas = self._cargar_delegaciones(data_dir / 'delegaciones.json')

        self.stdout.write('Cargando categorías y actividades...')
        actividades_creadas = self._cargar_actividades(data_dir / 'actividades.json')

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {delegaciones_creadas} delegaciones y '
            f'{actividades_creadas} actividades disponibles en la base de datos.'
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

            Actividad.objects.update_or_create(
                codigo=item['codigo'],
                defaults={
                    'fecha': item['fecha'],
                    'delegacion': delegacion,
                    'categoria': categoria,
                    'descripcion': item['descripcion'],
                    'funcionario': item['funcionario'],
                    'estado': item['estado'],
                },
            )
        return Actividad.objects.count()
