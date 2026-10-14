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
from django import forms

from comun.validadores import nombre_repetido, validar_nombre, validar_telefono
from organizacion.models import Funcionario

from .models import Actividad, Categoria


class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = [
            'codigo', 'fecha', 'delegacion', 'categoria', 'funcionario', 'estado',
            'descripcion', 'solicitud_problema', 'contacto', 'telefono_contacto',
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'delegacion': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'solicitud_problema': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'contacto': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_contacto': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_telefono_contacto(self):
        telefono = (self.cleaned_data.get('telefono_contacto') or '').strip()
        if telefono:
            validar_telefono(telefono)
        return telefono


class ValidacionForm(forms.ModelForm):
    """Formulario aparte, solo con el campo 'validado_por': lo usa el
    Delegado para validar una actividad que registró un Funcionario. El
    propio modelo (Actividad.clean()) rechaza que el Delegado elegido sea
    la misma persona que registró la actividad, o que no tenga rol
    'Delegado'."""

    class Meta:
        model = Actividad
        fields = ['validado_por']
        widgets = {
            'validado_por': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'validado_por': 'Delegado que valida esta actividad',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['validado_por'].queryset = Funcionario.objects.filter(rol='Delegado')
        self.fields['validado_por'].required = True

    def clean_validado_por(self):
        delegado = self.cleaned_data['validado_por']
        if delegado.rol != 'Delegado':
            raise forms.ValidationError('Solo un Funcionario con rol "Delegado" puede validar una actividad.')
        if delegado.id == self.instance.funcionario_id:
            raise forms.ValidationError('El Funcionario que registró la actividad no puede validarla él mismo.')
        return delegado

    def save(self, commit=True):
        actividad = self.instance
        delegado = self.cleaned_data['validado_por']
        actividad.marcar_validado(delegado)  # ya guarda y aplica la regla de negocio
        return actividad


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
