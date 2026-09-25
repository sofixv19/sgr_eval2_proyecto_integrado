"""
Vistas de la app 'gestion' (Aplicación 2).

Evaluación Sumativa 2: todas las vistas obtienen la información mediante
consultas Django ORM (antes se leía desde data/actividades.json).
"""
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Actividad, Categoria
from .services import grados_donut, resumen_por_estado


def listado(request):
    """Actividades registradas, con filtro por estado (?estado=) y búsqueda
    de texto (?q=), ambos resueltos con consultas ORM."""

    actividades = Actividad.objects.select_related('delegacion', 'categoria').all()

    estado_seleccionado = request.GET.get('estado')
    if estado_seleccionado in Actividad.Estado.values:
        actividades = actividades.filter(estado=estado_seleccionado)

    query = request.GET.get('q', '').strip()
    if query:
        actividades = actividades.filter(
            Q(codigo__icontains=query)
            | Q(descripcion__icontains=query)
            | Q(delegacion__nombre__icontains=query)
            | Q(categoria__nombre__icontains=query)
        )

    contexto = {
        'titulo_pagina': 'Actividades registradas',
        'actividades': actividades,
        'estados': Actividad.Estado.values,
        'estado_seleccionado': estado_seleccionado,
        'query': query,
        'total': actividades.count(),
    }
    return render(request, 'gestion/listado.html', contexto)


def detalle(request, actividad_id):
    """Ficha de detalle de una actividad específica."""

    actividad = get_object_or_404(
        Actividad.objects.select_related('delegacion', 'categoria'),
        pk=actividad_id,
    )

    contexto = {
        'titulo_pagina': f'Actividad {actividad.codigo}',
        'actividad': actividad,
    }
    return render(request, 'gestion/detalle.html', contexto)


def resumen(request):
    """Vista tipo 'semáforo': totaliza actividades por estado."""

    conteo, total = resumen_por_estado()

    if total > 0:
        porcentaje_realizado = round((conteo['realizado'] / total) * 100, 1)
    else:
        porcentaje_realizado = 0

    contexto = {
        'titulo_pagina': 'Resumen de gestión',
        'conteo': conteo,
        'total': total,
        'porcentaje_realizado': porcentaje_realizado,
        'donut_grados': grados_donut(conteo, total),
    }
    return render(request, 'gestion/resumen.html', contexto)


# ---------------------------------------------------------------------------
# Marcadores de posición para las operaciones CRUD desde la interfaz.
# Ver la nota equivalente en delegaciones/views.py: la implementación
# funcional de estos botones corresponde a la Evaluación Sumativa 3.
# ---------------------------------------------------------------------------

def crear(request):
    contexto = {
        'titulo_pagina': 'Agregar actividad',
        'accion': 'Agregar actividad',
        'volver_url': reverse('gestion:listado'),
    }
    return render(request, 'en_construccion.html', contexto)


def editar(request, actividad_id):
    actividad = get_object_or_404(Actividad, pk=actividad_id)
    contexto = {
        'titulo_pagina': f'Editar {actividad.codigo}',
        'accion': f'Modificar actividad: {actividad.codigo}',
        'volver_url': reverse('gestion:detalle', args=[actividad.pk]),
    }
    return render(request, 'en_construccion.html', contexto)


def eliminar(request, actividad_id):
    actividad = get_object_or_404(Actividad, pk=actividad_id)
    contexto = {
        'titulo_pagina': f'Eliminar {actividad.codigo}',
        'accion': f'Eliminar actividad: {actividad.codigo}',
        'volver_url': reverse('gestion:detalle', args=[actividad.pk]),
    }
    return render(request, 'en_construccion.html', contexto)
