"""
Formularios de la app 'gestion' (Aplicación 2).

Evaluación Sumativa 2: las vistas crear/editar de Actividad dejan de ser
marcadores de posición ('en_construccion.html') y pasan a usar ModelForm
real contra la base de datos.

ActividadForm: formulario normal (crea/edita los datos de la actividad).
Lo usa el Funcionario que registra la actividad; por eso NO incluye los
campos de validación ('validado', 'validado_por') — esos solo los puede
tocar un Delegado (ver retroalimentación del profesor Ciceo en
gestion/models.py) y se exponen aparte en ValidacionForm.
"""
from datetime import timedelta

from django import forms
from django.conf import settings
from django.utils import timezone

from comun.validadores import nombre_repetido, validar_nombre, validar_telefono, validar_texto_minimo
from delegaciones.models import OrganizacionComunitaria
from organizacion.models import Funcionario, Periodo

from .models import Actividad, Carta, Categoria, Compromiso, Evidencia, validar_archivo_evidencia


def inicio_ventana_registro(hoy=None):
    """Primer día que todavía se puede ingresar (v2.0, regla 4: cierre semanal).

    La semana de trabajo va de lunes a viernes y se cierra el lunes
    siguiente: el lunes aún se puede ingresar la semana anterior, pero
    desde el martes solo se ingresa la semana en curso.
    """
    hoy = hoy or timezone.localdate()
    lunes = hoy - timedelta(days=hoy.weekday())
    return lunes - timedelta(days=7) if hoy.weekday() == 0 else lunes


def ingresos_de_hoy(funcionario, hoy=None):
    """Actividades que el funcionario ya ingresó hoy (v2.0, regla 3)."""
    hoy = hoy or timezone.localdate()
    return Actividad.objects.filter(funcionario=funcionario, fecha_registro__date=hoy).count()


class ActividadForm(forms.ModelForm):
    """Registro de una actividad por el Funcionario.

    Retroalimentación Eval 2: el funcionario NO elige la delegación, ni el
    funcionario, ni escribe el código. La delegación y el funcionario salen
    de su propia cuenta, el código se genera con la sigla de su área
    (TR-0001) y el estado parte en Pendiente. La fecha puede ser de días
    anteriores, pero no futura ni más antigua que el plazo configurado.
    """

    evidencia = forms.FileField(
        label='Evidencia (fotografía o PDF)', required=False,
        help_text='Opcional al registrar. JPG, PNG o PDF, hasta 5 MB. También se puede subir después.',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.jpg,.jpeg,.png,.pdf'}),
    )

    class Meta:
        model = Actividad
        fields = ['fecha', 'categoria', 'tipo_gestion', 'estado', 'descripcion', 'tipo_solicitante', 'organizacion',
                  'solicitud_problema', 'vecino', 'contacto', 'telefono_contacto']
        widgets = {
            'tipo_gestion': forms.RadioSelect,
            'tipo_solicitante': forms.Select(attrs={'class': 'form-select'}),
            'organizacion': forms.Select(attrs={'class': 'form-select'}),
            'vecino': forms.Select(attrs={'class': 'form-select', 'data-autocompletar': 'vecino'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'solicitud_problema': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_contacto': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'categoria': 'Ítem / categoría de la actividad', 'descripcion': 'Acción realizada',
            'contacto': 'Nombre del usuario (vecino/a)', 'telefono_contacto': 'Teléfono del usuario',
        }
        help_texts = {
            'contacto': 'Obligatorio para que la actividad sume puntaje (v2.0).',
            'telefono_contacto': 'Obligatorio para que la actividad sume puntaje (v2.0).',
            'organizacion': 'Solo si la solicitó una organización comunitaria.',
        }

    def __init__(self, *args, funcionario=None, elegir_funcionario=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.funcionario = funcionario
        if not self.instance.pk:
            # Al registrar, el estado parte en Pendiente (no lo elige el usuario).
            del self.fields['estado']
        else:
            del self.fields['evidencia']
        if elegir_funcionario:
            # Solo el Administrador registra en nombre de otro funcionario.
            self.fields['funcionario'] = forms.ModelChoiceField(
                label='Funcionario', queryset=Funcionario.objects.filter(activo=True, delegacion__activa=True)
                .exclude(rol='Delegado').select_related('delegacion'),
                widget=forms.Select(attrs={'class': 'form-select'}),
            )
            self.order_fields(['funcionario'])
        organizaciones = OrganizacionComunitaria.objects.filter(activa=True)
        delegacion = getattr(funcionario, 'delegacion', None) or getattr(self.instance, 'delegacion', None)
        if delegacion is not None and not elegir_funcionario:
            organizaciones = organizaciones.filter(delegacion=delegacion)
        if 'organizacion' in self.fields:
            self.fields['organizacion'].queryset = organizaciones
        # v3.0: vecinos ya registrados (autocompletar nombre y teléfono)
        from territorio.models import Vecino
        vecinos = Vecino.objects.all()
        if delegacion is not None and not elegir_funcionario:
            vecinos = vecinos.filter(delegacion=delegacion)
        self.fields['vecino'].queryset = vecinos
        self.fields['vecino'].required = False
        if not self.instance.pk:
            self.fields['ingresar_al_tubo'] = forms.BooleanField(
                label='Ingresar también al Tubo (agenda colectiva) para hacerle seguimiento', required=False,
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
        self.fields['tipo_gestion'].widget.attrs['class'] = 'form-check-input'
        if 'tipo_solicitante' in self.fields:
            self.fields['tipo_solicitante'].required = False
        # Si el formulario no los envía (p. ej. integraciones antiguas), se usan
        # los valores por defecto del modelo: realización y solicitante vecino.
        self.fields['tipo_gestion'].required = False

    def clean_tipo_gestion(self):
        return self.cleaned_data.get('tipo_gestion') or Actividad.TipoGestion.REALIZACION

    def clean_tipo_solicitante(self):
        return self.cleaned_data.get('tipo_solicitante') or Actividad.TipoSolicitante.VECINO

    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if fecha is None:
            return fecha
        hoy = timezone.localdate()
        if fecha > hoy:
            raise forms.ValidationError('La fecha de la actividad no puede ser futura.')
        cerrado = Periodo.cerrado_que_contiene(fecha)
        if cerrado is not None:
            raise forms.ValidationError(f'El período {cerrado} está cerrado: no se pueden registrar ni mover '
                                        'actividades a esas fechas (RN-013).')
        if not self.instance.pk or fecha != self.instance.fecha:
            inicio = inicio_ventana_registro(hoy)
            if fecha < inicio:
                raise forms.ValidationError(
                    f'Esa semana ya está cerrada. Hoy solo se pueden ingresar actividades desde el '
                    f'{inicio:%d/%m/%Y}: cada semana (lunes a viernes) se cierra el lunes siguiente.')
        return fecha

    def clean(self):
        datos = super().clean()
        vecino = datos.get('vecino')
        if vecino is not None:
            # Autocompletar en el servidor: si se eligió un vecino registrado,
            # su nombre y teléfono se usan cuando el formulario los trae vacíos.
            if not (datos.get('contacto') or '').strip():
                datos['contacto'] = vecino.nombre[:100]
            if not (datos.get('telefono_contacto') or '').strip():
                datos['telefono_contacto'] = vecino.telefono
        if (datos.get('tipo_solicitante') == Actividad.TipoSolicitante.ORGANIZACION
                and not datos.get('organizacion')):
            self.add_error('organizacion', 'Indique qué organización comunitaria hizo la solicitud.')
        if not self.instance.pk:
            funcionario = datos.get('funcionario') or self.funcionario
            maximo = getattr(settings, 'SGR_MAX_INGRESOS_DIARIOS', 7)
            if funcionario is not None and ingresos_de_hoy(funcionario) >= maximo:
                raise forms.ValidationError(
                    f'Ya ingresó {maximo} actividades hoy, que es el máximo diario. '
                    'Las siguientes se pueden ingresar mañana (dentro de la misma semana).')
        return datos

    def clean_telefono_contacto(self):
        telefono = (self.cleaned_data.get('telefono_contacto') or '').strip()
        if telefono:
            validar_telefono(telefono)
        return telefono

    def clean_evidencia(self):
        archivo = self.cleaned_data.get('evidencia')
        if archivo:
            validar_archivo_evidencia(archivo)
        return archivo

    def save(self, commit=True, usuario=None):
        actividad = super().save(commit=False)
        if not actividad.pk:
            funcionario = self.cleaned_data.get('funcionario') or self.funcionario
            actividad.funcionario = funcionario
            actividad.delegacion = funcionario.delegacion
        if commit:
            actividad.save()
            archivo = self.cleaned_data.get('evidencia')
            if archivo:
                Evidencia.objects.create(actividad=actividad, archivo=archivo, subida_por=usuario)
        return actividad


class EvidenciaForm(forms.ModelForm):
    class Meta:
        model = Evidencia
        fields = ['archivo', 'descripcion']
        widgets = {
            'archivo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.jpg,.jpeg,.png,.pdf'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 200,
                                                  'placeholder': 'Ej.: foto de la reunión con la junta de vecinos'}),
        }
        labels = {'archivo': 'Fotografía o PDF'}


class GestionSocialForm(ActividadForm):
    """v3.0 (Guía PI Ev. 3): gestión social. Tiene el mismo flujo que una
    actividad (código, evidencia, verificación, metas y Tubo), pero siempre
    se registra para un vecino y con un tipo/subtipo de atención."""

    class Meta(ActividadForm.Meta):
        fields = ['fecha', 'categoria', 'subtipo_atencion', 'tipo_gestion', 'estado', 'vecino', 'descripcion',
                  'solicitud_problema']
        labels = dict(ActividadForm.Meta.labels, descripcion='Atención realizada',
                      solicitud_problema='Situación o necesidad del vecino')
        widgets = dict(ActividadForm.Meta.widgets, subtipo_atencion=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from territorio.models import SubtipoAtencion
        self.fields['subtipo_atencion'].queryset = SubtipoAtencion.objects.filter(
            activo=True, tipo__activo=True).select_related('tipo')
        self.fields['subtipo_atencion'].required = True
        self.fields['vecino'].required = True
        self.fields['vecino'].help_text = 'Busque por RUT o nombre. Si no existe, regístrelo primero en Vecinos.'

    def clean_tipo_solicitante(self):
        return Actividad.TipoSolicitante.VECINO

    def save(self, commit=True, usuario=None):
        self.instance.clase = Actividad.Clase.SOCIAL
        self.instance.tipo_solicitante = Actividad.TipoSolicitante.VECINO
        vecino = self.cleaned_data.get('vecino')
        if vecino is not None:
            self.instance.contacto = vecino.nombre[:100]
            self.instance.telefono_contacto = vecino.telefono
        return super().save(commit=commit, usuario=usuario)


class RevisionForm(forms.Form):
    """El Delegado aprueba o rechaza la evidencia de una actividad."""

    DECISIONES = [('aprobar', 'Aprobar (la actividad suma al avance)'),
                  ('antecedentes', 'Solicitar más antecedentes (el funcionario completa)'),
                  ('rechazar', 'Rechazar (el funcionario debe corregir)')]
    decision = forms.ChoiceField(label='Decisión', choices=DECISIONES, widget=forms.RadioSelect)
    observacion = forms.CharField(
        label='Observación', required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text='Obligatoria si se rechaza o se piden más antecedentes.',
    )

    def __init__(self, *args, actividad=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.actividad = actividad

    def clean(self):
        datos = super().clean()
        if self.actividad is not None and self.actividad.periodo_cerrado is not None:
            raise forms.ValidationError(f'El período {self.actividad.periodo_cerrado} está cerrado: '
                                        'la validación ya no se puede cambiar (RN-013).')
        if datos.get('decision') == 'rechazar' and not (datos.get('observacion') or '').strip():
            self.add_error('observacion', 'Indique el motivo del rechazo para que el funcionario pueda corregir.')
        if datos.get('decision') == 'antecedentes' and not (datos.get('observacion') or '').strip():
            self.add_error('observacion', 'Indique qué antecedentes debe agregar el funcionario.')
        if datos.get('decision') == 'aprobar' and self.actividad and not self.actividad.evidencias.exists():
            raise forms.ValidationError('No se puede aprobar una actividad sin evidencia. Pida al funcionario que la suba.')
        return datos


class CategoriaForm(forms.ModelForm):
    """Mantenedor de la tabla maestra Categoría."""

    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 80}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 200}),
        }

    def clean_nombre(self):
        nombre = validar_nombre(self.cleaned_data.get('nombre'), minimo=3, campo='nombre de la categoría')
        if nombre_repetido(Categoria.objects.all(), 'nombre', nombre, self.instance.pk):
            raise forms.ValidationError('Ya existe una categoría con ese nombre.')
        return nombre

    def clean_descripcion(self):
        return (self.cleaned_data.get('descripcion') or '').strip()


# ---------------------------------------------------------------------------
# Agenda colectiva (RF-016 a RF-019)
# ---------------------------------------------------------------------------
class CompromisoForm(forms.ModelForm):
    class Meta:
        model = Compromiso
        fields = ['origen', 'solicitante', 'rut_solicitante', 'organizacion', 'territorio', 'descripcion', 'responsable',
                  'area_apoyo', 'fecha_solicitud', 'fecha_compromiso']
        widgets = {
            'origen': forms.Select(attrs={'class': 'form-select'}),
            'solicitante': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 150,
                                                  'placeholder': 'Nombre del vecino, dirigente u oficina'}),
            'rut_solicitante': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 12,
                                                      'placeholder': '12.345.678-5 (opcional)'}),
            'organizacion': forms.Select(attrs={'class': 'form-select'}),
            'territorio': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 120,
                                                 'placeholder': 'Ej.: sector Las Rojas alto'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'responsable': forms.Select(attrs={'class': 'form-select'}),
            'area_apoyo': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 120,
                                                 'placeholder': 'Ej.: Diserco, Social, Organizaciones comunitarias'}),
            'fecha_solicitud': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'fecha_compromiso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
        }
        help_texts = {'fecha_compromiso': 'Fecha en que el equipo se compromete a cumplir.'}

    def __init__(self, *args, delegacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.delegacion = delegacion or getattr(self.instance, 'delegacion', None)
        equipo = Funcionario.objects.filter(activo=True, rol__in=['Funcionario', 'Delegado'])
        organizaciones = OrganizacionComunitaria.objects.filter(activa=True)
        if self.delegacion is not None:
            equipo = equipo.filter(delegacion=self.delegacion)
            organizaciones = organizaciones.filter(delegacion=self.delegacion)
        else:
            # Administrador sin delegación propia: elige la delegación.
            from delegaciones.models import Delegacion
            self.fields['delegacion'] = forms.ModelChoiceField(
                label='Delegación', queryset=Delegacion.objects.filter(activa=True),
                widget=forms.Select(attrs={'class': 'form-select'}))
            self.order_fields(['delegacion'])
        self.fields['responsable'].queryset = equipo.select_related('cargo')
        self.fields['responsable'].label_from_instance = lambda f: f'{f.nombre} · {f.cargo.nombre_cargo}'
        self.fields['organizacion'].queryset = organizaciones
        if self.instance.pk:
            # El responsable se cambia con "Reasignar" para que quede en el historial.
            del self.fields['responsable']

    def clean_solicitante(self):
        return validar_nombre(self.cleaned_data.get('solicitante'), minimo=3, campo='solicitante')

    def clean_rut_solicitante(self):
        from comun.validadores import normalizar_rut
        rut = (self.cleaned_data.get('rut_solicitante') or '').strip()
        return normalizar_rut(rut) if rut else ''

    def clean(self):
        datos = super().clean()
        solicitud, compromiso = datos.get('fecha_solicitud'), datos.get('fecha_compromiso')
        if solicitud and solicitud > timezone.localdate():
            self.add_error('fecha_solicitud', 'La fecha de la solicitud no puede ser futura.')
        if solicitud and compromiso and compromiso < solicitud:
            self.add_error('fecha_compromiso', 'La fecha comprometida no puede ser anterior a la solicitud.')
        delegacion = datos.get('delegacion') or self.delegacion
        responsable = datos.get('responsable')
        if delegacion and responsable and responsable.delegacion_id != delegacion.pk:
            self.add_error('responsable', 'El responsable debe pertenecer a la delegación del compromiso.')
        if delegacion is not None:
            self.instance.delegacion = delegacion
        return datos


class CambioEstadoCompromisoForm(forms.Form):
    estado = forms.ChoiceField(label='Nuevo estado', widget=forms.Select(attrs={'class': 'form-select'}))
    observacion = forms.CharField(label='Observación del avance',
                                  widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))

    def __init__(self, *args, compromiso=None, puede_reabrir=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estado'].choices = [(e, e) for e in compromiso.estados_siguientes(puede_reabrir)]


class ReasignarCompromisoForm(forms.Form):
    responsable = forms.ModelChoiceField(label='Nuevo responsable', queryset=Funcionario.objects.none(),
                                         widget=forms.Select(attrs={'class': 'form-select'}))
    motivo = forms.CharField(label='Motivo', widget=forms.TextInput(
        attrs={'class': 'form-control', 'maxlength': 200, 'placeholder': 'Ej.: licencia médica'}))

    def __init__(self, *args, compromiso=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsable'].queryset = (Funcionario.objects.filter(
            delegacion=compromiso.delegacion, activo=True, rol__in=['Funcionario', 'Delegado'])
            .exclude(pk=compromiso.responsable_id))


class CartaForm(forms.ModelForm):
    """v3.0: Tubo de cartas. La delegación sale de la cuenta del usuario."""

    class Meta:
        model = Carta
        fields = ['fecha_ingreso', 'para', 'remite', 'rut_remite', 'telefono_remite', 'tema', 'encargado', 'estado',
                  'pronunciamiento', 'derivada_a']
        widgets = {
            'fecha_ingreso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'para': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej.: Delegado, Alcaldía, Dideco'}),
            'remite': forms.TextInput(attrs={'class': 'form-control'}),
            'rut_remite': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-5 (opcional)'}),
            'telefono_remite': forms.TextInput(attrs={'class': 'form-control'}),
            'tema': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'encargado': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'pronunciamiento': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'derivada_a': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, delegacion=None, puede_cerrar=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.delegacion = delegacion or getattr(self.instance, 'delegacion', None)
        equipo = Funcionario.objects.filter(activo=True)
        if self.delegacion is not None:
            equipo = equipo.filter(delegacion=self.delegacion)
        else:
            from delegaciones.models import Delegacion
            self.fields['delegacion'] = forms.ModelChoiceField(
                label='Delegación', queryset=Delegacion.objects.filter(activa=True),
                widget=forms.Select(attrs={'class': 'form-select'}))
            self.order_fields(['delegacion'])
        self.fields['encargado'].queryset = equipo.order_by('nombre')
        if not puede_cerrar:
            # Solo el Delegado aprueba o finaliza una carta.
            self.fields['estado'].choices = [c for c in Carta.Estado.choices if c[0] not in Carta.CERRADOS]

    def clean_remite(self):
        return validar_texto_minimo(self.cleaned_data.get('remite'), minimo=3, campo='remitente')

    def clean_rut_remite(self):
        from comun.validadores import normalizar_rut
        rut = (self.cleaned_data.get('rut_remite') or '').strip()
        return normalizar_rut(rut) if rut else ''

    def clean_telefono_remite(self):
        telefono = (self.cleaned_data.get('telefono_remite') or '').strip()
        if telefono:
            validar_telefono(telefono)
        return telefono

    def clean_fecha_ingreso(self):
        fecha = self.cleaned_data.get('fecha_ingreso')
        if fecha and fecha > timezone.localdate():
            raise forms.ValidationError('La fecha de ingreso no puede ser futura.')
        return fecha

    def clean(self):
        datos = super().clean()
        delegacion = datos.get('delegacion') or self.delegacion
        encargado = datos.get('encargado')
        if delegacion and encargado and encargado.delegacion_id != delegacion.pk:
            self.add_error('encargado', 'El encargado debe pertenecer a la delegación.')
        if datos.get('estado') == Carta.Estado.FINALIZADA and not (datos.get('pronunciamiento') or '').strip():
            self.add_error('pronunciamiento', 'Para finalizar la carta indique el pronunciamiento o respuesta.')
        if delegacion is not None:
            self.instance.delegacion = delegacion
        return datos
