"""
Lógica de autenticación del SGR, separada de las vistas para poder probarla
como unidad (plan de pruebas unitarias, casos CP-LOGIN-001 a CP-LOGIN-010).

validar_credenciales() recibe el usuario y la contraseña escritos en el
formulario de inicio de sesión y devuelve un ResultadoLogin con:
- ok: True solo si las credenciales son válidas y la cuenta está activa;
- usuario: el objeto User autenticado (o None);
- codigo: motivo interno del resultado (sirve para las pruebas y el registro);
- mensaje: texto que se muestra al usuario.

Por seguridad, el usuario inexistente y la contraseña incorrecta muestran el
MISMO mensaje, para no revelar qué nombres de usuario existen.
"""
import logging
import re
from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.cache import cache

logger = logging.getLogger('sgr.seguridad')

PATRON_USUARIO = re.compile(r'^[\w.@+-]{3,150}$')
MENSAJE_INVALIDAS = 'Usuario o contraseña incorrectos.'

# Códigos de resultado
OK = 'ok'
USUARIO_VACIO = 'usuario_vacio'
CONTRASENA_VACIA = 'contrasena_vacia'
AMBOS_VACIOS = 'ambos_vacios'
FORMATO_INVALIDO = 'formato_invalido'
CREDENCIALES_INVALIDAS = 'credenciales_invalidas'
USUARIO_INACTIVO = 'usuario_inactivo'
BLOQUEADO = 'bloqueado'


@dataclass
class ResultadoLogin:
    ok: bool
    codigo: str
    mensaje: str
    usuario: object = None


def _max_intentos():
    return getattr(settings, 'SGR_LOGIN_MAX_INTENTOS', 5)


def _minutos_bloqueo():
    return getattr(settings, 'SGR_LOGIN_MINUTOS_BLOQUEO', 15)


def _clave_intentos(usuario):
    return f'sgr-login-intentos:{usuario.lower()}'


def esta_bloqueado(usuario):
    """True si el usuario superó el máximo de intentos fallidos."""
    return cache.get(_clave_intentos(usuario), 0) >= _max_intentos()


def registrar_intento_fallido(usuario):
    clave = _clave_intentos(usuario)
    intentos = cache.get(clave, 0) + 1
    cache.set(clave, intentos, timeout=_minutos_bloqueo() * 60)
    return intentos


def limpiar_intentos(usuario):
    cache.delete(_clave_intentos(usuario))


def validar_credenciales(usuario, contrasena, request=None):
    """Valida los datos del formulario de login. Ver docstring del módulo."""
    usuario = (usuario or '').strip()
    contrasena = contrasena or ''

    # 1) Campos obligatorios
    if not usuario and not contrasena:
        return ResultadoLogin(False, AMBOS_VACIOS, 'Debe ingresar su usuario y su contraseña.')
    if not usuario:
        return ResultadoLogin(False, USUARIO_VACIO, 'El usuario es obligatorio.')
    if not contrasena:
        return ResultadoLogin(False, CONTRASENA_VACIA, 'La contraseña es obligatoria.')

    # 2) Formato del nombre de usuario (evita entradas con espacios, símbolos
    #    o largo fuera de rango antes de consultar la base de datos)
    if not PATRON_USUARIO.match(usuario) or len(contrasena) > 128:
        return ResultadoLogin(
            False, FORMATO_INVALIDO,
            'Formato inválido: el usuario debe tener entre 3 y 150 caracteres '
            '(letras, números y . @ + - _).',
        )

    # 3) Bloqueo temporal por intentos fallidos
    if esta_bloqueado(usuario):
        logger.warning('Intento de acceso a cuenta bloqueada: %s', usuario)
        return ResultadoLogin(
            False, BLOQUEADO,
            f'Cuenta bloqueada temporalmente por demasiados intentos fallidos. '
            f'Intente nuevamente en {_minutos_bloqueo()} minutos.',
        )

    # 4) Autenticación contra la base de datos (contraseña con hash PBKDF2)
    user = authenticate(request, username=usuario, password=contrasena)
    if user is not None:
        limpiar_intentos(usuario)
        return ResultadoLogin(True, OK, 'Inicio de sesión correcto.', user)

    # 5) authenticate() devuelve None también para cuentas inactivas: se
    #    distingue solo si la contraseña es correcta, para no dar pistas.
    modelo = get_user_model()
    existente = modelo.objects.filter(username__iexact=usuario).first()
    if existente is not None and not existente.is_active and existente.check_password(contrasena):
        logger.warning('Intento de acceso con cuenta inactiva: %s', usuario)
        return ResultadoLogin(
            False, USUARIO_INACTIVO,
            'Su cuenta está desactivada. Contacte al Administrador del sistema.',
        )

    intentos = registrar_intento_fallido(usuario)
    logger.warning('Credenciales inválidas para %s (intento %s)', usuario, intentos)
    return ResultadoLogin(False, CREDENCIALES_INVALIDAS, MENSAJE_INVALIDAS)
