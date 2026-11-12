"""
Actividad reciente (RF-030) y alertas operativas (RF-037, HU-31) de los
paneles. Cada alerta indica motivo, responsable, fecha y enlace al elemento.
"""
from dataclasses import dataclass

from django.utils.formats import number_format as _nf

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from organizacion.models import Periodo

from .indicadores import periodo_vigente
from .models import Actividad, Compromiso


def periodo_elegido(request):
    """Período pedido en la URL (?periodo=) o el vigente (RF-008: consultar
    períodos anteriores)."""
    valor = request.GET.get('periodo', '')
    if valor.isdigit():
        periodo = Periodo.objects.filter(pk=int(valor)).first()
        if periodo:
            return periodo
    return periodo_vigente()


@dataclass
class Alerta:
    nivel: str          # 'rojo' o 'ambar'
    motivo: str
    responsable: str
    fecha: object
    enlace: str
    texto_enlace: str = 'Ver'


@dataclass
class ActividadReciente:
    ultimo_ingreso: object
    dias_sin_ingreso: object
    registros: int
    promedio_diario: float

    @property
    def inactivo(self):
        limite = getattr(settings, 'SGR_DIAS_SIN_REGISTRO', 5)
        return self.dias_sin_ingreso is None or self.dias_sin_ingreso > limite


def actividad_reciente(funcionario, periodo=None, hoy=None):
    """Fecha del último ingreso, días sin ingreso, cantidad de registros y
    promedio diario en el período (RF-030)."""
    hoy = hoy or timezone.localdate()
    actividades = Actividad.objects.filter(funcionario=funcionario)
    ultimo = actividades.order_by('-fecha_registro').values_list('fecha_registro', flat=True).first()
    ultimo_dia = timezone.localtime(ultimo).date() if ultimo else None
    registros, dias = 0, 0
    if periodo is not None:
        registros = actividades.filter(fecha__range=(periodo.fecha_inicio, periodo.fecha_fin)).count()
        dias = max(min((hoy - periodo.fecha_inicio).days + 1, (periodo.fecha_fin - periodo.fecha_inicio).days + 1), 1)
    return ActividadReciente(
        ultimo_ingreso=ultimo_dia,
        dias_sin_ingreso=(hoy - ultimo_dia).days if ultimo_dia else None,
        registros=registros,
        promedio_diario=round(registros / dias, 2) if dias else 0.0,
    )


def _alertas_compromisos(compromisos):
    alertas = []
    for c in compromisos.exclude(estado=Compromiso.Estado.REALIZADO).select_related('responsable'):
        if c.vencido or c.proximo_a_vencer:
            alertas.append(Alerta(
                'rojo' if c.vencido else 'ambar',
                f'Compromiso {c.codigo} {c.situacion[1].lower()}: {c.descripcion[:60]}',
                c.responsable.nombre, c.fecha_compromiso, c.get_absolute_url(), 'Ver compromiso'))
    return alertas


def alertas_funcionario(perfil, resultado):
    alertas = _alertas_compromisos(Compromiso.objects.filter(responsable=perfil))
    for a in Actividad.objects.filter(funcionario=perfil, estado_validacion=Actividad.EstadoValidacion.RECHAZADA):
        alertas.append(Alerta('rojo', f'Actividad {a.codigo} rechazada: {a.observacion_validacion[:60]}',
                              perfil.nombre, a.fecha, reverse('gestion:detalle', args=[a.pk]), 'Corregir'))
    reciente = actividad_reciente(perfil)
    if reciente.inactivo:
        dias = 'nunca' if reciente.dias_sin_ingreso is None else f'hace {reciente.dias_sin_ingreso} días'
        alertas.append(Alerta('ambar', f'Su último ingreso fue {dias}. Recuerde registrar a diario.',
                              perfil.nombre, reciente.ultimo_ingreso, reverse('gestion:crear'), 'Registrar'))
    if resultado.tiene_metas and resultado.color == 'rojo':
        alertas.append(Alerta('ambar', f'Avance bajo el umbral: {_nf(resultado.cumplimiento, 1)} % '
                                       f'de {_nf(resultado.esperado, 1)} % esperado.',
                              perfil.nombre, timezone.localdate(), reverse('delegaciones:inicio'), 'Ver metas'))
    return sorted(alertas, key=lambda a: a.nivel != 'rojo')


def alertas_delegacion(delegacion, detalle):
    alertas = _alertas_compromisos(Compromiso.objects.filter(delegacion=delegacion))
    pendientes = (Actividad.objects.filter(delegacion=delegacion, evidencias__isnull=False)
                  .exclude(estado_validacion=Actividad.EstadoValidacion.VALIDADA).distinct().count())
    if pendientes:
        alertas.append(Alerta('ambar', f'{pendientes} evidencia{"s" if pendientes != 1 else ""} esperando su validación.',
                              'Delegado', timezone.localdate(),
                              reverse('gestion:listado') + '?validacion=Pendiente', 'Validar'))
    for r in detalle:
        reciente = actividad_reciente(r.funcionario)
        if reciente.inactivo:
            dias = ('nunca ha registrado' if reciente.dias_sin_ingreso is None
                    else f'sin registros hace {reciente.dias_sin_ingreso} días')
            alertas.append(Alerta('ambar', f'{r.funcionario.nombre}: {dias}.', r.funcionario.nombre,
                                  reciente.ultimo_ingreso,
                                  reverse('organizacion:funcionario_detalle', args=[r.funcionario.pk]), 'Ver ficha'))
        if r.tiene_metas and r.color == 'rojo':
            alertas.append(Alerta('rojo',
                                  f'{r.funcionario.nombre} bajo el umbral: {_nf(r.cumplimiento, 1)} % '
                                  f'de {_nf(r.esperado, 1)} % esperado.',
                                  r.funcionario.nombre, timezone.localdate(),
                                  reverse('organizacion:funcionario_detalle', args=[r.funcionario.pk]), 'Ver ficha'))
    return sorted(alertas, key=lambda a: a.nivel != 'rojo')


def alertas_coordinacion(filas):
    alertas = []
    umbral = getattr(settings, 'SGR_UMBRAL_COLECTIVO', 80)
    hoy = timezone.localdate()
    vencidos = (Compromiso.objects.exclude(estado=Compromiso.Estado.REALIZADO)
                .filter(fecha_compromiso__lt=hoy).values('delegacion__nombre').order_by())
    por_delegacion = {}
    for fila in vencidos:
        por_delegacion[fila['delegacion__nombre']] = por_delegacion.get(fila['delegacion__nombre'], 0) + 1
    for nombre, cantidad in sorted(por_delegacion.items()):
        plural = 's' if cantidad != 1 else ''
        alertas.append(Alerta('rojo', f'{nombre}: {cantidad} compromiso{plural} vencido{plural} sin realizar.',
                              f'Delegado de {nombre}', hoy, reverse('gestion:agenda') + '?situacion=vencidos', 'Ver agenda'))
    for f in filas:
        if f['delegacion'].activa and f['color'] == 'rojo':
            alertas.append(Alerta('ambar', f'{f["delegacion"]}: cumplimiento {_nf(f["porcentaje"], 1)} %, bajo lo esperado.',
                                  f'Delegado de {f["delegacion"]}', hoy, f['delegacion'].get_absolute_url(), 'Ver delegación'))
    return alertas, umbral
