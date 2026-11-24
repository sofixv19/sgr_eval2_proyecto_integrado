"""v3.0 (Guía PI Ev. 3): dashboard con filtros y gráficos.

Muestra avance, cumplimiento y semáforo por funcionario y por delegación,
estado de los compromisos del Tubo, carga de trabajo y tendencia semanal.
Cada rol ve su ámbito: el Funcionario lo suyo, el Delegado su delegación y
el Coordinador, el Administrador y el Verificador todas.
"""
import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.db.models.functions import TruncWeek
from django.shortcuts import render
from django.utils.dateparse import parse_date

from cuentas.perfiles import (
    DELEGADO, FUNCIONARIO, filtrar_actividades, filtrar_compromisos, perfil_de, rol_de, ve_todo,
)
from delegaciones.models import Delegacion
from organizacion.models import Funcionario, Periodo

from .alertas import periodo_elegido
from .indicadores import cumplimiento_delegacion, cumplimiento_funcionario, porcentaje_esperado
from .models import Actividad, Compromiso

COLORES = {'verde': '#2B7A66', 'ambar': '#E0A93E', 'rojo': '#B42318', 'gris': '#9C8F94'}


@login_required
def dashboard(request):
    usuario = request.user
    rol, perfil = rol_de(usuario), perfil_de(usuario)
    periodo = periodo_elegido(request)
    filtros = {}

    # ----------------------------------------------------------- ámbito y filtros
    delegaciones = Delegacion.objects.filter(activa=True)
    if not ve_todo(usuario):
        delegaciones = delegaciones.filter(pk=perfil.delegacion_id) if perfil else delegaciones.none()
    valor = request.GET.get('delegacion', '')
    if valor.isdigit() and delegaciones.filter(pk=int(valor)).exists():
        delegaciones = delegaciones.filter(pk=int(valor))
        filtros['delegacion'] = valor

    funcionarios = Funcionario.objects.filter(activo=True, rol='Funcionario', delegacion__in=delegaciones)
    if rol == FUNCIONARIO and perfil:
        funcionarios = funcionarios.filter(pk=perfil.pk)
    valor = request.GET.get('funcionario', '')
    if valor.isdigit() and funcionarios.filter(pk=int(valor)).exists():
        funcionarios = funcionarios.filter(pk=int(valor))
        filtros['funcionario'] = valor
    funcionarios = list(funcionarios.select_related('cargo', 'delegacion').order_by('nombre'))

    desde = parse_date(request.GET.get('desde', '') or '') or (periodo.fecha_inicio if periodo else None)
    hasta = parse_date(request.GET.get('hasta', '') or '') or (periodo.fecha_fin if periodo else None)
    if request.GET.get('desde'):
        filtros['desde'] = desde.isoformat()
    if request.GET.get('hasta'):
        filtros['hasta'] = hasta.isoformat()

    registros = filtrar_actividades(usuario, Actividad.objects.all()).filter(
        delegacion__in=delegaciones, funcionario__in=funcionarios)
    if desde:
        registros = registros.filter(fecha__gte=desde)
    if hasta:
        registros = registros.filter(fecha__lte=hasta)
    estado = request.GET.get('validacion', '')
    if estado in Actividad.EstadoValidacion.values:
        registros = registros.filter(estado_validacion=estado)
        filtros['validacion'] = estado

    # --------------------------------------------------------------- cálculos
    resultados = [cumplimiento_funcionario(f, periodo) for f in funcionarios]
    por_funcionario = {
        'etiquetas': [r.funcionario.nombre for r in resultados],
        'valores': [r.cumplimiento for r in resultados],
        'colores': [COLORES.get(r.color, COLORES['gris']) for r in resultados],
        'esperado': porcentaje_esperado(periodo) if periodo else 0,
    }
    por_delegacion = {'etiquetas': [], 'valores': [], 'colores': []}
    if rol not in (FUNCIONARIO, DELEGADO):
        for d in delegaciones:
            porcentaje, color, _ = cumplimiento_delegacion(d, periodo)
            por_delegacion['etiquetas'].append(d.nombre)
            por_delegacion['valores'].append(porcentaje)
            por_delegacion['colores'].append(COLORES.get(color, COLORES['gris']))

    carga = list(registros.values('funcionario__nombre').annotate(
        actividades=Count('id', filter=Q(clase=Actividad.Clase.ACTIVIDAD)),
        sociales=Count('id', filter=Q(clase=Actividad.Clase.SOCIAL)),
    ).order_by('funcionario__nombre'))
    validacion = {e.label: registros.filter(estado_validacion=e.value).count() for e in Actividad.EstadoValidacion}

    semanas = list(registros.filter(estado_validacion=Actividad.EstadoValidacion.VALIDADA)
                   .annotate(semana=TruncWeek('fecha')).values('semana').annotate(total=Count('id')).order_by('semana'))
    todas = list(registros.annotate(semana=TruncWeek('fecha')).values('semana').annotate(total=Count('id'))
                 .order_by('semana'))
    etiquetas_semana = sorted({_fecha(s['semana']) for s in todas})
    aprobadas = {_fecha(s['semana']): s['total'] for s in semanas}
    ingresadas = {_fecha(s['semana']): s['total'] for s in todas}
    tendencia = {
        'etiquetas': [f'Sem. {d:%d/%m}' for d in etiquetas_semana],
        'ingresados': [ingresadas.get(d, 0) for d in etiquetas_semana],
        'aprobados': [aprobadas.get(d, 0) for d in etiquetas_semana],
    }

    compromisos = filtrar_compromisos(usuario, Compromiso.objects.filter(delegacion__in=delegaciones))
    if rol == FUNCIONARIO and perfil:
        compromisos = compromisos.filter(responsable=perfil)
    estados_compromiso = {e.label: compromisos.filter(estado=e.value).count() for e in Compromiso.Estado}
    vencidos = sum(1 for c in compromisos.exclude(estado=Compromiso.Estado.REALIZADO) if c.vencido)

    graficos = {
        'por_funcionario': por_funcionario, 'por_delegacion': por_delegacion,
        'carga': {'etiquetas': [c['funcionario__nombre'] for c in carga],
                  'actividades': [c['actividades'] for c in carga], 'sociales': [c['sociales'] for c in carga]},
        'validacion': {'etiquetas': list(validacion), 'valores': list(validacion.values())},
        'compromisos': {'etiquetas': list(estados_compromiso), 'valores': list(estados_compromiso.values())},
        'tendencia': tendencia,
    }
    total = registros.count()
    aprobados = validacion.get(Actividad.EstadoValidacion.VALIDADA.label, 0)
    contexto = {
        'titulo_pagina': 'Dashboard',
        'periodo': periodo, 'periodos': Periodo.objects.all(),
        'filtros': filtros, 'desde': desde, 'hasta': hasta,
        'opciones_delegacion': Delegacion.objects.filter(activa=True) if ve_todo(usuario) else None,
        'opciones_funcionario': (Funcionario.objects.filter(activo=True, rol='Funcionario',
                                                            delegacion__in=delegaciones).order_by('nombre')
                                 if rol != FUNCIONARIO else None),
        'estados_validacion': Actividad.EstadoValidacion.choices,
        'resultados': resultados,
        'indicadores': {
            'registros': total, 'aprobados': aprobados,
            'pct_aprobados': round(aprobados * 100 / total, 1) if total else 0,
            'compromisos_abiertos': compromisos.exclude(estado=Compromiso.Estado.REALIZADO).count(),
            'vencidos': vencidos,
        },
        'graficos': graficos,
    }
    return render(request, 'gestion/dashboard.html', contexto)


def _fecha(valor):
    return valor.date() if isinstance(valor, datetime.datetime) else valor
