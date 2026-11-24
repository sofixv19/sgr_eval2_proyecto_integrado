"""
v3.0: recupera un respaldo creado con "python manage.py respaldar".

Uso (en una base de datos nueva, con las migraciones aplicadas):
    python manage.py migrate
    python manage.py restaurar respaldos/sgr_AAAAMMDD_HHMMSS.zip --confirmar

Carga datos.json con loaddata y copia las evidencias a MEDIA_ROOT.
"""
import tempfile
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Recupera un respaldo .zip creado con el comando respaldar.'

    def add_arguments(self, parser):
        parser.add_argument('archivo')
        parser.add_argument('--confirmar', action='store_true',
                            help='Obligatorio: confirma que se cargarán los datos del respaldo.')

    def handle(self, *args, **opciones):
        if not opciones['confirmar']:
            raise CommandError('Agregue --confirmar. Use una base de datos nueva (recién migrada) para no duplicar datos.')
        ruta = Path(opciones['archivo'])
        if not ruta.exists():
            raise CommandError(f'No existe el archivo {ruta}.')
        media = Path(settings.MEDIA_ROOT)
        with zipfile.ZipFile(ruta) as zipf, tempfile.TemporaryDirectory() as carpeta:
            for miembro in zipf.namelist():
                destino = (Path(carpeta) / miembro).resolve()
                if not str(destino).startswith(str(Path(carpeta).resolve())):
                    raise CommandError('El respaldo contiene rutas no permitidas.')
            zipf.extractall(carpeta)
            call_command('loaddata', str(Path(carpeta) / 'datos.json'), verbosity=0)
            origen = Path(carpeta) / 'media'
            copiados = 0
            if origen.exists():
                for archivo in origen.rglob('*'):
                    if archivo.is_file():
                        final = media / archivo.relative_to(origen)
                        final.parent.mkdir(parents=True, exist_ok=True)
                        final.write_bytes(archivo.read_bytes())
                        copiados += 1
        self.stdout.write(self.style.SUCCESS(f'Respaldo recuperado ({copiados} archivos de evidencia).'))
