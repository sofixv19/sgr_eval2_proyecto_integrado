"""
Crea el período de medición vigente y se lo asigna a las metas que ya
existían (antes de esta etapa las metas no tenían período).
"""
import datetime

from django.db import migrations


def crear_periodo(apps, schema_editor):
    Periodo = apps.get_model('organizacion', 'Periodo')
    MetaProyecto = apps.get_model('organizacion', 'MetaProyecto')
    periodo, _ = Periodo.objects.get_or_create(
        nombre='Segundo semestre 2026',
        defaults={'fecha_inicio': datetime.date(2026, 7, 1), 'fecha_fin': datetime.date(2026, 12, 31), 'estado': 'Abierto'},
    )
    MetaProyecto.objects.filter(periodo__isnull=True).update(periodo=periodo)


def revertir(apps, schema_editor):
    MetaProyecto = apps.get_model('organizacion', 'MetaProyecto')
    MetaProyecto.objects.update(periodo=None)


class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0004_periodo'),
    ]

    operations = [
        migrations.RunPython(crear_periodo, revertir),
    ]
