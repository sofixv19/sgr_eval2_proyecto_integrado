"""
Formularios de la app 'delegaciones' (Aplicación 1).

Evaluación Sumativa 2: las vistas crear/editar/eliminar dejan de ser
marcadores de posición ('en_construccion.html') y pasan a usar un
ModelForm real, que valida y guarda contra la base de datos.
"""
from django import forms

from comun.validadores import nombre_repetido, validar_nombre, validar_telefono, validar_texto_minimo

from .models import Delegacion, OrganizacionComunitaria


class DelegacionForm(forms.ModelForm):
    class Meta:
        model = Delegacion
        fields = ['nombre', 'encargado', 'direccion', 'telefono', 'email', 'territorio', 'enfoque', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'encargado': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'territorio': forms.TextInput(attrs={'class': 'form-control'}),
            'enfoque': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_nombre(self):
        nombre = validar_texto_minimo(self.cleaned_data.get('nombre'), minimo=3, campo='nombre de la delegación')
        if nombre_repetido(Delegacion.objects.all(), 'nombre', nombre, self.instance.pk):
            raise forms.ValidationError('Ya existe una delegación con ese nombre.')
        return nombre

    def clean_encargado(self):
        return validar_nombre(self.cleaned_data.get('encargado'), minimo=3, campo='nombre del encargado/a')

    def clean_telefono(self):
        telefono = (self.cleaned_data.get('telefono') or '').strip()
        validar_telefono(telefono)
        return telefono

    def clean_email(self):
        return (self.cleaned_data.get('email') or '').strip().lower()

    def clean_direccion(self):
        return validar_texto_minimo(self.cleaned_data.get('direccion'), minimo=5, campo='dirección')


class OrganizacionForm(forms.ModelForm):
    """Versión 2.0 (RF-039): organizaciones territoriales y funcionales."""

    class Meta:
        model = OrganizacionComunitaria
        fields = ['nombre', 'tipo', 'delegacion', 'domicilio', 'socios_activos', 'fecha_constitucion',
                  'registro_pj', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 200}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'delegacion': forms.Select(attrs={'class': 'form-select'}),
            'domicilio': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 200}),
            'socios_activos': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'fecha_constitucion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'registro_pj': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 30}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'tipo': 'Junta de Vecinos = organización territorial. El resto son funcionales: agrupan por un '
                    'objetivo o interés común, sin importar el territorio exacto donde vive cada socio.',
        }

    def __init__(self, *args, delegacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.delegacion_fija = delegacion
        if delegacion is not None:
            # El Delegado registra organizaciones solo de su propia delegación.
            del self.fields['delegacion']
        else:
            self.fields['delegacion'].queryset = Delegacion.objects.filter(activa=True)

    def clean_nombre(self):
        return validar_texto_minimo(self.cleaned_data.get('nombre'), minimo=3, campo='nombre de la organización')

    def clean(self):
        datos = super().clean()
        delegacion = self.delegacion_fija or datos.get('delegacion')
        nombre = datos.get('nombre')
        if delegacion and nombre:
            repetida = OrganizacionComunitaria.objects.filter(delegacion=delegacion, nombre__iexact=nombre)
            if repetida.exclude(pk=self.instance.pk).exists():
                self.add_error('nombre', 'Ya existe una organización con ese nombre en esta delegación.')
        if self.delegacion_fija is not None:
            self.instance.delegacion = self.delegacion_fija
        return datos
