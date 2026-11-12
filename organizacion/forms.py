"""
Formularios de los mantenedores de la app 'organizacion' (tablas maestras
Cargo, Funcionario y Meta), con sus validaciones y reglas de negocio.
"""
from django import forms
from django.db.models import Sum

from comun.validadores import nombre_repetido, normalizar_rut, validar_nombre, validar_texto_minimo

from delegaciones.models import Delegacion
from gestion.models import Categoria

from .models import CargoFuncion, Funcionario, MetaProyecto, Periodo

UNIDADES = [
    ('Porcentaje', 'Porcentaje'),
    ('Cantidad', 'Cantidad'),
    ('Días', 'Días'),
    ('Horas', 'Horas'),
]


class CargoFuncionForm(forms.ModelForm):
    class Meta:
        model = CargoFuncion
        fields = ['nombre_cargo', 'area', 'descripcion', 'active']
        widgets = {
            'nombre_cargo': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'area': forms.Select(attrs={'class': 'form-select'}),
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

    # modo: 'admin' (todos los campos), 'coordinador' (crea y asigna
    # Delegados a una delegación) o 'delegado' (crea funcionarios de SU
    # delegación). Retroalimentación del profesor Caiceo, Evaluación 2.
    def __init__(self, *args, modo='admin', delegacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.modo = modo
        self.delegacion_fija = delegacion
        # Solo se ofrecen cargos vigentes (más el cargo actual al editar).
        cargos = CargoFuncion.objects.filter(active=True)
        if self.instance.pk:
            cargos = cargos | CargoFuncion.objects.filter(pk=self.instance.cargo_id)
        self.fields['cargo'].queryset = cargos.distinct()
        delegaciones = Delegacion.objects.filter(activa=True)
        if self.instance.pk:
            delegaciones = delegaciones | Delegacion.objects.filter(pk=self.instance.delegacion_id)
        self.fields['delegacion'].queryset = delegaciones.distinct()
        if modo == 'delegado':
            del self.fields['delegacion']
            del self.fields['rol']
        elif modo == 'coordinador':
            del self.fields['rol']
            self.fields['delegacion'].label = 'Delegación que tendrá a cargo'
            self.fields['delegacion'].help_text = 'Cada delegación tiene un solo Delegado activo.'

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
        if self.modo == 'delegado':
            # El Delegado solo crea funcionarios de SU delegación.
            self.instance.delegacion = delegacion = self.delegacion_fija
            self.instance.rol = rol = 'Funcionario'
        elif self.modo == 'coordinador':
            # El Coordinador crea a los Delegados.
            self.instance.rol = rol = 'Delegado'
        if delegacion and rol == 'Delegado' and activo:
            otro = (Funcionario.objects.filter(delegacion=delegacion, rol='Delegado', activo=True)
                    .exclude(pk=self.instance.pk).first())
            if otro:
                raise forms.ValidationError(
                    f'La delegación {delegacion} ya tiene un Delegado activo ({otro.nombre}). '
                    'Cada delegación tiene un solo Delegado.'
                )
        return datos


class PeriodoForm(forms.ModelForm):
    """Mantenedor de la tabla maestra Período (tabla 'periodo' de la Evaluación 1)."""

    class Meta:
        model = Periodo
        fields = ['nombre', 'fecha_inicio', 'fecha_fin', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 60,
                                             'placeholder': 'Segundo semestre 2026'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }
        help_texts = {
            'estado': ('Un período Cerrado no se puede modificar, salvo para volver a abrirlo (RN-013). '
                       'Solo puede haber un período Abierto.'),
        }

    def clean_nombre(self):
        nombre = validar_texto_minimo(self.cleaned_data.get('nombre'), minimo=3, campo='nombre del período')
        if nombre_repetido(Periodo.objects.all(), 'nombre', nombre, self.instance.pk):
            raise forms.ValidationError('Ya existe un período con ese nombre.')
        return nombre

    def clean(self):
        datos = super().clean()
        inicio, fin, estado = datos.get('fecha_inicio'), datos.get('fecha_fin'), datos.get('estado')
        if inicio and fin and fin <= inicio:
            self.add_error('fecha_fin', 'La fecha de término debe ser posterior a la fecha de inicio.')
        elif inicio and fin:
            otro = (Periodo.objects.filter(fecha_inicio__lte=fin, fecha_fin__gte=inicio)
                    .exclude(pk=self.instance.pk).first())
            if otro:
                raise forms.ValidationError(f'Las fechas se cruzan con el período "{otro}". Los períodos no pueden solaparse.')
        abiertos = Periodo.objects.filter(estado=Periodo.Estado.ABIERTO).exclude(pk=self.instance.pk)
        if estado == Periodo.Estado.ABIERTO and abiertos.exists():
            self.add_error('estado', 'Ya existe un período Abierto. Ciérrelo antes de abrir otro.')
        if self.instance.pk and self.instance.estado == Periodo.Estado.CERRADO and estado == Periodo.Estado.CERRADO:
            cambios = [c for c in ('nombre', 'fecha_inicio', 'fecha_fin') if c in self.changed_data]
            if cambios:
                raise forms.ValidationError(
                    'El período está Cerrado y no se puede modificar. Para corregirlo, primero cámbielo a Abierto (RN-013).')
        return datos


class MetaProyectoForm(forms.ModelForm):
    unidad = forms.ChoiceField(
        label='Unidad de medida', choices=UNIDADES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = MetaProyecto
        fields = ['cargo', 'periodo', 'item_medible', 'valor_objetivo', 'unidad', 'ponderador']
        widgets = {
            'cargo': forms.Select(attrs={'class': 'form-select'}),
            'periodo': forms.Select(attrs={'class': 'form-select'}),
            'item_medible': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 100}),
            'valor_objetivo': forms.TextInput(attrs={'class': 'form-control', 'inputmode': 'decimal'}),
            'ponderador': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
        }
        help_texts = {
            'valor_objetivo': 'Número mayor que cero. Si la unidad es Porcentaje, no puede superar 100.',
            'ponderador': 'Entre 1 y 100. La suma de ponderadores de un cargo en un período no puede superar 100 %.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['periodo'].required = True
        # No se pueden agregar metas a un período cerrado (se conserva el actual al editar).
        periodos = Periodo.objects.exclude(estado=Periodo.Estado.CERRADO)
        if self.instance.pk and self.instance.periodo_id:
            periodos = periodos | Periodo.objects.filter(pk=self.instance.periodo_id)
        self.fields['periodo'].queryset = periodos.distinct()
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
        cargo, ponderador, periodo = datos.get('cargo'), datos.get('ponderador'), datos.get('periodo')
        unidad, valor = datos.get('unidad'), datos.get('valor_objetivo')
        if unidad == 'Porcentaje' and valor and float(valor) > 100:
            self.add_error('valor_objetivo', 'Un valor en porcentaje no puede superar 100.')
        if cargo and ponderador and periodo:
            otras = MetaProyecto.objects.filter(cargo=cargo, periodo=periodo).exclude(pk=self.instance.pk)
            suma = (otras.aggregate(total=Sum('ponderador'))['total'] or 0) + ponderador
            if suma > 100:
                self.add_error(
                    'ponderador',
                    f'La suma de ponderadores del cargo {cargo} en el período {periodo} quedaría en {suma} %. '
                    'No puede superar 100 % (RN-001).',
                )
        return datos


class MetaFuncionarioForm(forms.ModelForm):
    """Meta que el Delegado asigna a un funcionario de su delegación.

    Retroalimentación Eval 2: "¿quién hace la pega de asignar esas metas?
    Usted como delegado". Cada meta mide una categoría de actividad: el
    avance es la cantidad de actividades VALIDADAS de esa categoría en el
    período. La suma de ponderadores de un funcionario en un período no
    puede superar 100 % (RN-001).
    """

    class Meta:
        model = MetaProyecto
        fields = ['funcionario', 'periodo', 'categoria', 'valor_objetivo', 'ponderador']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'periodo': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'valor_objetivo': forms.TextInput(attrs={'class': 'form-control', 'inputmode': 'numeric'}),
            'ponderador': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
        }
        labels = {
            'categoria': 'Ítem a medir (categoría de actividad)',
            'valor_objetivo': 'Meta del período (cantidad de actividades validadas)',
            'ponderador': 'Ponderador (%)',
        }
        help_texts = {
            'ponderador': 'Entre 1 y 100. La suma de las metas del funcionario en el período no puede superar 100 %.',
        }

    def __init__(self, *args, funcionarios=None, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ('funcionario', 'periodo', 'categoria'):
            self.fields[campo].required = True
        consulta = funcionarios if funcionarios is not None else Funcionario.objects.all()
        self.fields['funcionario'].queryset = consulta.filter(activo=True).exclude(rol='Delegado').select_related('delegacion')
        periodos = Periodo.objects.exclude(estado=Periodo.Estado.CERRADO)
        if self.instance.pk and self.instance.periodo_id:
            periodos = periodos | Periodo.objects.filter(pk=self.instance.periodo_id)
        self.fields['periodo'].queryset = periodos.distinct()
        self.fields['categoria'].queryset = Categoria.objects.all()

    def clean_valor_objetivo(self):
        texto = (self.cleaned_data.get('valor_objetivo') or '').strip().replace(',', '.')
        try:
            valor = float(texto)
        except ValueError:
            raise forms.ValidationError('La meta debe ser un número (por ejemplo 20).')
        if valor <= 0:
            raise forms.ValidationError('La meta debe ser mayor que cero (RN-002).')
        return texto

    def clean_ponderador(self):
        ponderador = self.cleaned_data.get('ponderador')
        if ponderador is None or not 1 <= ponderador <= 100:
            raise forms.ValidationError('El ponderador debe estar entre 1 y 100.')
        return ponderador

    def clean(self):
        datos = super().clean()
        funcionario, periodo, categoria = datos.get('funcionario'), datos.get('periodo'), datos.get('categoria')
        ponderador = datos.get('ponderador')
        if funcionario and periodo and categoria:
            repetida = (MetaProyecto.objects.filter(funcionario=funcionario, periodo=periodo, categoria=categoria)
                        .exclude(pk=self.instance.pk).exists())
            if repetida:
                self.add_error('categoria', 'Este funcionario ya tiene una meta para esa categoría en el período.')
        if funcionario and periodo and ponderador:
            otras = MetaProyecto.objects.filter(funcionario=funcionario, periodo=periodo).exclude(pk=self.instance.pk)
            suma = (otras.aggregate(total=Sum('ponderador'))['total'] or 0) + ponderador
            if suma > 100:
                self.add_error('ponderador', f'Las metas de {funcionario.nombre} en {periodo} sumarían {suma} %. '
                                             'No puede superar 100 % (RN-001).')
        return datos

    def save(self, commit=True):
        meta = super().save(commit=False)
        meta.cargo = meta.funcionario.cargo
        meta.item_medible = meta.categoria.nombre
        meta.unidad = 'Cantidad'
        if commit:
            meta.save()
        return meta
