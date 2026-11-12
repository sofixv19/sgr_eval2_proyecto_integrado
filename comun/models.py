"""
Auditoría de operaciones críticas (RF-036, RNF-008, HU-30, CA-09).

Cada alta, modificación o eliminación de las tablas del SGR queda registrada
con usuario, fecha, acción, entidad, identificador, valor anterior y valor
nuevo. También se registran los accesos denegados y los inicios de sesión.

El historial es de solo lectura: no se puede modificar ni eliminar desde la
aplicación ni desde Django Admin (ni siquiera el Administrador).
"""
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils import timezone


class RegistroAuditoria(models.Model):
    class Accion(models.TextChoices):
        ALTA = 'Alta', 'Alta'
        MODIFICACION = 'Modificación', 'Modificación'
        ELIMINACION = 'Eliminación', 'Eliminación'
        VALIDACION = 'Validación', 'Validación'
        RECHAZO = 'Rechazo', 'Rechazo de evidencia'
        INICIO_SESION = 'Inicio de sesión', 'Inicio de sesión'
        ACCESO_FALLIDO = 'Acceso fallido', 'Inicio de sesión fallido'
        ACCESO_DENEGADO = 'Acceso denegado', 'Acceso denegado'

    fecha = models.DateTimeField('Fecha', default=timezone.now, db_index=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='auditoria', verbose_name='Usuario')
    usuario_texto = models.CharField('Usuario (texto)', max_length=150, blank=True,
                                     help_text='Se conserva aunque la cuenta se elimine después.')
    accion = models.CharField('Acción', max_length=20, choices=Accion.choices, db_index=True)
    entidad = models.CharField('Entidad', max_length=80, blank=True, db_index=True)
    objeto_id = models.CharField('Identificador', max_length=40, blank=True)
    objeto = models.CharField('Registro', max_length=200, blank=True)
    cambios = models.JSONField('Cambios (valor anterior → valor nuevo)', default=dict, blank=True)
    detalle = models.CharField('Detalle', max_length=255, blank=True)
    ip = models.GenericIPAddressField('Dirección IP', null=True, blank=True)

    class Meta:
        verbose_name = 'Registro de auditoría'
        verbose_name_plural = 'Auditoría'
        ordering = ['-fecha', '-id']

    def __str__(self):
        return f'{self.fecha:%d/%m/%Y %H:%M} · {self.usuario_texto or "sistema"} · {self.accion} · {self.entidad}'

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionDenied('El historial de auditoría no se puede modificar.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionDenied('El historial de auditoría no se puede eliminar.')
