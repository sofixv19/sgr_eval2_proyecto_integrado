"""Estado de la cuenta de acceso (versión 3.0, Guía PI Evaluación 3).

Una cuenta creada con contraseña temporal debe cambiarla en su primer
ingreso. El estado se guarda aparte del usuario de Django para no modificar
la tabla auth_user.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class EstadoCuenta(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='estado_cuenta', verbose_name='Usuario',
    )
    debe_cambiar_clave = models.BooleanField(
        'Debe cambiar la contraseña', default=False,
        help_text='Se activa cuando se entrega una contraseña temporal.',
    )
    clave_cambiada_en = models.DateTimeField('Último cambio de contraseña', null=True, blank=True)

    class Meta:
        verbose_name = 'Estado de cuenta'
        verbose_name_plural = 'Estados de cuenta'

    def __str__(self):
        return f'{self.usuario} ({"debe cambiar clave" if self.debe_cambiar_clave else "al día"})'


def marcar_clave_temporal(usuario):
    """La próxima vez que entre, el usuario tendrá que cambiar su contraseña."""
    EstadoCuenta.objects.update_or_create(usuario=usuario, defaults={'debe_cambiar_clave': True})


def registrar_cambio_clave(usuario, detalle='Cambio de contraseña'):
    EstadoCuenta.objects.update_or_create(
        usuario=usuario, defaults={'debe_cambiar_clave': False, 'clave_cambiada_en': timezone.now()},
    )
    from comun.auditoria import registrar
    registrar('Cambio de clave', detalle=detalle, usuario=usuario)


def debe_cambiar_clave(usuario):
    if not getattr(usuario, 'is_authenticated', False):
        return False
    return EstadoCuenta.objects.filter(usuario=usuario, debe_cambiar_clave=True).exists()
