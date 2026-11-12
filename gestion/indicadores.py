"""
Cálculo de avance, cumplimiento y semáforo (Guía SGR, sección 13.1).

- Solo una actividad con validación APROBADA aporta al avance (CA-01, CA-02).
- cumplimiento (%) = avance aprobado / meta del período x 100.
- resultado ponderado = ponderador x cumplimiento / 100.
- meta esperada al día = días transcurridos / días del período x 100.
- semáforo: verde si cumplimiento >= esperado; ámbar si >= 60 % del
  esperado; rojo si es menor.

Versión 2.0 (Nuevos requerimientos, octubre 2026):
- Además de validada, la actividad debe ser "puntuable" (Actividad.puntuable):
  no suman las gestiones previas, las solicitadas por el propio Delegado ni
  las que no tienen nombre y teléfono del usuario (reglas 1, 2 y 5).
- Tope por ítem de 120 % (SGR_TOPE_ITEM, regla 7).
- Felicitaciones (+10 c/u, máx. 3) y reclamos (−20 c/u) registrados por el
  Delegado; el total del colaborador queda entre 0 y 150 % (SGR_TOPE_CUMPLIMIENTO).
- Las ausencias (licencias, vacaciones, días administrativos o libres) se
  descuentan de los días del período para calcular la meta esperada (regla 9).
"""
from dataclasses import dataclass, field

from django.conf import settings
from django.utils import timezone

from organizacion.models import Ausencia, MetaProyecto, Periodo, Reconocimiento

from .models import Actividad


def periodo_vigente():
    """Período Abierto; si no hay, el más reciente."""
    return (Periodo.objects.filter(estado=Periodo.Estado.ABIERTO).first()
            or Periodo.objects.order_by('-fecha_inicio').first())


def porcentaje_esperado(periodo, hoy=None):
    if periodo is None:
        return 0.0
    hoy = hoy or timezone.localdate()
    total = (periodo.fecha_fin - periodo.fecha_inicio).days + 1
    transcurridos = min(max((hoy - periodo.fecha_inicio).days + 1, 0), total)
    return round(transcurridos / total * 100, 1) if total > 0 else 0.0


def dias_ausencia(funcionario, inicio, fin):
    """Días de ausencia registrados para el funcionario dentro de [inicio, fin]."""
    if fin < inicio:
        return 0
    ausencias = Ausencia.objects.filter(funcionario=funcionario, desde__lte=fin, hasta__gte=inicio)
    dias = set()
    for ausencia in ausencias:
        desde, hasta = max(ausencia.desde, inicio), min(ausencia.hasta, fin)
        dias.update(desde.toordinal() + i for i in range((hasta - desde).days + 1))
    return len(dias)


def porcentaje_esperado_funcionario(funcionario, periodo, hoy=None):
    """Meta esperada al día descontando las ausencias del funcionario (regla 9):
    (días transcurridos − ausencias hasta hoy) / (días del período − ausencias del período)."""
    if periodo is None:
        return 0.0
    hoy = hoy or timezone.localdate()
    total = (periodo.fecha_fin - periodo.fecha_inicio).days + 1
    transcurridos = min(max((hoy - periodo.fecha_inicio).days + 1, 0), total)
    ausente_total = dias_ausencia(funcionario, periodo.fecha_inicio, periodo.fecha_fin)
    ausente_hasta_hoy = dias_ausencia(funcionario, periodo.fecha_inicio, min(hoy, periodo.fecha_fin))
    disponibles = total - ausente_total
    if disponibles <= 0:
        return 0.0
    return round(min(max((transcurridos - ausente_hasta_hoy) / disponibles * 100, 0.0), 100.0), 1)


MENSAJES_SEMAFORO = {
    'verde': 'Va al día con sus metas',
    'ambar': 'Algo atrasado respecto a lo esperado',
    'rojo': 'Bajo lo esperado a la fecha',
    'gris': 'Sin metas en el período',
}


def semaforo(cumplimiento, esperado):
    if esperado <= 0 or cumplimiento >= esperado:
        return 'verde'
    if cumplimiento >= esperado * 0.6:
        return 'ambar'
    return 'rojo'


@dataclass
class FilaMeta:
    meta: MetaProyecto
    avance: int
    cumplimiento: float
    ponderado: float
    color: str = 'gris'

    @property
    def barra(self):
        """Ancho de la barra de avance (0 a 100 %)."""
        return min(self.cumplimiento, 100)


@dataclass
class ResultadoFuncionario:
    funcionario: object
    filas: list = field(default_factory=list)
    cumplimiento: float = 0.0
    esperado: float = 0.0
    color: str = 'verde'
    # Versión 2.0
    base: float = 0.0               # cumplimiento ponderado antes de felicitaciones y reclamos
    felicitaciones: int = 0
    reclamos: int = 0
    ajuste: float = 0.0             # puntos sumados o restados por felicitaciones y reclamos
    dias_ausencia: int = 0

    @property
    def tiene_ajuste(self):
        return bool(self.felicitaciones or self.reclamos)

    @property
    def puntos_felicitaciones(self):
        return (min(self.felicitaciones, getattr(settings, 'SGR_MAX_FELICITACIONES', 3))
                * getattr(settings, 'SGR_PUNTOS_FELICITACION', 10))

    @property
    def puntos_reclamos(self):
        return self.reclamos * getattr(settings, 'SGR_PUNTOS_RECLAMO', 20)

    @property
    def tiene_metas(self):
        return bool(self.filas)

    @property
    def barra(self):
        return min(self.cumplimiento, 100)

    @property
    def mensaje(self):
        return MENSAJES_SEMAFORO.get(self.color, MENSAJES_SEMAFORO['gris'])


def cumplimiento_funcionario(funcionario, periodo=None, hoy=None):
    periodo = periodo or periodo_vigente()
    resultado = ResultadoFuncionario(funcionario=funcionario,
                                     esperado=porcentaje_esperado_funcionario(funcionario, periodo, hoy))
    if periodo is None:
        return resultado
    resultado.dias_ausencia = dias_ausencia(funcionario, periodo.fecha_inicio, periodo.fecha_fin)
    tope_item = getattr(settings, 'SGR_TOPE_ITEM', 120)
    tope_total = getattr(settings, 'SGR_TOPE_CUMPLIMIENTO', 150)
    metas = (MetaProyecto.objects.filter(funcionario=funcionario, periodo=periodo)
             .select_related('categoria').order_by('item_medible'))
    total_ponderado, total_ponderadores = 0.0, 0
    for meta in metas:
        avance = 0
        if meta.categoria_id:
            avance = Actividad.objects.filter(
                funcionario=funcionario, categoria_id=meta.categoria_id,
                estado_validacion=Actividad.EstadoValidacion.VALIDADA, puntuable=True,
                fecha__range=(periodo.fecha_inicio, periodo.fecha_fin),
            ).count()
        objetivo = meta.valor_numerico
        cumplimiento = min(avance / objetivo * 100, tope_item) if objetivo > 0 else 0.0
        ponderado = meta.ponderador * cumplimiento / 100
        resultado.filas.append(FilaMeta(meta, avance, round(cumplimiento, 1), round(ponderado, 1),
                                        semaforo(cumplimiento, resultado.esperado)))
        total_ponderado += ponderado
        total_ponderadores += meta.ponderador
    if total_ponderadores:
        # Si los ponderadores aún no suman 100, se normaliza sobre lo asignado.
        resultado.base = round(total_ponderado * 100 / total_ponderadores, 1)
    reconocimientos = Reconocimiento.objects.filter(funcionario=funcionario, periodo=periodo)
    resultado.felicitaciones = reconocimientos.filter(tipo=Reconocimiento.Tipo.FELICITACION).count()
    resultado.reclamos = reconocimientos.filter(tipo=Reconocimiento.Tipo.RECLAMO).count()
    resultado.ajuste = resultado.puntos_felicitaciones - resultado.puntos_reclamos
    if resultado.tiene_metas or resultado.tiene_ajuste:
        resultado.cumplimiento = round(min(max(resultado.base + resultado.ajuste, 0.0), tope_total), 1)
    resultado.color = semaforo(resultado.cumplimiento, resultado.esperado)
    return resultado


def cumplimiento_delegacion(delegacion, periodo=None, hoy=None):
    """Promedio del cumplimiento de los funcionarios operativos activos de la delegación
    que tienen metas en el período. Devuelve (porcentaje, color, detalle)."""
    periodo = periodo or periodo_vigente()
    detalle = [
        cumplimiento_funcionario(f, periodo, hoy)
        for f in delegacion.funcionarios.filter(activo=True, rol='Funcionario').select_related('cargo')
    ]
    con_metas = [r for r in detalle if r.tiene_metas]
    porcentaje = round(sum(r.cumplimiento for r in con_metas) / len(con_metas), 1) if con_metas else 0.0
    esperado = porcentaje_esperado(periodo, hoy)
    color = semaforo(porcentaje, esperado) if con_metas else 'gris'
    return porcentaje, color, detalle
