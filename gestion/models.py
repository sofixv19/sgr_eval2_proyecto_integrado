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
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
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

    class EstadoValidacion(models.TextChoices):
        PENDIENTE = 'Pendiente', 'Pendiente de validación'
        VALIDADA = 'Validada', 'Validada'
        RECHAZADA = 'Rechazada', 'Rechazada'

    # --- Versión 2.0 (Nuevos requerimientos, octubre 2026) ---
    class TipoGestion(models.TextChoices):
        REALIZACION = 'Realizacion', 'Realización de la acción (taller, visita, atención, operativo…)'
        PREVIA = 'Previa', 'Gestión previa (coordinación, correo, invitación, coordinación interna)'

    class TipoSolicitante(models.TextChoices):
        VECINO = 'Vecino', 'Vecino/a (usuario)'
        ORGANIZACION = 'Organizacion', 'Organización comunitaria'
        DELEGADO = 'Delegado', 'El propio Delegado (gestión interna)'

    codigo = models.CharField(
        'Código', max_length=20, unique=True, blank=True,
        help_text='Se genera automáticamente con la sigla del área del funcionario (por ejemplo, TR-0001).',
    )
    fecha = models.DateField('Fecha de la actividad', default=timezone.localdate)
    fecha_registro = models.DateTimeField('Fecha de registro', default=timezone.now, editable=False)
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

    # --- Versión 2.0: reglas de puntaje (RF-040, RF-041, RF-044) ---
    tipo_gestion = models.CharField(
        'Tipo de gestión', max_length=20, choices=TipoGestion.choices, default=TipoGestion.REALIZACION,
        help_text='Solo la realización de la acción da punto; las gestiones previas no.',
    )
    tipo_solicitante = models.CharField(
        'Quién solicita', max_length=20, choices=TipoSolicitante.choices, default=TipoSolicitante.VECINO,
        help_text='Si el solicitante es el propio Delegado, la actividad no se contabiliza (otra gestión).',
    )
    organizacion = models.ForeignKey(
        'delegaciones.OrganizacionComunitaria', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='actividades', verbose_name='Organización solicitante',
    )
    puntuable = models.BooleanField(
        'Suma puntaje', default=True, editable=False,
        help_text='Se calcula al guardar según las reglas de la versión 2.0.',
    )
    motivo_sin_puntaje = models.CharField('Motivo por el que no suma', max_length=200, blank=True, editable=False)
    version_reglas = models.CharField(
        'Versión de reglas', max_length=5, default='2.0', editable=False,
        help_text='Versión de los requerimientos vigente al registrar la actividad. '
                  'Las reglas de puntaje de la 2.0 no se aplican hacia atrás a las actividades 1.x.',
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
    estado_validacion = models.CharField(
        'Estado de validación', max_length=20,
        choices=EstadoValidacion.choices, default=EstadoValidacion.PENDIENTE,
    )
    observacion_validacion = models.TextField('Observación del Delegado', blank=True)

    class Meta:
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'
        ordering = ['-fecha', 'codigo']
        permissions = [('validar_actividad', 'Puede validar o rechazar actividades de su delegación')]

    # ------------------------------------------------------------ código
    @staticmethod
    def siguiente_codigo(sigla):
        """Siguiente código correlativo para un área: TR-0001, TR-0002, ...
        (RF-011: dos actividades nunca reciben el mismo código)."""
        prefijo = f'{sigla}-'
        numeros = []
        for codigo in Actividad.objects.filter(codigo__startswith=prefijo).values_list('codigo', flat=True):
            resto = codigo[len(prefijo):]
            if resto.isdigit():
                numeros.append(int(resto))
        return f'{prefijo}{(max(numeros) + 1) if numeros else 1:04d}'

    # ------------------------------------------------------------ puntaje
    def motivos_sin_puntaje(self):
        """Reglas de la versión 2.0 que impiden que la actividad sume puntaje."""
        motivos = []
        if self.tipo_gestion == self.TipoGestion.PREVIA:
            motivos.append('es una gestión previa (solo la realización da punto)')
        if self.tipo_solicitante == self.TipoSolicitante.DELEGADO:
            motivos.append('el solicitante es el propio Delegado (otra gestión)')
        if not (self.contacto or '').strip() or not (self.telefono_contacto or '').strip():
            motivos.append('falta el nombre o el teléfono del usuario')
        return motivos

    def actualizar_puntaje(self):
        if self.version_reglas.startswith('1.'):
            self.puntuable, self.motivo_sin_puntaje = True, ''
            return
        motivos = self.motivos_sin_puntaje()
        self.puntuable = not motivos
        self.motivo_sin_puntaje = ('No suma: ' + '; '.join(motivos) + '.')[:200] if motivos else ''

    @property
    def suma_al_avance(self):
        """Aporta al cumplimiento: validada por el Delegado y puntuable."""
        return self.puntuable and self.estado_validacion == self.EstadoValidacion.VALIDADA

    def save(self, *args, **kwargs):
        self.actualizar_puntaje()
        campos = kwargs.get('update_fields')
        if campos is not None:
            kwargs['update_fields'] = list(set(campos) | {'puntuable', 'motivo_sin_puntaje'})
        if not self.codigo:
            sigla = 'AD'
            if self.funcionario_id:
                sigla = self.funcionario.cargo.area or 'AD'
            with transaction.atomic():
                self.codigo = self.siguiente_codigo(sigla)
                return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)

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
        self.estado_validacion = self.EstadoValidacion.VALIDADA
        self.observacion_validacion = ''
        self.save(update_fields=['validado', 'validado_por', 'fecha_validacion',
                                 'estado_validacion', 'observacion_validacion'])

    def rechazar(self, delegado, observacion):
        """El Delegado rechaza la evidencia con una observación (CA-02): la
        actividad no aporta al avance hasta que se corrija y se apruebe."""
        if delegado.rol != 'Delegado':
            raise ValueError('Solo un Funcionario con rol "Delegado" puede rechazar una actividad.')
        if delegado.id == self.funcionario_id:
            raise ValueError('El Funcionario que registró la actividad no puede revisarla él mismo.')
        if not (observacion or '').strip():
            raise ValueError('Debe indicar el motivo del rechazo.')
        self.validado = False
        self.validado_por = delegado
        self.fecha_validacion = timezone.now()
        self.estado_validacion = self.EstadoValidacion.RECHAZADA
        self.observacion_validacion = observacion.strip()
        self.save(update_fields=['validado', 'validado_por', 'fecha_validacion',
                                 'estado_validacion', 'observacion_validacion'])

    @property
    def editable_por_funcionario(self):
        return self.estado_validacion != self.EstadoValidacion.VALIDADA


EXTENSIONES_EVIDENCIA = ('.jpg', '.jpeg', '.png', '.pdf')


def ruta_evidencia(instancia, nombre_archivo):
    """La evidencia se guarda con el código de la actividad como nombre
    (RF-011 / presentación: el código sirve para nombrar la fotografía)."""
    extension = os.path.splitext(nombre_archivo)[1].lower()
    numero = instancia.actividad.evidencias.count() + 1
    return f'evidencias/{instancia.actividad.codigo}_{numero}{extension}'


def validar_archivo_evidencia(archivo):
    extension = os.path.splitext(archivo.name)[1].lower()
    if extension not in EXTENSIONES_EVIDENCIA:
        raise ValidationError('Formato no permitido. Use una fotografía JPG o PNG, o un PDF.')
    maximo = getattr(settings, 'SGR_EVIDENCIA_MAX_MB', 5)
    if archivo.size > maximo * 1024 * 1024:
        raise ValidationError(f'El archivo no puede superar los {maximo} MB.')


class Evidencia(models.Model):
    """Fotografía o documento que respalda una actividad. La sube el
    Funcionario que registró la actividad y la revisa su Delegado."""

    actividad = models.ForeignKey(
        Actividad, on_delete=models.CASCADE, related_name='evidencias', verbose_name='Actividad',
    )
    archivo = models.FileField('Archivo', upload_to=ruta_evidencia, validators=[validar_archivo_evidencia])
    descripcion = models.CharField('Descripción', max_length=200, blank=True)
    subida_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='evidencias_subidas', verbose_name='Subida por',
    )
    fecha_carga = models.DateTimeField('Fecha de carga', default=timezone.now)

    class Meta:
        verbose_name = 'Evidencia'
        verbose_name_plural = 'Evidencias'
        ordering = ['fecha_carga']

    def __str__(self):
        return os.path.basename(self.archivo.name)

    @property
    def es_imagen(self):
        return os.path.splitext(self.archivo.name)[1].lower() in ('.jpg', '.jpeg', '.png')
