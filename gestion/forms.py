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

from comun.validadores import nombre_repetido, validar_nombre, validar_telefono
from organizacion.models import Funcionario

from .models import Actividad, Categoria, Evidencia, validar_archivo_evidencia


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
        fields = ['fecha', 'categoria', 'estado', 'descripcion', 'solicitud_problema', 'contacto', 'telefono_contacto']
        widgets = {
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'solicitud_problema': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_contacto': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {'categoria': 'Ítem / categoría de la actividad', 'descripcion': 'Acción realizada'}

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

    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if fecha is None:
            return fecha
        hoy = timezone.localdate()
        dias = getattr(settings, 'SGR_DIAS_REGISTRO_RETROACTIVO', 7)
        if fecha > hoy:
            raise forms.ValidationError('La fecha de la actividad no puede ser futura.')
        if not self.instance.pk and fecha < hoy - timedelta(days=dias):
            raise forms.ValidationError(
                f'Solo se pueden registrar actividades de hasta {dias} días atrás.')
        return fecha

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


class RevisionForm(forms.Form):
    """El Delegado aprueba o rechaza la evidencia de una actividad."""

    DECISIONES = [('aprobar', 'Aprobar (la actividad suma al avance)'),
                  ('rechazar', 'Rechazar (el funcionario debe corregir)')]
    decision = forms.ChoiceField(label='Decisión', choices=DECISIONES, widget=forms.RadioSelect)
    observacion = forms.CharField(
        label='Observación', required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        help_text='Obligatoria si se rechaza.',
    )

    def __init__(self, *args, actividad=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.actividad = actividad

    def clean(self):
        datos = super().clean()
        if datos.get('decision') == 'rechazar' and not (datos.get('observacion') or '').strip():
            self.add_error('observacion', 'Indique el motivo del rechazo para que el funcionario pueda corregir.')
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
