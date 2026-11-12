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
from django.views.decorators.http import require_POST

from cuentas.perfiles import (
    ADMINISTRADOR, COORDINADOR, DELEGADO, FUNCIONARIO, VERIFICADOR, perfil_de, rol_de,
)
from gestion.indicadores import (
    MENSAJES_SEMAFORO, cumplimiento_delegacion, cumplimiento_funcionario, periodo_vigente, porcentaje_esperado,
    semaforo,
)
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
    """Portada distinta según el rol (retroalimentación Eval 2: "el template
    es el mismo para el delegado y el funcionario, no veo la diferencia")."""
    rol = rol_de(request.user)
    perfil = perfil_de(request.user)
    if rol == FUNCIONARIO and perfil:
        return panel_funcionario(request, perfil)
    if rol == DELEGADO and perfil:
        return panel_delegado(request, perfil)
    if rol in (COORDINADOR, ADMINISTRADOR, VERIFICADOR):
        return panel_coordinador(request)
    return portada_general(request)


def panel_funcionario(request, perfil):
    actividades = Actividad.objects.filter(funcionario=perfil).select_related('categoria')
    contexto = {
        'titulo_pagina': 'Mi panel',
        'perfil': perfil,
        'resultado': cumplimiento_funcionario(perfil),
        'periodo': periodo_vigente(),
        'recientes': actividades.order_by('-fecha', '-fecha_registro')[:6],
        'rechazadas': actividades.filter(estado_validacion=Actividad.EstadoValidacion.RECHAZADA),
        'sin_evidencia': actividades.filter(evidencias__isnull=True)
        .exclude(estado_validacion=Actividad.EstadoValidacion.VALIDADA).count(),
        'total': actividades.count(),
        'validadas': actividades.filter(estado_validacion=Actividad.EstadoValidacion.VALIDADA).count(),
        'pendientes': actividades.filter(estado_validacion=Actividad.EstadoValidacion.PENDIENTE).count(),
    }
    return render(request, 'delegaciones/panel_funcionario.html', contexto)


def panel_delegado(request, perfil):
    delegacion = perfil.delegacion
    actividades = Actividad.objects.filter(delegacion=delegacion).select_related('funcionario', 'categoria')
    por_validar = (actividades.exclude(estado_validacion=Actividad.EstadoValidacion.VALIDADA)
                   .filter(evidencias__isnull=False).distinct())
    porcentaje, color, detalle = cumplimiento_delegacion(delegacion)
    contexto = {
        'titulo_pagina': f'Panel de {delegacion}',
        'perfil': perfil,
        'delegacion': delegacion,
        'periodo': periodo_vigente(),
        'por_validar': por_validar[:10],
        'total_por_validar': por_validar.count(),
        'porcentaje': porcentaje,
        'color': color,
        'barra': min(porcentaje, 100),
        'mensaje': MENSAJES_SEMAFORO.get(color, ''),
        'esperado': porcentaje_esperado(periodo_vigente()),
        'detalle': detalle,
        'total_actividades': actividades.count(),
    }
    return render(request, 'delegaciones/panel_delegado.html', contexto)


def panel_coordinador(request):
    """El Coordinador gestiona las delegaciones y ve su cumplimiento: "me
    acabo de meter y usted lleva un 20 % de cumplimiento, ¿qué pasa?"."""
    periodo = periodo_vigente()
    filas = []
    for delegacion in Delegacion.objects.all():
        porcentaje, color, detalle = cumplimiento_delegacion(delegacion, periodo)
        filas.append({
            'delegacion': delegacion,
            'delegado': delegacion.delegado,
            'porcentaje': porcentaje,
            'color': color,
            'barra': min(porcentaje, 100),
            'funcionarios': len(detalle),
            'actividades': delegacion.actividades.count(),
            'pendientes': delegacion.actividades.exclude(estado_validacion=Actividad.EstadoValidacion.VALIDADA).count(),
        })
    contexto = {
        'titulo_pagina': 'Panel de coordinación',
        'periodo': periodo,
        'esperado': porcentaje_esperado(periodo),
        'filas': filas,
        'sin_delegado': [f['delegacion'] for f in filas if f['delegado'] is None and f['delegacion'].activa],
        'total_activas': sum(1 for f in filas if f['delegacion'].activa),
        'total_por_validar': sum(f['pendientes'] for f in filas),
        'total_actividades': sum(f['actividades'] for f in filas),
    }
    con_metas = [f['porcentaje'] for f in filas if f['color'] != 'gris' and f['delegacion'].activa]
    contexto['promedio'] = round(sum(con_metas) / len(con_metas), 1) if con_metas else 0.0
    contexto['color_promedio'] = semaforo(contexto['promedio'], contexto['esperado']) if con_metas else 'gris'
    contexto['barra_promedio'] = min(contexto['promedio'], 100)
    contexto['mensaje_promedio'] = MENSAJES_SEMAFORO[contexto['color_promedio']]
    return render(request, 'delegaciones/panel_coordinador.html', contexto)


def portada_general(request):
    """Portada informativa (usuarios sin rol asignado)."""

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


def _delegaciones_visibles(usuario):
    if rol_de(usuario) == DELEGADO:
        perfil = perfil_de(usuario)
        return Delegacion.objects.filter(pk=perfil.delegacion_id) if perfil else Delegacion.objects.none()
    return Delegacion.objects.all()


@permission_required('delegaciones.view_delegacion', raise_exception=True)
def listado(request):
    """Listado de delegaciones, con búsqueda opcional por texto (?q=)."""

    query = request.GET.get('q', '').strip()
    delegaciones = _delegaciones_visibles(request.user)

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


@permission_required('delegaciones.view_delegacion', raise_exception=True)
def detalle(request, slug):
    """Ficha de una delegación con su Delegado, funcionarios y cumplimiento."""

    delegacion = get_object_or_404(_delegaciones_visibles(request.user), slug=slug)
    porcentaje, color, detalle_funcionarios = cumplimiento_delegacion(delegacion)

    contexto = {
        'titulo_pagina': delegacion.nombre,
        'delegacion': delegacion,
        'delegado': delegacion.delegado,
        'porcentaje': porcentaje,
        'color': color,
        'detalle_funcionarios': detalle_funcionarios,
        'puede_asignar_delegado': (request.user.has_perm('organizacion.add_funcionario')
                                   and rol_de(request.user) in (COORDINADOR, ADMINISTRADOR)),
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


@require_POST
@permission_required('delegaciones.change_delegacion', raise_exception=True)
def cambiar_estado(request, slug):
    """El Coordinador activa o desactiva una delegación (RF-001)."""
    delegacion = get_object_or_404(Delegacion, slug=slug)
    delegacion.activa = not delegacion.activa
    delegacion.save(update_fields=['activa'])
    estado = 'activada' if delegacion.activa else 'desactivada'
    messages.success(request, f'Delegación "{delegacion.nombre}" {estado}.')
    return redirect(request.POST.get('volver') or reverse('delegaciones:detalle', args=[delegacion.slug]))
