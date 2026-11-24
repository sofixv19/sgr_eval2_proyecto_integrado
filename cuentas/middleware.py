"""
Exige sesión iniciada en todo el sitio, salvo en las rutas públicas
(inicio de sesión, panel de administración —que tiene su propio login— y
archivos estáticos). Así ninguna pantalla nueva queda abierta por olvido.
"""
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode


class LoginObligatorioMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and not self._es_publica(request.path):
            return redirect(f"{reverse('cuentas:login')}?{urlencode({'next': request.get_full_path()})}")
        return self.get_response(request)

    @staticmethod
    def _es_publica(ruta):
        estaticos = settings.STATIC_URL if settings.STATIC_URL.startswith('/') else '/' + settings.STATIC_URL
        publicas = [reverse('cuentas:login'), '/cuentas/recuperar/', '/cuentas/restablecer/', '/admin/', estaticos]
        return any(ruta.startswith(p) for p in publicas)


class CambioClaveObligatorioMiddleware:
    """v3.0: quien entró con una contraseña temporal solo puede ir a la
    pantalla de cambio de contraseña (o cerrar sesión) hasta cambiarla."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .models import debe_cambiar_clave
        permitidas = (reverse('cuentas:cambiar_clave'), reverse('cuentas:logout'))
        estaticos = settings.STATIC_URL if settings.STATIC_URL.startswith('/') else '/' + settings.STATIC_URL
        if (request.path not in permitidas and not request.path.startswith(estaticos)
                and debe_cambiar_clave(request.user)):
            return redirect('cuentas:cambiar_clave')
        return self.get_response(request)
