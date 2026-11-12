"""Consulta de la auditoría (HU-30): solo lectura, con filtros."""
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.utils.dateparse import parse_date

from .models import RegistroAuditoria


@permission_required('comun.view_registroauditoria', raise_exception=True)
def auditoria(request):
    registros = RegistroAuditoria.objects.select_related('usuario')
    filtros = {}
    accion = request.GET.get('accion', '')
    if accion in RegistroAuditoria.Accion.values:
        registros = registros.filter(accion=accion)
        filtros['accion'] = accion
    entidad = request.GET.get('entidad', '')
    if entidad:
        registros = registros.filter(entidad=entidad)
        filtros['entidad'] = entidad
    usuario = request.GET.get('usuario', '').strip()
    if usuario:
        registros = registros.filter(usuario_texto__icontains=usuario)
        filtros['usuario'] = usuario
    for campo, condicion in (('desde', 'fecha__date__gte'), ('hasta', 'fecha__date__lte')):
        fecha = parse_date(request.GET.get(campo, '') or '')
        if fecha:
            registros = registros.filter(**{condicion: fecha})
            filtros[campo] = fecha.isoformat()
    texto = request.GET.get('q', '').strip()
    if texto:
        registros = registros.filter(Q(objeto__icontains=texto) | Q(detalle__icontains=texto)
                                     | Q(objeto_id=texto))
        filtros['q'] = texto
    pagina = Paginator(registros, 50).get_page(request.GET.get('pagina'))
    parametros = request.GET.copy()
    parametros.pop('pagina', None)
    return render(request, 'comun/auditoria.html', {
        'titulo_pagina': 'Auditoría',
        'pagina': pagina,
        'filtros': filtros,
        'acciones': RegistroAuditoria.Accion.values,
        'entidades': RegistroAuditoria.objects.exclude(entidad='').values_list('entidad', flat=True)
        .distinct().order_by('entidad'),
        'parametros': parametros.urlencode(),
    })
