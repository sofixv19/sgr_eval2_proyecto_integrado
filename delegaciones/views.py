"""
Vistas de la app 'delegaciones' (Aplicación 1).

Evaluación Sumativa 2: todas las vistas obtienen la información mediante
consultas Django ORM contra la base de datos (antes se leía desde
data/delegaciones.json).
"""
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Count, ProtectedError, Q, RestrictedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from gestion.models import Actividad
from gestion.services import grados_donut, resumen_por_estado

from .forms import DelegacionForm
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
# CRUD real de Delegación (Evaluación Sumativa N.º 3): formularios ModelForm
# que efectivamente crean, modifican y eliminan registros en la base de
# datos, con mensajes de confirmación (django.contrib.messages).
# ---------------------------------------------------------------------------

@permission_required('delegaciones.add_delegacion', raise_exception=True)
def crear(request):
    if request.method == 'POST':
        form = DelegacionForm(request.POST)
        if form.is_valid():
            delegacion = form.save()
            messages.success(request, f'Delegación "{delegacion.nombre}" creada correctamente.')
            return redirect('delegaciones:detalle', slug=delegacion.slug)
    else:
        form = DelegacionForm()

    contexto = {
        'titulo_pagina': 'Agregar delegación',
        'accion': 'Agregar delegación',
        'form': form,
        'volver_url': reverse('delegaciones:listado'),
    }
    return render(request, 'delegaciones/form.html', contexto)


@permission_required('delegaciones.change_delegacion', raise_exception=True)
def editar(request, slug):
    delegacion = get_object_or_404(Delegacion, slug=slug)

    if request.method == 'POST':
        form = DelegacionForm(request.POST, instance=delegacion)
        if form.is_valid():
            delegacion = form.save()
            messages.success(request, f'Delegación "{delegacion.nombre}" actualizada correctamente.')
            return redirect('delegaciones:detalle', slug=delegacion.slug)
    else:
        form = DelegacionForm(instance=delegacion)

    contexto = {
        'titulo_pagina': f'Editar {delegacion.nombre}',
        'accion': f'Modificar delegación: {delegacion.nombre}',
        'form': form,
        'volver_url': reverse('delegaciones:detalle', args=[delegacion.slug]),
    }
    return render(request, 'delegaciones/form.html', contexto)


@permission_required('delegaciones.delete_delegacion', raise_exception=True)
def eliminar(request, slug):
    delegacion = get_object_or_404(Delegacion, slug=slug)

    if request.method == 'POST':
        nombre = delegacion.nombre
        try:
            delegacion.delete()
        except (ProtectedError, RestrictedError):
            # Funcionario.delegacion usa on_delete=RESTRICT: no se puede
            # borrar una delegación que todavía tiene funcionarios.
            messages.error(
                request,
                f'No se puede eliminar la delegación "{nombre}" porque tiene funcionarios '
                'asignados. Primero reasígnelos a otra delegación.',
            )
            return redirect('delegaciones:detalle', slug=delegacion.slug)
        messages.success(request, f'Delegación "{nombre}" eliminada correctamente.')
        return redirect('delegaciones:listado')

    contexto = {
        'titulo_pagina': f'Eliminar {delegacion.nombre}',
        'accion': f'Eliminar delegación: {delegacion.nombre}',
        'objeto': delegacion,
        'advertencia': (
            f'Esto eliminará también las {delegacion.total_actividades} actividad(es) '
            'asociadas a esta delegación (relación en cascada).'
        ) if delegacion.total_actividades else '',
        'volver_url': reverse('delegaciones:detalle', args=[delegacion.slug]),
    }
    return render(request, 'confirmar_eliminar.html', contexto)
