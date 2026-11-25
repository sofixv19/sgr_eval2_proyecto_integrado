"""v3.0.1 (INC-17): desactiva las cuentas de Funcionario o Delegado que
quedaron sin ficha de funcionario (porque la ficha se eliminó antes de que
existiera la corrección). No borra nada: solo las deja inactivas y sin rol.
Administrador, Coordinador y Verificador no se tocan (no necesitan ficha)."""
from django.db import migrations


def desactivar(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Funcionario = apps.get_model('organizacion', 'Funcionario')
    con_ficha = Funcionario.objects.exclude(usuario=None).values_list('usuario_id', flat=True)
    huerfanas = (User.objects.filter(groups__name__in=['Funcionario', 'Delegado'], is_superuser=False)
                 .exclude(pk__in=list(con_ficha)).distinct())
    for usuario in huerfanas:
        usuario.is_active = False
        usuario.save(update_fields=['is_active'])
        usuario.groups.clear()


class Migration(migrations.Migration):

    dependencies = [
        ('organizacion', '0009_trimestre'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [migrations.RunPython(desactivar, migrations.RunPython.noop)]
