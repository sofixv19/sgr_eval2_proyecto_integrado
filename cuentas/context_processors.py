"""Deja disponible en todos los templates el rol y el perfil del usuario,
para mostrar un menú y una pantalla distinta según quién inicia sesión."""
from django.conf import settings

from .perfiles import perfil_de, rol_de


def rol_usuario(request):
    usuario = getattr(request, 'user', None)
    return {
        'rol_usuario': rol_de(usuario) if usuario else None,
        'perfil_usuario': perfil_de(usuario) if usuario else None,
        'sgr_version': getattr(settings, 'SGR_VERSION', ''),
    }
