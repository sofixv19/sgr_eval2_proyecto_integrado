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
    activa = models.BooleanField(
        'Activa', default=True,
        help_text='Una delegación desactivada no aparece para asignar funcionarios ni registrar actividades.',
    )

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

    @property
    def delegado(self):
        """Funcionario con rol Delegado activo asignado a esta delegación."""
        return self.funcionarios.filter(rol='Delegado', activo=True).first()


class OrganizacionComunitaria(models.Model):
    """Organización comunitaria del territorio de una delegación.

    Versión 2.0 (Nuevos requerimientos, octubre 2026 — RF-039): además de
    las Juntas de Vecinos (organizaciones territoriales, Ley 19.418) se
    registran las organizaciones funcionales, que agrupan a personas por un
    objetivo o interés común sin importar el territorio exacto en que viven.
    Una actividad puede indicar la organización que la solicitó.
    """

    class Tipo(models.TextChoices):
        JUNTA_VECINOS = 'JJVV', 'Junta de Vecinos (territorial)'
        ADULTO_MAYOR = 'ADULTO_MAYOR', 'Club de Adulto Mayor'
        DEPORTIVA = 'DEPORTIVA', 'Organización Deportiva'
        CENTRO_MADRES = 'CENTRO_MADRES', 'Centro de Madres'
        CENTRO_CULTURAL = 'CENTRO_CULTURAL', 'Centro Cultural'
        JUVENIL = 'JUVENIL', 'Agrupación Juvenil'
        COMITE_VECINOS = 'COMITE_VECINOS', 'Comité de Vecinos'
        COMITE_ALLEGADOS = 'COMITE_ALLEGADOS', 'Comité de Allegados'
        COMITE_SEGURIDAD = 'COMITE_SEGURIDAD', 'Comité de Seguridad'
        OTRA_FUNCIONAL = 'OTRA', 'Otra organización funcional'

    nombre = models.CharField('Nombre de la organización', max_length=200)
    tipo = models.CharField('Tipo de organización', max_length=20, choices=Tipo.choices, default=Tipo.JUNTA_VECINOS)
    delegacion = models.ForeignKey(
        Delegacion, on_delete=models.PROTECT, related_name='organizaciones', verbose_name='Delegación',
    )
    domicilio = models.CharField('Domicilio legal', max_length=200, blank=True)
    socios_activos = models.PositiveIntegerField('Socios activos', null=True, blank=True)
    fecha_constitucion = models.DateField('Fecha de constitución', null=True, blank=True)
    registro_pj = models.CharField('N° registro personalidad jurídica', max_length=30, blank=True)
    activa = models.BooleanField('Vigente', default=True)

    class Meta:
        verbose_name = 'Organización comunitaria'
        verbose_name_plural = 'Organizaciones comunitarias'
        ordering = ['delegacion__nombre', 'nombre']
        constraints = [
            models.UniqueConstraint(fields=['delegacion', 'nombre'], name='organizacion_unica_por_delegacion'),
        ]

    def __str__(self):
        return self.nombre

    @property
    def es_territorial(self):
        return self.tipo == self.Tipo.JUNTA_VECINOS

    @property
    def clase(self):
        return 'Territorial' if self.es_territorial else 'Funcional'
