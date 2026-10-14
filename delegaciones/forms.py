"""
Formularios de la app 'delegaciones' (Aplicación 1).

Evaluación Sumativa 2: las vistas crear/editar/eliminar dejan de ser
marcadores de posición ('en_construccion.html') y pasan a usar un
ModelForm real, que valida y guarda contra la base de datos.
"""
from django import forms

from comun.validadores import nombre_repetido, validar_nombre, validar_telefono, validar_texto_minimo

from .models import Delegacion


class DelegacionForm(forms.ModelForm):
    class Meta:
        model = Delegacion
        fields = ['nombre', 'encargado', 'direccion', 'telefono', 'email', 'territorio', 'enfoque']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'encargado': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'territorio': forms.TextInput(attrs={'class': 'form-control'}),
            'enfoque': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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
