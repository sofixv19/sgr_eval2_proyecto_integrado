"""Inicio y cierre de sesión del sitio SGR."""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .forms import LoginForm


def _destino_seguro(request):
    """Devuelve ?next= solo si apunta a este mismo sitio (evita redirecciones
    abiertas hacia sitios externos)."""
    destino = request.POST.get('next') or request.GET.get('next') or ''
    seguro = url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    )
    if destino and seguro:
        return destino
    return '/'


@never_cache
@csrf_protect
def iniciar_sesion(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)  # login() también renueva la clave de sesión
            messages.success(request, f'Bienvenido/a, {usuario.get_full_name() or usuario.username}.')
            return redirect(_destino_seguro(request))
    else:
        form = LoginForm(request=request)

    return render(request, 'cuentas/login.html', {
        'titulo_pagina': 'Iniciar sesión',
        'form': form,
        'next': request.GET.get('next', ''),
    })


@require_POST
def cerrar_sesion(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('cuentas:login')
