"""
Vistas de la app 'delegaciones' (Aplicación 1).

Evaluación Sumativa 2: todas las vistas obtienen la información mediante
consultas Django ORM contra la base de datos (antes se leía desde
data/delegaciones.json).
"""
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from gestion.models import Actividad
from gestion.services import grados_donut, resumen_por_estado

from .models import Delegacion


def _actividades_por_delegacion():
    """Cuenta cuántas actividades tiene cada delegación (para el gráfico de
    barras de la portada), mediante una consulta ORM agregada."""
    filas = (
        Actividad.objects.values('delegacion__nombre')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')
    )
    if not filas:
        return []

    maximo = max(fila['cantidad'] for fila in filas)
    return [
        {
            'nombre': fila['delegacion__nombre'],
            'cantidad': fila['cantidad'],
            'porcentaje': round(fila['cantidad'] / maximo * 100),
        }
        for fila in filas
    ]


def inicio(request):
    """Página de inicio / presentación de la Aplicación 1."""

    total = Delegacion.objects.count()

    if total > 0:
        mensaje_resumen = f'Actualmente hay {total} delegaciones registradas.'
    else:
        mensaje_resumen = 'Aún no hay delegaciones registradas.'

    conteo_estado, total_actividades = resumen_por_estado()

    contexto = {
        'titulo_pagina': 'Delegaciones Municipales - La Serena',
        'total_delegaciones': total,
        'mensaje_resumen': mensaje_resumen,
        'actividades_por_delegacion': _actividades_por_delegacion(),
        'conteo_estado': conteo_estado,
        'total_actividades': total_actividades,
        'donut_grados': grados_donut(conteo_estado, total_actividades),
    }
    return render(request, 'delegaciones/inicio.html', contexto)


def listado(request):
    """Listado de delegaciones, con búsqueda opcional por texto (?q=)."""

    query = request.GET.get('q', '').strip()
    delegaciones = Delegacion.objects.all()

    if query:
        delegaciones = delegaciones.filter(
            Q(nombre__icontains=query)
            | Q(encargado__icontains=query)
            | Q(territorio__icontains=query)
        )

    contexto = {
        'titulo_pagina': 'Listado de Delegaciones',
        'delegaciones': delegaciones,
        'query': query,
    }
    return render(request, 'delegaciones/listado.html', contexto)


def detalle(request, slug):
    """Ficha de detalle de una delegación específica, buscada por su slug."""

    delegacion = get_object_or_404(Delegacion, slug=slug)

    contexto = {
        'titulo_pagina': delegacion.nombre,
        'delegacion': delegacion,
    }
    return render(request, 'delegaciones/detalle.html', contexto)


# ---------------------------------------------------------------------------
# Marcadores de posición para las operaciones CRUD desde la interfaz.
#
# La Evaluación 2 solo exige que los botones "Agregar / Modificar / Eliminar"
# existan visualmente y enlacen a una ruta real; la implementación funcional
# (formularios que efectivamente creen/editen/borren registros) es el
# alcance de la Evaluación Sumativa 3. Por ahora, estas vistas muestran una
# pantalla informativa reutilizable (templates/en_construccion.html).
# ---------------------------------------------------------------------------

def crear(request):
    contexto = {
        'titulo_pagina': 'Agregar delegación',
        'accion': 'Agregar delegación',
        'volver_url': reverse('delegaciones:listado'),
    }
    return render(request, 'en_construccion.html', contexto)


def editar(request, slug):
    delegacion = get_object_or_404(Delegacion, slug=slug)
    contexto = {
        'titulo_pagina': f'Editar {delegacion.nombre}',
        'accion': f'Modificar delegación: {delegacion.nombre}',
        'volver_url': reverse('delegaciones:detalle', args=[delegacion.slug]),
    }
    return render(request, 'en_construccion.html', contexto)


def eliminar(request, slug):
    delegacion = get_object_or_404(Delegacion, slug=slug)
    contexto = {
        'titulo_pagina': f'Eliminar {delegacion.nombre}',
        'accion': f'Eliminar delegación: {delegacion.nombre}',
        'volver_url': reverse('delegaciones:detalle', args=[delegacion.slug]),
    }
    return render(request, 'en_construccion.html', contexto)
