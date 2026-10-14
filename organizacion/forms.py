"""
Formularios de los mantenedores de la app 'organizacion' (tablas maestras
Cargo, Funcionario y Meta), con sus validaciones y reglas de negocio.
"""
from django import forms
from django.db.models import Sum

from comun.validadores import nombre_repetido, normalizar_rut, validar_nombre, validar_texto_minimo

from .models import CargoFuncion, Funcionario, MetaProyecto

UNIDADES = [
    ('Porcentaje', 'Porcentaje'),
    ('Cantidad', 'Cantidad'),
    ('Días', 'Días'),
    ('Horas', 'Horas'),
]


class CargoFuncionForm(forms.ModelForm):
    class Meta:
        model = CargoFuncion
        fields = ['nombre_cargo', 'descripcion', 'active']
        widgets = {
            'nombre_cargo': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'maxlength': 500}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_nombre_cargo(self):
        nombre = validar_nombre(self.cleaned_data.get('nombre_cargo'), minimo=3, campo='nombre del cargo')
        if nombre_repetido(CargoFuncion.objects.all(), 'nombre_cargo', nombre, self.instance.pk):
            raise forms.ValidationError('Ya existe un cargo con ese nombre.')
        return nombre

    def clean_descripcion(self):
        descripcion = (self.cleaned_data.get('descripcion') or '').strip()
        if len(descripcion) > 500:
            raise forms.ValidationError('La descripción no puede superar los 500 caracteres.')
        return descripcion


class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = ['nombre', 'rut', 'email', 'delegacion', 'cargo', 'rol', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-5', 'maxlength': 12}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'delegacion': forms.Select(attrs={'class': 'form-select'}),
            'cargo': forms.Select(attrs={'class': 'form-select'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'rut': 'Con puntos y guion. Se valida el dígito verificador.',
            'rol': 'Solo puede existir un Delegado activo por delegación.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo se ofrecen cargos vigentes (más el cargo actual al editar).
        cargos = CargoFuncion.objects.filter(active=True)
        if self.instance.pk:
            cargos = cargos | CargoFuncion.objects.filter(pk=self.instance.cargo_id)
        self.fields['cargo'].queryset = cargos.distinct()

    def clean_nombre(self):
        return validar_nombre(self.cleaned_data.get('nombre'), minimo=3, campo='nombre')

    def clean_rut(self):
        rut = normalizar_rut(self.cleaned_data.get('rut'))
        if Funcionario.objects.filter(rut=rut).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe un funcionario con ese RUT.')
        return rut

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if Funcionario.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe un funcionario con ese correo.')
        return email

    def clean(self):
        datos = super().clean()
        delegacion, rol, activo = datos.get('delegacion'), datos.get('rol'), datos.get('activo')
        if delegacion and rol == 'Delegado' and activo:
            otro = (Funcionario.objects.filter(delegacion=delegacion, rol='Delegado', activo=True)
                    .exclude(pk=self.instance.pk).first())
            if otro:
                raise forms.ValidationError(
                    f'La delegación {delegacion} ya tiene un Delegado activo ({otro.nombre}). '
                    'Cada delegación tiene un solo Delegado.'
                )
        return datos


class MetaProyectoForm(forms.ModelForm):
    unidad = forms.ChoiceField(
        label='Unidad de medida', choices=UNIDADES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = MetaProyecto
        fields = ['cargo', 'item_medible', 'valor_objetivo', 'unidad', 'ponderador']
        widgets = {
            'cargo': forms.Select(attrs={'class': 'form-select'}),
            'item_medible': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'valor_objetivo': forms.TextInput(attrs={'class': 'form-control', 'inputmode': 'decimal'}),
            'ponderador': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
        }
        help_texts = {
            'valor_objetivo': 'Número mayor que cero. Si la unidad es Porcentaje, no puede superar 100.',
            'ponderador': 'Entre 1 y 100. La suma de ponderadores de un cargo no puede superar 100 %.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        actual = self.instance.unidad if self.instance.pk else None
        if actual and actual not in dict(UNIDADES):
            self.fields['unidad'].choices = UNIDADES + [(actual, actual)]

    def clean_item_medible(self):
        return validar_texto_minimo(self.cleaned_data.get('item_medible'), minimo=3, campo='nombre de la meta')

    def clean_valor_objetivo(self):
        texto = (self.cleaned_data.get('valor_objetivo') or '').strip().replace(',', '.')
        try:
            valor = float(texto)
        except ValueError:
            raise forms.ValidationError('El valor objetivo debe ser un número (por ejemplo 20 o 90,5).')
        if valor <= 0:
            raise forms.ValidationError('El valor objetivo debe ser mayor que cero (RN-002).')
        return texto

    def clean_ponderador(self):
        ponderador = self.cleaned_data.get('ponderador')
        if ponderador is None or not 1 <= ponderador <= 100:
            raise forms.ValidationError('El ponderador debe estar entre 1 y 100.')
        return ponderador

    def clean(self):
        datos = super().clean()
        cargo, ponderador = datos.get('cargo'), datos.get('ponderador')
        unidad, valor = datos.get('unidad'), datos.get('valor_objetivo')
        if unidad == 'Porcentaje' and valor and float(valor) > 100:
            self.add_error('valor_objetivo', 'Un valor en porcentaje no puede superar 100.')
        if cargo and ponderador:
            otras = MetaProyecto.objects.filter(cargo=cargo).exclude(pk=self.instance.pk)
            suma = (otras.aggregate(total=Sum('ponderador'))['total'] or 0) + ponderador
            if suma > 100:
                self.add_error(
                    'ponderador',
                    f'La suma de ponderadores del cargo {cargo} quedaría en {suma} %. No puede superar 100 % (RN-001).',
                )
        return datos
