"""
v3.0 (Guía PI Ev. 3, Actividad 3): respaldo de la base de datos y de las
evidencias, independiente del motor (SQLite o MariaDB).

Uso:
    python manage.py respaldar                 # crea respaldos/sgr_AAAAMMDD_HHMM.zip
    python manage.py respaldar --destino /ruta

El .zip contiene datos.json (todos los datos con dumpdata) y la carpeta
media/ (evidencias). Para recuperar, ver GUIA_DESPLIEGUE.md, sección
"Respaldo y recuperación".
"""
import io
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

EXCLUIR = ['contenttypes', 'auth.permission', 'sessions', 'admin.logentry']


class Command(BaseCommand):
    help = 'Respalda la base de datos (JSON) y las evidencias en un archivo .zip.'

    def add_arguments(self, parser):
        parser.add_argument('--destino', default=str(Path(settings.BASE_DIR) / 'respaldos'),
                            help='Carpeta donde se guarda el respaldo.')

    def handle(self, *args, **opciones):
        destino = Path(opciones['destino'])
        destino.mkdir(parents=True, exist_ok=True)
        nombre = destino / f'sgr_{timezone.localtime():%Y%m%d_%H%M%S}.zip'
        datos = io.StringIO()
        call_command('dumpdata', '--natural-foreign', '--indent', '1', exclude=EXCLUIR, stdout=datos)
        media = Path(settings.MEDIA_ROOT)
        archivos = 0
        with zipfile.ZipFile(nombre, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr('datos.json', datos.getvalue())
            if media.exists():
                for archivo in media.rglob('*'):
                    if archivo.is_file():
                        zipf.write(archivo, Path('media') / archivo.relative_to(media))
                        archivos += 1
        self.stdout.write(self.style.SUCCESS(f'Respaldo creado: {nombre} ({archivos} archivos de evidencia).'))
        return None
