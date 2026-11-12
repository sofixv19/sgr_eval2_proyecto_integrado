"""
Registro automático de la auditoría (RF-036).

- Un middleware guarda la petición en curso (usuario e IP).
- Señales pre_save/post_save/post_delete comparan el registro antes y después
  de guardarlo y anotan solo los campos que cambiaron.
- Se registran también los inicios de sesión (correctos y fallidos) y los
  accesos denegados (403), como pide HU-26.
"""
import threading

from django.apps import apps
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.core.exceptions import PermissionDenied
from django.db.models.signals import post_delete, post_save, pre_save

_local = threading.local()

# Tablas auditadas (app, modelo). Se excluye el propio historial de auditoría
# y CambioCompromiso, que ya es un historial.
MODELOS_AUDITADOS = [
    ('delegaciones', 'Delegacion'), ('delegaciones', 'OrganizacionComunitaria'),
    ('organizacion', 'CargoFuncion'), ('organizacion', 'Funcionario'), ('organizacion', 'Periodo'),
    ('organizacion', 'MetaProyecto'), ('organizacion', 'Reconocimiento'), ('organizacion', 'Ausencia'),
    ('gestion', 'Categoria'), ('gestion', 'Actividad'), ('gestion', 'Evidencia'), ('gestion', 'Compromiso'),
]
CAMPOS_IGNORADOS = {'creado', 'fecha_registro', 'fecha_carga', 'puntuable', 'motivo_sin_puntaje'}


def peticion_actual():
    return getattr(_local, 'peticion', None)


class AuditoriaMiddleware:
    """Deja disponible la petición en curso para las señales y registra los
    accesos denegados."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.peticion = request
        try:
            return self.get_response(request)
        finally:
            _local.peticion = None

    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied):
            registrar('Acceso denegado', detalle=f'{request.method} {request.path}'[:255])
        return None


def _ip(request):
    if request is None:
        return None
    reenviada = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return (reenviada.split(',')[0].strip() or request.META.get('REMOTE_ADDR')) or None


def registrar(accion, instancia=None, cambios=None, detalle='', usuario=None):
    from .models import RegistroAuditoria
    request = peticion_actual()
    if usuario is None and request is not None and getattr(request, 'user', None) is not None:
        usuario = request.user if request.user.is_authenticated else None
    datos = {
        'accion': accion, 'cambios': cambios or {}, 'detalle': detalle[:255], 'ip': _ip(request),
        'usuario': usuario, 'usuario_texto': usuario.get_username() if usuario else 'sistema',
    }
    if instancia is not None:
        datos.update({'entidad': str(instancia._meta.verbose_name).capitalize(), 'objeto_id': str(instancia.pk),
                      'objeto': str(instancia)[:200]})
    try:
        RegistroAuditoria.objects.create(**datos)
    except Exception:  # la auditoría nunca debe impedir la operación principal
        pass


def _valor(instancia, campo):
    if campo.is_relation:
        relacionado = getattr(instancia, campo.name, None)
        return str(relacionado) if relacionado is not None else ''
    valor = campo.value_from_object(instancia)
    if campo.choices:
        return str(dict(campo.flatchoices).get(valor, valor))
    if hasattr(valor, 'name'):        # archivos
        return valor.name or ''
    return '' if valor is None else str(valor)


def _foto(instancia):
    """Valores legibles del registro, con el nombre de cada campo tal como lo
    ve el usuario (por ejemplo, "Fecha comprometida")."""
    return {str(c.verbose_name).capitalize(): _valor(instancia, c) for c in instancia._meta.concrete_fields
            if c.name not in CAMPOS_IGNORADOS and not c.primary_key}


def _antes_de_guardar(sender, instance, raw=False, **kwargs):
    if raw or not instance.pk:
        instance._auditoria_antes = None
        return
    anterior = sender.objects.filter(pk=instance.pk).first()
    instance._auditoria_antes = _foto(anterior) if anterior else None


def _despues_de_guardar(sender, instance, created, raw=False, **kwargs):
    if raw:
        return
    despues = _foto(instance)
    antes = getattr(instance, '_auditoria_antes', None)
    if created or antes is None:
        cambios = {campo: ['', valor] for campo, valor in despues.items() if valor not in ('', 'None')}
        registrar('Alta', instance, cambios)
        return
    cambios = {campo: [antes.get(campo, ''), valor] for campo, valor in despues.items()
               if antes.get(campo, '') != valor}
    if not cambios:
        return
    accion = 'Modificación'
    clave_validacion = 'Estado de validación'
    if sender.__name__ == 'Actividad' and clave_validacion in cambios:
        accion = {'Validada': 'Validación', 'Rechazada': 'Rechazo'}.get(instance.estado_validacion, accion)
    registrar(accion, instance, cambios)


def _despues_de_eliminar(sender, instance, **kwargs):
    registrar('Eliminación', instance, {c: [v, ''] for c, v in _foto(instance).items() if v})


def _inicio_sesion(sender, request, user, **kwargs):
    registrar('Inicio de sesión', usuario=user, detalle='Sesión iniciada')


def _inicio_fallido(sender, credentials, request=None, **kwargs):
    registrar('Acceso fallido', detalle=f'Usuario ingresado: {credentials.get("username", "")}'[:255])


def conectar_senales():
    for app_label, modelo in MODELOS_AUDITADOS:
        clase = apps.get_model(app_label, modelo)
        uid = f'auditoria_{app_label}_{modelo}'
        pre_save.connect(_antes_de_guardar, sender=clase, dispatch_uid=f'{uid}_pre')
        post_save.connect(_despues_de_guardar, sender=clase, dispatch_uid=f'{uid}_post')
        post_delete.connect(_despues_de_eliminar, sender=clase, dispatch_uid=f'{uid}_del')
    user_logged_in.connect(_inicio_sesion, dispatch_uid='auditoria_login')
    user_login_failed.connect(_inicio_fallido, dispatch_uid='auditoria_login_fallido')
