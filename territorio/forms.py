"""Formularios de la versión 3.0 con validaciones en el servidor."""
from django import forms

from comun.validadores import normalizar_rut, validar_nombre, validar_texto_minimo
from delegaciones.models import Delegacion, OrganizacionComunitaria
from organizacion.models import Funcionario

from .models import Hito, MembresiaOrganizacion, SubtipoAtencion, Territorio, TipoAtencion, Vecino


def _estilo(form):
    for nombre, campo in form.fields.items():
        widget = campo.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs.setdefault('class', 'form-check-input')
        elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
            widget.attrs.setdefault('class', 'form-select')
        else:
            widget.attrs.setdefault('class', 'form-control')


class DelegacionFijaMixin:
    """El Delegado y el Funcionario solo registran en su propia delegación:
    el campo desaparece y se asigna solo."""

    def _fijar_delegacion(self, delegacion):
        self.delegacion_fija = delegacion
        if delegacion is not None and 'delegacion' in self.fields:
            del self.fields['delegacion']
        elif 'delegacion' in self.fields:
            self.fields['delegacion'].queryset = Delegacion.objects.filter(activa=True)

    def delegacion_elegida(self):
        return self.delegacion_fija or self.cleaned_data.get('delegacion')

    def _aplicar_delegacion(self):
        if self.delegacion_fija is not None:
            self.instance.delegacion = self.delegacion_fija


class TerritorioForm(DelegacionFijaMixin, forms.ModelForm):
    class Meta:
        model = Territorio
        fields = ['nombre', 'delegacion', 'descripcion', 'activo']

    def __init__(self, *args, delegacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._fijar_delegacion(delegacion)
        _estilo(self)

    def clean_nombre(self):
        return validar_texto_minimo(self.cleaned_data.get('nombre'), minimo=3, campo='nombre del territorio')

    def clean(self):
        datos = super().clean()
        delegacion, nombre = self.delegacion_elegida(), datos.get('nombre')
        if delegacion and nombre and Territorio.objects.filter(delegacion=delegacion, nombre__iexact=nombre).exclude(
                pk=self.instance.pk).exists():
            self.add_error('nombre', 'Ya existe un territorio con ese nombre en esta delegación.')
        self._aplicar_delegacion()
        return datos


class VecinoForm(DelegacionFijaMixin, forms.ModelForm):
    class Meta:
        model = Vecino
        fields = ['rut', 'nombre', 'telefono', 'email', 'direccion', 'delegacion', 'territorio']

    def __init__(self, *args, delegacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._fijar_delegacion(delegacion)
        territorios = Territorio.objects.filter(activo=True)
        if delegacion is not None:
            territorios = territorios.filter(delegacion=delegacion)
        self.fields['territorio'].queryset = territorios
        _estilo(self)

    def clean_rut(self):
        try:
            rut = normalizar_rut(self.cleaned_data.get('rut'))
        except forms.ValidationError:
            raise
        if Vecino.objects.filter(rut=rut).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe un vecino con ese RUT. Búsquelo en el listado.')
        return rut

    def clean_nombre(self):
        return validar_nombre(self.cleaned_data.get('nombre'), minimo=5, campo='nombre')

    def clean(self):
        datos = super().clean()
        territorio, delegacion = datos.get('territorio'), self.delegacion_elegida()
        if territorio and delegacion and territorio.delegacion_id != delegacion.pk:
            self.add_error('territorio', 'El territorio no pertenece a la delegación elegida.')
        self._aplicar_delegacion()
        return datos


class MembresiaForm(forms.ModelForm):
    class Meta:
        model = MembresiaOrganizacion
        fields = ['organizacion', 'vecino', 'rol', 'cargo', 'desde', 'vigente']
        widgets = {'desde': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}

    def __init__(self, *args, delegacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        organizaciones = OrganizacionComunitaria.objects.filter(activa=True)
        vecinos = Vecino.objects.all()
        if delegacion is not None:
            organizaciones = organizaciones.filter(delegacion=delegacion)
            vecinos = vecinos.filter(delegacion=delegacion)
        self.fields['organizacion'].queryset = organizaciones
        self.fields['vecino'].queryset = vecinos
        _estilo(self)

    def clean(self):
        datos = super().clean()
        rol, cargo = datos.get('rol'), datos.get('cargo')
        if rol == MembresiaOrganizacion.Rol.DIRIGENTE and not cargo:
            self.add_error('cargo', 'Indique el cargo del dirigente en la directiva.')
        if rol == MembresiaOrganizacion.Rol.SOCIO and cargo:
            self.add_error('cargo', 'Un socio sin cargo debe quedar con "—". Cámbielo a Dirigente si tiene cargo.')
        organizacion, vecino = datos.get('organizacion'), datos.get('vecino')
        if organizacion and vecino and MembresiaOrganizacion.objects.filter(
                organizacion=organizacion, vecino=vecino).exclude(pk=self.instance.pk).exists():
            self.add_error('vecino', 'Este vecino ya está registrado en esa organización.')
        if organizacion and cargo and datos.get('vigente', True) and MembresiaOrganizacion.objects.filter(
                organizacion=organizacion, cargo=cargo, vigente=True).exclude(pk=self.instance.pk).exists():
            self.add_error('cargo', 'Esa organización ya tiene un dirigente vigente con ese cargo.')
        return datos


class HitoForm(DelegacionFijaMixin, forms.ModelForm):
    class Meta:
        model = Hito
        fields = ['nombre', 'descripcion', 'fecha', 'delegacion', 'territorio', 'responsable', 'estado']
        widgets = {'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
                   'descripcion': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, delegacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._fijar_delegacion(delegacion)
        responsables = Funcionario.objects.filter(activo=True)
        territorios = Territorio.objects.filter(activo=True)
        if delegacion is not None:
            responsables = responsables.filter(delegacion=delegacion)
            territorios = territorios.filter(delegacion=delegacion)
        self.fields['responsable'].queryset = responsables.order_by('nombre')
        self.fields['territorio'].queryset = territorios
        _estilo(self)

    def clean_nombre(self):
        return validar_texto_minimo(self.cleaned_data.get('nombre'), minimo=4, campo='nombre del hito')

    def clean(self):
        datos = super().clean()
        delegacion = self.delegacion_elegida()
        responsable, territorio = datos.get('responsable'), datos.get('territorio')
        if delegacion and responsable and responsable.delegacion_id != delegacion.pk:
            self.add_error('responsable', 'El responsable debe pertenecer a la delegación del hito.')
        if delegacion and territorio and territorio.delegacion_id != delegacion.pk:
            self.add_error('territorio', 'El territorio no pertenece a la delegación del hito.')
        self._aplicar_delegacion()
        return datos


class TipoAtencionForm(forms.ModelForm):
    class Meta:
        model = TipoAtencion
        fields = ['nombre', 'activo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilo(self)

    def clean_nombre(self):
        nombre = validar_texto_minimo(self.cleaned_data.get('nombre'), minimo=3, campo='tipo de atención')
        if TipoAtencion.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe ese tipo de atención.')
        return nombre


class SubtipoAtencionForm(forms.ModelForm):
    class Meta:
        model = SubtipoAtencion
        fields = ['tipo', 'nombre', 'activo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].queryset = TipoAtencion.objects.filter(activo=True)
        _estilo(self)

    def clean(self):
        datos = super().clean()
        nombre, tipo = datos.get('nombre'), datos.get('tipo')
        if nombre:
            datos['nombre'] = nombre = validar_texto_minimo(nombre, minimo=3, campo='subtipo')
        if tipo and nombre and SubtipoAtencion.objects.filter(tipo=tipo, nombre__iexact=nombre).exclude(
                pk=self.instance.pk).exists():
            self.add_error('nombre', 'Ese subtipo ya existe para este tipo de atención.')
        return datos
