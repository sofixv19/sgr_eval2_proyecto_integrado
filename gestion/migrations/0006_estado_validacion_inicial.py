from django.db import migrations


def copiar_validacion(apps, schema_editor):
    """Las actividades que ya estaban validadas quedan con estado Validada."""
    Actividad = apps.get_model('gestion', 'Actividad')
    Actividad.objects.filter(validado=True).update(estado_validacion='Validada')


class Migration(migrations.Migration):
    dependencies = [('gestion', '0005_validacion_evidencias')]
    operations = [migrations.RunPython(copiar_validacion, migrations.RunPython.noop)]
