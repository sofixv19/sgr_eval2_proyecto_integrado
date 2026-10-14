"""
Modelos de la app 'gestion' (Aplicación 2).

Evaluación Sumativa 2: la información que en la Evaluación 1 vivía en
`data/actividades.json` ahora se modela con relaciones reales hacia
`delegaciones.Delegacion`, más un catálogo de categorías.

Fusión con el proyecto del compañero (ramo de Alex): 'funcionario' deja de
ser un texto libre y pasa a ser una relación real hacia
`organizacion.Funcionario`, y se incorporan los campos de 'solicitud
vecinal' que el compañero había modelado en su propia app
'registroActividadesApp', para no perder ese trabajo al unificar los dos
proyectos en uno solo.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from delegaciones.models import Delegacion
from organizacion.models import Funcionario


class Categoria(models.Model):
    """Catálogo de categorías de actividad (Diserco, Social, Seguridad, etc.).

    Se modela como tabla propia (y no como texto libre) para demostrar
    una segunda relación (ForeignKey) además de la que existe con
    Delegacion, y para que se pueda administrar desde Django Admin.
    """

    nombre = models.CharField('Nombre', max_length=80, unique=True)
    descripcion = models.CharField('Descripción', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Actividad(models.Model):
    """Una actividad / solicitud registrada por una delegación."""

    class Estado(models.TextChoices):
        PENDIENTE = 'Pendiente', 'Pendiente'
        EN_PROCESO = 'En proceso', 'En proceso'
        REALIZADO = 'Realizado', 'Realizado'

    codigo = models.CharField('Código', max_length=20, unique=True)
    fecha = models.DateField('Fecha')
    delegacion = models.ForeignKey(
        Delegacion,
        on_delete=models.CASCADE,
        related_name='actividades',
        verbose_name='Delegación',
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='actividades',
        verbose_name='Categoría',
    )
    descripcion = models.TextField('Descripción')
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,
        related_name='actividades',
        verbose_name='Funcionario a cargo',
    )
    estado = models.CharField(
        'Estado', max_length=20, choices=Estado.choices, default=Estado.PENDIENTE,
    )

    # --- Campos incorporados desde el proyecto del compañero (registro de
    # solicitudes vecinales) ---
    solicitud_problema = models.TextField(
        'Solicitud o problema vecinal', blank=True,
        help_text='Detalle de la solicitud del vecino que originó la actividad, si corresponde.',
    )
    contacto = models.CharField(
        'Vecino de contacto', max_length=100, blank=True,
    )
    telefono_contacto = models.CharField(
        'Teléfono de contacto', max_length=20, blank=True,
    )

    # --- Validación (retroalimentación del profesor Ciceo, Evaluación 1):
    # el Funcionario que registra la actividad NO puede validarla él mismo;
    # solo un Funcionario con rol 'Delegado' puede hacerlo. Por eso
    # 'validado_por' solo admite Funcionarios con ese rol (limit_choices_to)
    # y es un campo aparte del 'funcionario' que registró la actividad. ---
    validado = models.BooleanField(
        'Validado', default=False,
        help_text='Lo marca el Delegado de la delegación, no el propio Funcionario que registró la actividad.',
    )
    validado_por = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='validaciones_realizadas',
        limit_choices_to={'rol': 'Delegado'},
        verbose_name='Validado por (Delegado)',
    )
    fecha_validacion = models.DateTimeField('Fecha de validación', null=True, blank=True)

    class Meta:
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'
        ordering = ['-fecha', 'codigo']

    def __str__(self):
        return f'{self.codigo} · {self.delegacion.nombre}'

    def get_absolute_url(self):
        return reverse('gestion:detalle', args=[self.pk])

    def clean(self):
        """Regla de negocio pedida por el profesor Ciceo: un Funcionario no
        puede validar su propia actividad, y solo un Funcionario con rol
        'Delegado' puede validar (no un par del mismo nivel jerárquico)."""
        super().clean()
        if self.validado_por_id:
            if self.validado_por.rol != 'Delegado':
                raise ValidationError({
                    'validado_por': 'Solo un Funcionario con rol "Delegado" puede validar una actividad.',
                })
            if self.funcionario_id and self.validado_por_id == self.funcionario_id:
                raise ValidationError({
                    'validado_por': 'El Funcionario que registró la actividad no puede validarla él mismo.',
                })

    def marcar_validado(self, delegado):
        """Marca la actividad como validada por un Funcionario con rol
        'Delegado', aplicando la misma regla de negocio que clean()."""
        if delegado.rol != 'Delegado':
            raise ValueError('Solo un Funcionario con rol "Delegado" puede validar una actividad.')
        if delegado_id := getattr(delegado, 'id', None):
            if delegado_id == self.funcionario_id:
                raise ValueError('El Funcionario que registró la actividad no puede validarla él mismo.')
        self.validado = True
        self.validado_por = delegado
        self.fecha_validacion = timezone.now()
        self.save(update_fields=['validado', 'validado_por', 'fecha_validacion'])
