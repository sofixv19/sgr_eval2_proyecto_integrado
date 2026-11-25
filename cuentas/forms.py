from django import forms

from .servicios import validar_credenciales


class LoginForm(forms.Form):
    """Formulario de inicio de sesión. La validación completa se delega a
    servicios.validar_credenciales() para que la misma regla se pruebe de
    forma unitaria."""

    usuario = forms.CharField(
        label='Usuario o correo', max_length=150, required=False,
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


# ------------------------------------------------------------------ v3.0
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm  # noqa: E402


def _estilo(form):
    for campo in form.fields.values():
        campo.widget.attrs.setdefault('class', 'form-control')
    return form


class CambiarClaveForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = 'Contraseña actual (o temporal)'
        self.fields['new_password1'].label = 'Nueva contraseña'
        self.fields['new_password2'].label = 'Repita la nueva contraseña'
        _estilo(self)


class RecuperarClaveForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = 'Correo institucional'
        _estilo(self)


class RestablecerClaveForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].label = 'Nueva contraseña'
        self.fields['new_password2'].label = 'Repita la nueva contraseña'
        _estilo(self)
