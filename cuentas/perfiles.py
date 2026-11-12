"""
Rol y ámbito de cada usuario del SGR.

Retroalimentación del profesor Caiceo (revisión de la Evaluación 2):
cada actor debe ver y modificar SOLO la información de su función y de su
delegación (Guía SGR, "principio de acceso"):

- Funcionario: ve y registra solo SUS actividades y sube su evidencia.
- Delegado: ve el trabajo de los funcionarios de SU delegación, valida la
  evidencia, gestiona a sus funcionarios y les asigna metas.
- Coordinador: gestiona las delegaciones (crear, activar/desactivar),
  crea a los Delegados y los asigna a una delegación, y ve el cumplimiento
  de todas las delegaciones.
- Administrador: dominio sobre todo el sistema (configuración).
- Verificador: solo lectura de todo (auditoría).

Cada usuario que trabaja dentro de una delegación (Funcionario y Delegado)
tiene un registro en la tabla de funcionarios enlazado a su cuenta
(Funcionario.usuario). Ese enlace es lo que define su delegación.
"""
import secrets
import string

from django.contrib.auth.models import Group, User

ADMINISTRADOR = 'Administrador'
COORDINADOR = 'Coordinador'
DELEGADO = 'Delegado'
FUNCIONARIO = 'Funcionario'
VERIFICADOR = 'Verificador'
ORDEN_ROLES = [ADMINISTRADOR, COORDINADOR, DELEGADO, FUNCIONARIO, VERIFICADOR]


def rol_de(usuario):
    """Rol principal del usuario (el de mayor jerarquía si tuviera varios)."""
    if not getattr(usuario, 'is_authenticated', False):
        return None
    if usuario.is_superuser:
        return ADMINISTRADOR
    grupos = set(usuario.groups.values_list('name', flat=True))
    for rol in ORDEN_ROLES:
        if rol in grupos:
            return rol
    return None


def perfil_de(usuario):
    """Registro de funcionario enlazado a la cuenta (o None)."""
    if not getattr(usuario, 'is_authenticated', False):
        return None
    try:
        return usuario.funcionario
    except Exception:  # RelatedObjectDoesNotExist
        return None


def delegacion_de(usuario):
    perfil = perfil_de(usuario)
    return perfil.delegacion if perfil else None


def ve_todo(usuario):
    """Administrador, Coordinador y Verificador ven todas las delegaciones."""
    return rol_de(usuario) in (ADMINISTRADOR, COORDINADOR, VERIFICADOR)


# ------------------------------------------------------------------ ámbitos
def filtrar_actividades(usuario, consulta):
    rol = rol_de(usuario)
    if rol in (ADMINISTRADOR, COORDINADOR, VERIFICADOR):
        return consulta
    perfil = perfil_de(usuario)
    if perfil is None:
        return consulta.none()
    if rol == DELEGADO:
        return consulta.filter(delegacion_id=perfil.delegacion_id)
    if rol == FUNCIONARIO:
        return consulta.filter(funcionario_id=perfil.pk)
    return consulta.none()


def filtrar_funcionarios(usuario, consulta):
    rol = rol_de(usuario)
    if rol in (ADMINISTRADOR, COORDINADOR, VERIFICADOR):
        return consulta
    perfil = perfil_de(usuario)
    if rol == DELEGADO and perfil:
        # El equipo de la delegación: el propio Delegado y sus funcionarios.
        return consulta.filter(delegacion_id=perfil.delegacion_id, rol__in=(DELEGADO, FUNCIONARIO))
    if perfil:
        return consulta.filter(pk=perfil.pk)
    return consulta.none()


def filtrar_metas(usuario, consulta):
    rol = rol_de(usuario)
    if rol in (ADMINISTRADOR, COORDINADOR, VERIFICADOR):
        return consulta
    perfil = perfil_de(usuario)
    if rol == DELEGADO and perfil:
        return consulta.filter(funcionario__delegacion_id=perfil.delegacion_id)
    if perfil:
        return consulta.filter(funcionario_id=perfil.pk)
    return consulta.none()


def es_delegado_de(usuario, delegacion_id):
    perfil = perfil_de(usuario)
    return (rol_de(usuario) == DELEGADO and perfil is not None
            and perfil.activo and perfil.delegacion_id == delegacion_id)


# ----------------------------------------------------------------- cuentas
def generar_clave(largo=10):
    """Contraseña temporal: letras, números y un símbolo (cumple los
    validadores de contraseña de Django)."""
    letras = string.ascii_letters + string.digits
    while True:
        clave = ''.join(secrets.choice(letras) for _ in range(largo - 1)) + secrets.choice('.-_#')
        if any(c.isdigit() for c in clave) and any(c.isupper() for c in clave) and any(c.islower() for c in clave):
            return clave


def _nombre_usuario_libre(base):
    base = ''.join(c for c in base.lower() if c.isalnum() or c in '._-')[:30] or 'usuario'
    nombre, n = base, 1
    while User.objects.filter(username__iexact=nombre).exists():
        n += 1
        nombre = f'{base}{n}'
    return nombre


def sincronizar_cuenta(funcionario, clave=None):
    """Crea (si no existe) o actualiza la cuenta de acceso de un funcionario:
    grupo según su rol, estado activo y nombre. Devuelve (usuario, clave)
    donde clave es la contraseña temporal SOLO si la cuenta es nueva o si se
    pidió una nueva; en otro caso es None."""
    usuario = funcionario.usuario
    clave_generada = None
    if usuario is None:
        usuario = User(username=_nombre_usuario_libre(funcionario.email.split('@')[0]))
        clave_generada = clave or generar_clave()
        usuario.set_password(clave_generada)
    elif clave:
        usuario.set_password(clave)
        clave_generada = clave
    partes = funcionario.nombre.split(' ', 1)
    usuario.first_name = partes[0][:150]
    usuario.last_name = (partes[1] if len(partes) > 1 else '')[:150]
    usuario.email = funcionario.email
    usuario.is_active = funcionario.activo
    usuario.save()
    grupo = Group.objects.filter(name=funcionario.rol).first()
    if grupo:
        usuario.groups.set([grupo])
    if funcionario.usuario_id != usuario.pk:
        funcionario.usuario = usuario
        funcionario.save(update_fields=['usuario'])
    return usuario, clave_generada
