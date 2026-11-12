from django.db import migrations

AREA_POR_PALABRA = [
    ('territorial', 'TR'), ('inspector', 'TR'),
    ('social', 'SO'),
    ('comunitari', 'OC'),
    ('infraestructura', 'DI'), ('diserco', 'DI'),
    ('seguridad', 'SE'),
    ('planificaci', 'PC'), ('control', 'PC'),
]


def asignar_areas(apps, schema_editor):
    """Asigna el área a los cargos existentes según su nombre (los que no
    calzan quedan en Administrativa, AD)."""
    CargoFuncion = apps.get_model('organizacion', 'CargoFuncion')
    for cargo in CargoFuncion.objects.all():
        nombre = cargo.nombre_cargo.lower()
        cargo.area = next((sigla for palabra, sigla in AREA_POR_PALABRA if palabra in nombre), 'AD')
        cargo.save(update_fields=['area'])


class Migration(migrations.Migration):
    dependencies = [('organizacion', '0006_area_usuario_metas_por_funcionario')]
    operations = [migrations.RunPython(asignar_areas, migrations.RunPython.noop)]
