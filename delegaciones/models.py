"""
Modelos de la app 'delegaciones' (Aplicación 1).

Evaluación Sumativa 2: la información que en la Evaluación 1 vivía en
`data/delegaciones.json` ahora se modela como una tabla relacional,
administrable desde Django Admin.
"""
from django.db import models
from django.urls import reverse
from slugify import slugify  # librería externa, ya usada en la Evaluación 1


class Delegacion(models.Model):
    """Una delegación municipal (una de las 6 oficinas territoriales)."""

    nombre = models.CharField('Nombre', max_length=120, unique=True)
    slug = models.SlugField(
        'Slug (URL)', max_length=140, unique=True, blank=True,
        help_text='Se genera automáticamente a partir del nombre si se deja en blanco.',
    )
    encargado = models.CharField('Encargado/a', max_length=150)
    direccion = models.CharField('Dirección', max_length=200)
    telefono = models.CharField('Teléfono', max_length=30)
    email = models.EmailField('Correo electrónico')
    territorio = models.CharField('Territorio', max_length=200)
    enfoque = models.TextField('Enfoque de gestión')

    class Meta:
        verbose_name = 'Delegación'
        verbose_name_plural = 'Delegaciones'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # Igual que en la Evaluación 1 (donde se usaba python-slugify sobre
        # el JSON), el slug se calcula a partir del nombre si no se definió.
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('delegaciones:detalle', args=[self.slug])

    @property
    def total_actividades(self):
        return self.actividades.count()
