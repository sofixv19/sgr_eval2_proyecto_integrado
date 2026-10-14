"""
Corrige el dígito verificador de los RUT de los funcionarios de ejemplo
cargados por 'cargar_datos_iniciales'. Los RUT originales tenían un DV
inventado y no pasarían la nueva validación de RUT del formulario.
Solo modifica esos RUT de ejemplo; no toca ningún otro registro.
"""
from django.db import migrations

RUTS_EJEMPLO = {
    '12.222.222-2': '12.222.222-5',
    '13.333.333-3': '13.333.333-9',
    '14.444.444-4': '14.444.444-2',
    '15.555.555-5': '15.555.555-6',
    '16.666.666-6': '16.666.666-K',
    '17.777.777-7': '17.777.777-3',
    '18.888.888-8': '18.888.888-7',
    '19.999.999-9': '19.999.999-0',
    '20.000.000-0': '20.000.000-5',
}


def corregir(apps, schema_editor):
    Funcionario = apps.get_model('organizacion', 'Funcionario')
    for anterior, correcto in RUTS_EJEMPLO.items():
        if not Funcionario.objects.filter(rut=correcto).exists():
            Funcionario.objects.filter(rut=anterior).update(rut=correcto)


def revertir(apps, schema_editor):
    Funcionario = apps.get_model('organizacion', 'Funcionario')
    for anterior, correcto in RUTS_EJEMPLO.items():
        Funcionario.objects.filter(rut=correcto).update(rut=anterior)


class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0002_alter_funcionario_rol'),
    ]

    operations = [
        migrations.RunPython(corregir, revertir),
    ]
