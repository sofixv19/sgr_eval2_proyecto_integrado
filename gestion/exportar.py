"""
Exportación de informes (RF-033, HU-20).

Cada informe se descarga como CSV que Excel abre directamente (UTF-8 con BOM
y separador ";"). Respeta el ámbito del usuario y los mismos filtros de la
pantalla, e incluye el título, la fecha de generación y los filtros aplicados.
"""
import csv

from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.utils import timezone

from cuentas.perfiles import filtrar_actividades, filtrar_compromisos, filtrar_funcionarios
from organizacion.models import Funcionario, Periodo

from .indicadores import cumplimiento_funcionario, periodo_vigente
from .models import Actividad, Compromiso


def _respuesta_csv(nombre, titulo, usuario, filtros):
    respuesta = HttpResponse(content_type='text/csv; charset=utf-8')
    fecha = timezone.localtime()
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre}_{fecha:%Y%m%d_%H%M}.csv"'
    respuesta.write('﻿')  # BOM: Excel reconoce los tildes
    escritor = csv.writer(respuesta, delimiter=';')
    escritor.writerow([titulo])
    escritor.writerow(['Generado el', fecha.strftime('%d/%m/%Y %H:%M'), 'por', usuario.get_username()])
    escritor.writerow(['Filtros aplicados', '; '.join(f'{k}={v}' for k, v in filtros.items()) or 'ninguno'])
    escritor.writerow([])
    return respuesta, escritor


@permission_required('gestion.view_actividad', raise_exception=True)
def exportar_actividades(request):
    from .views import filtrar_listado_actividades
    actividades, filtros = filtrar_listado_actividades(
        request, filtrar_actividades(request.user, Actividad.objects.select_related(
            'delegacion', 'categoria', 'funcionario', 'validado_por', 'organizacion')))
    respuesta, escritor = _respuesta_csv('actividades', 'SGR La Serena - Actividades registradas', request.user, filtros)
    escritor.writerow(['Código', 'Fecha', 'Delegación', 'Funcionario', 'Ítem/categoría', 'Tipo de gestión',
                       'Acción realizada', 'Solicitante', 'Organización', 'Contacto', 'Teléfono', 'Estado',
                       'Validación', 'Validado por', 'Suma puntaje', 'Motivo', 'Versión de reglas'])
    for a in actividades:
        escritor.writerow([
            a.codigo, a.fecha.strftime('%d/%m/%Y'), a.delegacion.nombre, a.funcionario.nombre, a.categoria.nombre,
            a.get_tipo_gestion_display(), a.descripcion, a.get_tipo_solicitante_display(),
            a.organizacion.nombre if a.organizacion else '', a.contacto, a.telefono_contacto, a.estado,
            a.get_estado_validacion_display(), a.validado_por.nombre if a.validado_por else '',
            'Sí' if a.puntuable else 'No', a.motivo_sin_puntaje, a.version_reglas,
        ])
    return respuesta


@permission_required('gestion.view_compromiso', raise_exception=True)
def exportar_agenda(request):
    from .views_agenda import filtrar_agenda
    compromisos, filtros = filtrar_agenda(
        request, filtrar_compromisos(request.user, Compromiso.objects.select_related('responsable', 'delegacion')))
    respuesta, escritor = _respuesta_csv('agenda_colectiva', 'SGR La Serena - Agenda colectiva', request.user, filtros)
    escritor.writerow(['Código', 'Delegación', 'Origen', 'Solicitante', 'Territorio', 'Compromiso', 'Responsable',
                       'Área de apoyo', 'Fecha solicitud', 'Fecha comprometida', 'Estado', 'Situación',
                       'Fecha de cierre', 'Último avance'])
    for c in compromisos:
        escritor.writerow([
            c.codigo, c.delegacion.nombre, c.origen, c.solicitante, c.territorio, c.descripcion, c.responsable.nombre,
            c.area_apoyo, c.fecha_solicitud.strftime('%d/%m/%Y'), c.fecha_compromiso.strftime('%d/%m/%Y'),
            c.estado, c.situacion[1], c.fecha_cierre.strftime('%d/%m/%Y') if c.fecha_cierre else '', c.observacion,
        ])
    return respuesta


@login_required
def exportar_cumplimiento(request):
    """Informe de desempeño (HU-07/HU-20): meta, avance, fórmula, ponderación y
    resultado de cada funcionario del ámbito, en el período elegido."""
    periodo = None
    if request.GET.get('periodo', '').isdigit():
        periodo = Periodo.objects.filter(pk=int(request.GET['periodo'])).first()
    periodo = periodo or periodo_vigente()
    funcionarios = filtrar_funcionarios(request.user, Funcionario.objects.filter(rol='Funcionario')
                                        .select_related('delegacion', 'cargo')).order_by('delegacion__nombre', 'nombre')
    filtros = {'periodo': str(periodo) if periodo else 'sin período'}
    respuesta, escritor = _respuesta_csv('cumplimiento', 'SGR La Serena - Cumplimiento por funcionario',
                                         request.user, filtros)
    escritor.writerow(['Delegación', 'Funcionario', 'Cargo', 'Ítem', 'Meta', 'Avance validado',
                       'Cumplimiento % (avance/meta x 100, tope 120)', 'Ponderador %', 'Resultado ponderado',
                       'Felicitaciones', 'Reclamos', 'Cumplimiento total %', 'Esperado al día %', 'Semáforo'])
    for funcionario in funcionarios:
        resultado = cumplimiento_funcionario(funcionario, periodo)
        for fila in resultado.filas:
            escritor.writerow([funcionario.delegacion.nombre, funcionario.nombre, funcionario.cargo.nombre_cargo,
                               fila.meta.item_medible, fila.meta.valor_objetivo, fila.avance,
                               str(fila.cumplimiento).replace('.', ','), fila.meta.ponderador,
                               str(fila.ponderado).replace('.', ','), '', '', '', '', ''])
        escritor.writerow([funcionario.delegacion.nombre, funcionario.nombre, funcionario.cargo.nombre_cargo,
                           'TOTAL', '', '', '', '', str(resultado.base).replace('.', ','),
                           resultado.felicitaciones, resultado.reclamos,
                           str(resultado.cumplimiento).replace('.', ','),
                           str(resultado.esperado).replace('.', ','), resultado.color])
    return respuesta
