"""
Vistas de la app 'gestion' (Aplicación 2).

Evaluación Sumativa 2: todas las vistas obtienen la información mediante
consultas Django ORM (antes se leía desde data/actividades.json).
"""
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from comun.vistas import MantenedorCrear, MantenedorEditar, MantenedorEliminar, MantenedorListado

from .forms import ActividadForm, CategoriaForm, ValidacionForm
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
    """Ficha de detalle de una actividad específica. Si todavía no está
    validada, muestra además el formulario de validación (solo lo puede
    completar un Delegado; la regla la aplica ValidacionForm/Actividad.clean())."""

    actividad = get_object_or_404(
        Actividad.objects.select_related('delegacion', 'categoria', 'funcionario', 'validado_por'),
        pk=actividad_id,
    )

    validacion_form = None
    if not actividad.validado and request.user.has_perm('gestion.change_actividad'):
        if request.method == 'POST' and 'validar' in request.POST:
            validacion_form = ValidacionForm(request.POST, instance=actividad)
            if validacion_form.is_valid():
                validacion_form.save()
                messages.success(request, f'Actividad {actividad.codigo} validada correctamente.')
                return redirect('gestion:detalle', actividad_id=actividad.id)
        else:
            validacion_form = ValidacionForm(instance=actividad)

    contexto = {
        'titulo_pagina': f'Actividad {actividad.codigo}',
        'actividad': actividad,
        'validacion_form': validacion_form,
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
# CRUD real de Actividad (Evaluación Sumativa N.º 3): formularios ModelForm
# que efectivamente crean, modifican y eliminan registros en la base de
# datos, con mensajes de confirmación (django.contrib.messages).
# ---------------------------------------------------------------------------

@permission_required('gestion.add_actividad', raise_exception=True)
def crear(request):
    if request.method == 'POST':
        form = ActividadForm(request.POST)
        if form.is_valid():
            actividad = form.save()
            messages.success(request, f'Actividad "{actividad.codigo}" registrada correctamente.')
            return redirect('gestion:detalle', actividad_id=actividad.id)
    else:
        form = ActividadForm()

    contexto = {
        'titulo_pagina': 'Agregar actividad',
        'accion': 'Agregar actividad',
        'form': form,
        'volver_url': reverse('gestion:listado'),
    }
    return render(request, 'gestion/form.html', contexto)


@permission_required('gestion.change_actividad', raise_exception=True)
def editar(request, actividad_id):
    actividad = get_object_or_404(Actividad, pk=actividad_id)

    if request.method == 'POST':
        form = ActividadForm(request.POST, instance=actividad)
        if form.is_valid():
            actividad = form.save()
            messages.success(request, f'Actividad "{actividad.codigo}" actualizada correctamente.')
            return redirect('gestion:detalle', actividad_id=actividad.id)
    else:
        form = ActividadForm(instance=actividad)

    contexto = {
        'titulo_pagina': f'Editar {actividad.codigo}',
        'accion': f'Modificar actividad: {actividad.codigo}',
        'form': form,
        'volver_url': reverse('gestion:detalle', args=[actividad.pk]),
    }
    return render(request, 'gestion/form.html', contexto)


@permission_required('gestion.delete_actividad', raise_exception=True)
def eliminar(request, actividad_id):
    actividad = get_object_or_404(Actividad, pk=actividad_id)

    if request.method == 'POST':
        codigo = actividad.codigo
        actividad.delete()
        messages.success(request, f'Actividad "{codigo}" eliminada correctamente.')
        return redirect('gestion:listado')

    contexto = {
        'titulo_pagina': f'Eliminar {actividad.codigo}',
        'accion': f'Eliminar actividad: {actividad.codigo}',
        'objeto': actividad,
        'advertencia': '',
        'volver_url': reverse('gestion:detalle', args=[actividad.pk]),
    }
    return render(request, 'confirmar_eliminar.html', contexto)


# ---------------------------------------------------------------------------
# Mantenedor de la tabla maestra Categoría (vistas genéricas de comun/vistas.py)
# ---------------------------------------------------------------------------

class CategoriaConfig:
    model = Categoria
    form_class = CategoriaForm
    nombre_singular = 'categoría'
    nombre_plural = 'categorías de actividad'
    url_listado = 'gestion:categorias'


class CategoriaListado(CategoriaConfig, MantenedorListado):
    campos_busqueda = ('nombre', 'descripcion')
    columnas = (('Categoría', 'nombre'), ('Descripción', 'descripcion'), ('N.º de actividades', 'total_actividades'))
    url_crear, url_editar, url_eliminar = 'gestion:categoria_crear', 'gestion:categoria_editar', 'gestion:categoria_eliminar'

    def get_queryset(self):
        return super().get_queryset().annotate(total_actividades=Count('actividades'))


class CategoriaCrear(CategoriaConfig, MantenedorCrear):
    pass


class CategoriaEditar(CategoriaConfig, MantenedorEditar):
    pass


class CategoriaEliminar(CategoriaConfig, MantenedorEliminar):
    advertencia = 'Si la categoría está usada por alguna actividad no se podrá eliminar.'
