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
    compromiso = models.ForeignKey(
        'gestion.Compromiso', on_delete=models.SET_NULL, null=True, blank=True, related_name='actividades',
        verbose_name='Compromiso de la agenda que cumple',
        help_text='Si la actividad cumple un compromiso de la agenda colectiva (RF-020).',
    )
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
    def periodo_cerrado(self):
        """Período Cerrado al que pertenece la actividad (CA-10): sus
        resultados ya no se pueden alterar sin reabrir el período."""
        from organizacion.models import Periodo
        return Periodo.cerrado_que_contiene(self.fecha)

    @property
    def editable_por_funcionario(self):
        return self.estado_validacion != self.EstadoValidacion.VALIDADA and self.periodo_cerrado is None


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


# ---------------------------------------------------------------------------
# Agenda colectiva o "tubo de trabajo" (Guía SGR 4.2, RF-016 a RF-021)
# ---------------------------------------------------------------------------
class Compromiso(models.Model):
    """Compromiso futuro adquirido con un vecino u organización, visible
    para el equipo de la delegación (agenda colectiva)."""

    class Estado(models.TextChoices):
        INGRESADO = 'Ingresado', 'Ingresado'
        PENDIENTE = 'Pendiente', 'Pendiente'
        EN_PROCESO = 'En proceso', 'En proceso'
        REALIZADO = 'Realizado', 'Realizado'

    class Origen(models.TextChoices):
        EXTERNO = 'EXT', 'Externo (vecino u organización)'
        INTERNO = 'INT', 'Interno (municipio)'

    # Transiciones permitidas (RF-018). Reabrir un compromiso realizado
    # (Realizado -> En proceso) solo lo puede hacer el Delegado o el Administrador.
    TRANSICIONES = {
        Estado.INGRESADO: [Estado.PENDIENTE, Estado.EN_PROCESO, Estado.REALIZADO],
        Estado.PENDIENTE: [Estado.EN_PROCESO, Estado.REALIZADO],
        Estado.EN_PROCESO: [Estado.PENDIENTE, Estado.REALIZADO],
        Estado.REALIZADO: [Estado.EN_PROCESO],
    }

    codigo = models.CharField('Código', max_length=20, unique=True, blank=True, editable=False)
    delegacion = models.ForeignKey(Delegacion, on_delete=models.PROTECT, related_name='compromisos',
                                   verbose_name='Delegación')
    origen = models.CharField('Origen', max_length=3, choices=Origen.choices, default=Origen.EXTERNO)
    solicitante = models.CharField('Solicitante', max_length=150)
    organizacion = models.ForeignKey(
        'delegaciones.OrganizacionComunitaria', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='compromisos', verbose_name='Organización solicitante',
    )
    territorio = models.CharField('Territorio / sector', max_length=120)
    descripcion = models.TextField('Actividad, solicitud o problema')
    responsable = models.ForeignKey(Funcionario, on_delete=models.PROTECT, related_name='compromisos',
                                    verbose_name='Responsable')
    area_apoyo = models.CharField('Área o persona de apoyo', max_length=120, blank=True)
    fecha_solicitud = models.DateField('Fecha de la solicitud', default=timezone.localdate)
    fecha_compromiso = models.DateField('Fecha comprometida')
    estado = models.CharField('Estado', max_length=20, choices=Estado.choices, default=Estado.INGRESADO)
    observacion = models.TextField('Avance u observaciones', blank=True)
    fecha_cierre = models.DateField('Fecha de cierre', null=True, blank=True, editable=False)
    actividad_origen = models.ForeignKey(
        'gestion.Actividad', on_delete=models.SET_NULL, null=True, blank=True, related_name='compromisos_generados',
        verbose_name='Actividad que lo originó',
    )
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='compromisos_creados', verbose_name='Registrado por')
    creado = models.DateTimeField('Fecha de registro', default=timezone.now, editable=False)

    class Meta:
        verbose_name = 'Compromiso (agenda colectiva)'
        verbose_name_plural = 'Agenda colectiva'
        ordering = ['fecha_compromiso', 'codigo']

    def __str__(self):
        return f'{self.codigo} · {self.solicitante}'

    def get_absolute_url(self):
        return reverse('gestion:compromiso_detalle', args=[self.pk])

    def save(self, *args, **kwargs):
        if not self.codigo:
            with transaction.atomic():
                numeros = [int(c[3:]) for c in Compromiso.objects.filter(codigo__startswith='AC-')
                           .values_list('codigo', flat=True) if c[3:].isdigit()]
                self.codigo = f'AC-{(max(numeros) + 1) if numeros else 1:04d}'
                return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)

    # ------------------------------------------------------------ plazos (RF-019)
    @property
    def esta_cerrado(self):
        return self.estado == self.Estado.REALIZADO

    @property
    def dias_restantes(self):
        return (self.fecha_compromiso - timezone.localdate()).days

    @property
    def vencido(self):
        return not self.esta_cerrado and self.dias_restantes < 0

    @property
    def proximo_a_vencer(self):
        dias = getattr(settings, 'SGR_DIAS_AVISO_COMPROMISO', 3)
        return not self.esta_cerrado and 0 <= self.dias_restantes <= dias

    @property
    def fuera_de_plazo(self):
        return self.esta_cerrado and self.fecha_cierre is not None and self.fecha_cierre > self.fecha_compromiso

    @property
    def situacion(self):
        """Texto y color para destacar el compromiso en la agenda."""
        if self.vencido:
            return 'rojo', f'Vencido hace {-self.dias_restantes} día{"s" if self.dias_restantes != -1 else ""}'
        if self.proximo_a_vencer:
            if self.dias_restantes == 0:
                return 'ambar', 'Vence hoy'
            return 'ambar', f'Vence en {self.dias_restantes} día{"s" if self.dias_restantes != 1 else ""}'
        if self.fuera_de_plazo:
            return 'ambar', 'Realizado fuera de plazo'
        if self.esta_cerrado:
            return 'verde', 'Realizado'
        return 'gris', f'Faltan {self.dias_restantes} días'

    def estados_siguientes(self, puede_reabrir=False):
        siguientes = list(self.TRANSICIONES.get(self.estado, []))
        if self.estado == self.Estado.REALIZADO and not puede_reabrir:
            return []
        return siguientes

    def cambiar_estado(self, nuevo, usuario, observacion, puede_reabrir=False):
        """Cambio de estado controlado (RF-018): guarda estado anterior, nuevo,
        autor, fecha y observación."""
        if nuevo not in self.estados_siguientes(puede_reabrir):
            raise ValidationError(f'No se puede pasar de "{self.estado}" a "{nuevo}".')
        if not (observacion or '').strip():
            raise ValidationError('Indique una observación del avance.')
        anterior = self.estado
        self.estado = nuevo
        self.fecha_cierre = timezone.localdate() if nuevo == self.Estado.REALIZADO else None
        self.observacion = observacion.strip()
        self.save(update_fields=['estado', 'fecha_cierre', 'observacion'])
        return CambioCompromiso.objects.create(
            compromiso=self, campo='Estado', valor_anterior=anterior, valor_nuevo=nuevo,
            observacion=observacion.strip(), autor=usuario,
        )

    def reasignar(self, nuevo_responsable, usuario, motivo):
        """Reasignación por ausencia u otro motivo (HU-15): conserva responsable
        anterior, nuevo, autor, fecha y motivo."""
        if not (motivo or '').strip():
            raise ValidationError('Indique el motivo de la reasignación.')
        anterior = self.responsable
        self.responsable = nuevo_responsable
        self.save(update_fields=['responsable'])
        return CambioCompromiso.objects.create(
            compromiso=self, campo='Responsable', valor_anterior=anterior.nombre,
            valor_nuevo=nuevo_responsable.nombre, observacion=motivo.strip(), autor=usuario,
        )


class CambioCompromiso(models.Model):
    """Historial de un compromiso: cambios de estado y reasignaciones (RF-018)."""

    compromiso = models.ForeignKey(Compromiso, on_delete=models.CASCADE, related_name='cambios',
                                   verbose_name='Compromiso')
    campo = models.CharField('Qué cambió', max_length=20)
    valor_anterior = models.CharField('Valor anterior', max_length=150, blank=True)
    valor_nuevo = models.CharField('Valor nuevo', max_length=150)
    observacion = models.TextField('Observación')
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                              related_name='cambios_compromisos', verbose_name='Autor')
    fecha = models.DateTimeField('Fecha', default=timezone.now)

    class Meta:
        verbose_name = 'Cambio de compromiso'
        verbose_name_plural = 'Historial de compromisos'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.compromiso.codigo}: {self.campo} {self.valor_anterior} → {self.valor_nuevo}'
