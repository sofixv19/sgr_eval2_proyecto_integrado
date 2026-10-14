"""Ayudas compartidas por las pruebas automatizadas del proyecto."""
from django.contrib.auth.models import Group, User

CLAVE_PRUEBA = 'ClaveDePrueba.2026'


def crear_usuario(username='usuario.prueba', clave=CLAVE_PRUEBA, grupos=(), activo=True, superusuario=False):
    if superusuario:
        usuario = User.objects.create_superuser(username=username, password=clave, email=f'{username}@laserena.cl')
    else:
        usuario = User.objects.create_user(username=username, password=clave, is_active=activo)
    for nombre in grupos:
        usuario.groups.add(Group.objects.get_or_create(name=nombre)[0])
    return usuario


def iniciar_sesion_admin(client):
    """Inicia sesión con un superusuario (tiene todos los permisos)."""
    usuario = crear_usuario('admin.pruebas', superusuario=True)
    client.force_login(usuario)
    return usuario
