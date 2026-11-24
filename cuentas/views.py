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


# ------------------------------------------------------------------ v3.0
# Cambio obligatorio de la contraseña temporal y recuperación por correo.
from django.contrib.auth import update_session_auth_hash  # noqa: E402
from django.contrib.auth import views as auth_views  # noqa: E402
from django.contrib.auth.decorators import login_required  # noqa: E402
from django.urls import reverse_lazy  # noqa: E402

from .forms import CambiarClaveForm, RecuperarClaveForm, RestablecerClaveForm  # noqa: E402
from .models import debe_cambiar_clave, registrar_cambio_clave  # noqa: E402


@login_required
@never_cache
@csrf_protect
def cambiar_clave(request):
    obligatorio = debe_cambiar_clave(request.user)
    if request.method == 'POST':
        form = CambiarClaveForm(request.user, request.POST)
        if form.is_valid():
            usuario = form.save()
            update_session_auth_hash(request, usuario)   # no cierra la sesión actual
            registrar_cambio_clave(usuario)
            messages.success(request, 'Contraseña cambiada correctamente.')
            return redirect('/')
    else:
        form = CambiarClaveForm(request.user)
    return render(request, 'cuentas/cambiar_clave.html', {
        'titulo_pagina': 'Cambiar contraseña', 'form': form, 'obligatorio': obligatorio,
    })


class RecuperarClave(auth_views.PasswordResetView):
    """Envía un enlace de un solo uso que vence (PASSWORD_RESET_TIMEOUT).
    Siempre muestra el mismo mensaje, exista o no el correo, para no revelar
    qué correos están registrados."""
    form_class = RecuperarClaveForm
    template_name = 'cuentas/recuperar.html'
    email_template_name = 'cuentas/correo_recuperar.txt'
    subject_template_name = 'cuentas/correo_recuperar_asunto.txt'
    success_url = reverse_lazy('cuentas:recuperar_enviado')
    extra_context = {'titulo_pagina': 'Recuperar contraseña'}


class RecuperarEnviado(auth_views.PasswordResetDoneView):
    template_name = 'cuentas/recuperar_enviado.html'
    extra_context = {'titulo_pagina': 'Revise su correo'}


class RestablecerClave(auth_views.PasswordResetConfirmView):
    form_class = RestablecerClaveForm
    template_name = 'cuentas/restablecer.html'
    success_url = reverse_lazy('cuentas:restablecer_listo')
    extra_context = {'titulo_pagina': 'Nueva contraseña'}

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        registrar_cambio_clave(form.user, 'Contraseña restablecida con enlace de recuperación')
        return respuesta


class RestablecerListo(auth_views.PasswordResetCompleteView):
    template_name = 'cuentas/restablecer_listo.html'
    extra_context = {'titulo_pagina': 'Contraseña restablecida'}
