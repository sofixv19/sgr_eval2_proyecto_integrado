from django import forms

from .servicios import validar_credenciales


class LoginForm(forms.Form):
    """Formulario de inicio de sesión. La validación completa se delega a
    servicios.validar_credenciales() para que la misma regla se pruebe de
    forma unitaria."""

    usuario = forms.CharField(
        label='Usuario', max_length=150, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'username', 'autofocus': True}),
    )
    contrasena = forms.CharField(
        label='Contraseña', max_length=128, required=False, strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}),
    )

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self.resultado = None
        super().__init__(*args, **kwargs)

    def clean(self):
        datos = super().clean()
        self.resultado = validar_credenciales(datos.get('usuario'), datos.get('contrasena'), self.request)
        if not self.resultado.ok:
            raise forms.ValidationError(self.resultado.mensaje, code=self.resultado.codigo)
        return datos

    def get_user(self):
        return self.resultado.usuario if self.resultado else None
