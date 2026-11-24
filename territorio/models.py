"""
Versión 3.0 (Guía PI Evaluación 3, alcance funcional mínimo):
territorios, vecinos, membresía y dirigencia en juntas de vecinos, hitos y
tipos/subtipos de atención social.

Todas son tablas normalizadas con claves foráneas: no hay una tabla por
funcionario ni datos repetidos (el vecino se registra una vez y se reutiliza
en actividades, gestiones sociales y organizaciones).
"""
from django.db import models

from comun.validadores import normalizar_rut, validar_rut, validar_telefono
from delegaciones.models import Delegacion, OrganizacionComunitaria
from organizacion.models import Funcionario


class Territorio(models.Model):
    """Sector o unidad vecinal dentro de una delegación."""

    nombre = models.CharField('Nombre del territorio', max_length=120)
    delegacion = models.ForeignKey(Delegacion, on_delete=models.PROTECT, related_name='territorios',
                                   verbose_name='Delegación')
    descripcion = models.CharField('Descripción / límites', max_length=250, blank=True)
    activo = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Territorio'
        verbose_name_plural = 'Territorios'
        ordering = ['delegacion__nombre', 'nombre']
        constraints = [models.UniqueConstraint(fields=['delegacion', 'nombre'], name='territorio_unico_por_delegacion')]

    def __str__(self):
        return f'{self.nombre} ({self.delegacion})'


class Vecino(models.Model):
    """Persona atendida o que solicita algo a la delegación (usuario/a)."""

    rut = models.CharField('RUT', max_length=12, unique=True, validators=[validar_rut],
                           help_text='Formato 12.345.678-5. Sirve para buscarlo y autocompletar sus datos.')
    nombre = models.CharField('Nombre completo', max_length=150, db_index=True)
    telefono = models.CharField('Teléfono', max_length=20, validators=[validar_telefono])
    email = models.EmailField('Correo', blank=True)
    direccion = models.CharField('Dirección', max_length=200, blank=True)
    delegacion = models.ForeignKey(Delegacion, on_delete=models.PROTECT, related_name='vecinos',
                                   verbose_name='Delegación')
    territorio = models.ForeignKey(Territorio, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='vecinos', verbose_name='Territorio')
    creado_en = models.DateTimeField('Registrado el', auto_now_add=True)

    class Meta:
        verbose_name = 'Vecino/a'
        verbose_name_plural = 'Vecinos'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.rut})'

    def save(self, *args, **kwargs):
        self.rut = normalizar_rut(self.rut)
        super().save(*args, **kwargs)


class MembresiaOrganizacion(models.Model):
    """Un vecino es socio o dirigente de una junta de vecinos u organización."""

    class Rol(models.TextChoices):
        SOCIO = 'Socio', 'Socio/a'
        DIRIGENTE = 'Dirigente', 'Dirigente'

    class Cargo(models.TextChoices):
        NINGUNO = '', '—'
        PRESIDENTE = 'Presidente', 'Presidente/a'
        SECRETARIO = 'Secretario', 'Secretario/a'
        TESORERO = 'Tesorero', 'Tesorero/a'
        DIRECTOR = 'Director', 'Director/a'

    vecino = models.ForeignKey(Vecino, on_delete=models.CASCADE, related_name='membresias', verbose_name='Vecino/a')
    organizacion = models.ForeignKey(OrganizacionComunitaria, on_delete=models.CASCADE, related_name='membresias',
                                     verbose_name='Organización')
    rol = models.CharField('Rol', max_length=12, choices=Rol.choices, default=Rol.SOCIO)
    cargo = models.CharField('Cargo en la directiva', max_length=12, choices=Cargo.choices, blank=True)
    desde = models.DateField('Desde', null=True, blank=True)
    vigente = models.BooleanField('Vigente', default=True)

    class Meta:
        verbose_name = 'Socio o dirigente'
        verbose_name_plural = 'Socios y dirigentes'
        ordering = ['organizacion__nombre', '-rol', 'vecino__nombre']
        constraints = [
            models.UniqueConstraint(fields=['vecino', 'organizacion'], name='membresia_unica'),
        ]

    def __str__(self):
        return f'{self.vecino.nombre} · {self.get_rol_display()} de {self.organizacion}'


class Hito(models.Model):
    """Hito o evento territorial con un funcionario responsable."""

    class Estado(models.TextChoices):
        PLANIFICADO = 'Planificado', 'Planificado'
        EN_CURSO = 'En curso', 'En curso'
        REALIZADO = 'Realizado', 'Realizado'
        CANCELADO = 'Cancelado', 'Cancelado'

    nombre = models.CharField('Nombre del hito', max_length=150)
    descripcion = models.TextField('Descripción', blank=True)
    fecha = models.DateField('Fecha', db_index=True)
    delegacion = models.ForeignKey(Delegacion, on_delete=models.PROTECT, related_name='hitos',
                                   verbose_name='Delegación')
    territorio = models.ForeignKey(Territorio, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='hitos', verbose_name='Territorio')
    responsable = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='hitos',
                                    verbose_name='Responsable')
    estado = models.CharField('Estado', max_length=12, choices=Estado.choices, default=Estado.PLANIFICADO)

    class Meta:
        verbose_name = 'Hito'
        verbose_name_plural = 'Hitos'
        ordering = ['-fecha', 'nombre']

    def __str__(self):
        return f'{self.nombre} ({self.fecha:%d/%m/%Y})'


class TipoAtencion(models.Model):
    """Tipo de atención social (catálogo LISTA/DATO MENU de la matriz)."""

    nombre = models.CharField('Tipo de atención', max_length=120, unique=True)
    activo = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Tipo de atención'
        verbose_name_plural = 'Tipos de atención'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class SubtipoAtencion(models.Model):
    tipo = models.ForeignKey(TipoAtencion, on_delete=models.PROTECT, related_name='subtipos',
                             verbose_name='Tipo de atención')
    nombre = models.CharField('Subtipo', max_length=120)
    activo = models.BooleanField('Activo', default=True)

    class Meta:
        verbose_name = 'Subtipo de atención'
        verbose_name_plural = 'Subtipos de atención'
        ordering = ['tipo__nombre', 'nombre']
        constraints = [models.UniqueConstraint(fields=['tipo', 'nombre'], name='subtipo_unico_por_tipo')]

    def __str__(self):
        return f'{self.tipo} › {self.nombre}'
