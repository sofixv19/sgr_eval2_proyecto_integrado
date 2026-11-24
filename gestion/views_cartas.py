"""v3.0 (Guía PI Ev. 3): Tubo de cartas de la delegación.

- Todos los funcionarios de la delegación ven el Tubo de cartas.
- Cada funcionario modifica solo sus propios registros (los que registró o
  tiene a cargo) mientras no estén aprobados o finalizados.
- Solo el Delegado aprueba o finaliza una carta.
"""
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from cuentas.perfiles import ADMINISTRADOR, DELEGADO, filtrar_por_delegacion, perfil_de, rol_de, ve_todo
from delegaciones.models import Delegacion
from organizacion.models import Funcionario

from .forms import CartaForm
from .models import Carta


def _es_jefe(usuario, carta):
    perfil = perfil_de(usuario)
    if rol_de(usuario) == ADMINISTRADOR:
        return True
    return rol_de(usuario) == DELEGADO and perfil is not None and perfil.delegacion_id == carta.delegacion_id


def puede_modificar_carta(usuario, carta):
    if not usuario.has_perm('gestion.change_carta'):
        return False
    if _es_jefe(usuario, carta):
        return carta.estado != Carta.Estado.FINALIZADA
    perfil = perfil_de(usuario)
    propia = perfil is not None and perfil.pk in (carta.registrada_por_id, carta.encargado_id)
    return propia and not carta.cerrada


@permission_required('gestion.view_carta', raise_exception=True)
def cartas(request):
    consulta = filtrar_por_delegacion(request.user, Carta.objects.select_related('encargado', 'delegacion'))
    filtros = {}
    valor = request.GET.get('estado', '')
    if valor in Carta.Estado.values:
        consulta, filtros['estado'] = consulta.filter(estado=valor), valor
    valor = request.GET.get('encargado', '')
    if valor.isdigit():
        consulta, filtros['encargado'] = consulta.filter(encargado_id=int(valor)), valor
    for campo, condicion in (('desde', 'fecha_ingreso__gte'), ('hasta', 'fecha_ingreso__lte')):
        fecha = parse_date(request.GET.get(campo, '') or '')
        if fecha:
            consulta = consulta.filter(**{condicion: fecha})
            filtros[campo] = fecha.isoformat()
    texto = request.GET.get('q', '').strip()
    if texto:
        consulta = consulta.filter(Q(codigo__icontains=texto) | Q(remite__icontains=texto)
                                   | Q(rut_remite__icontains=texto) | Q(tema__icontains=texto))
        filtros['q'] = texto
    lista = list(consulta)
    for carta in lista:
        carta.modificable = puede_modificar_carta(request.user, carta)
    base = filtrar_por_delegacion(request.user, Carta.objects.all())
    return render(request, 'gestion/cartas.html', {
        'titulo_pagina': 'Tubo de cartas',
        'cartas': lista,
        'filtros': filtros,
        'estados': Carta.Estado.choices,
        'encargados': Funcionario.objects.filter(pk__in=base.values('encargado_id')).order_by('nombre'),
        'puede_crear': request.user.has_perm('gestion.add_carta') and (
            perfil_de(request.user) is not None or rol_de(request.user) == ADMINISTRADOR),
        'muestra_delegacion': ve_todo(request.user),
    })


def _formulario(request, carta=None):
    perfil = perfil_de(request.user)
    delegacion = perfil.delegacion if perfil else (carta.delegacion if carta else None)
    es_jefe = carta is None and rol_de(request.user) in (DELEGADO, ADMINISTRADOR) or (
        carta is not None and _es_jefe(request.user, carta))
    kwargs = {'delegacion': delegacion, 'puede_cerrar': es_jefe}
    if request.method == 'POST':
        form = CartaForm(request.POST, instance=carta, **kwargs)
        if form.is_valid():
            nueva = form.save(commit=False)
            if carta is None:
                nueva.registrada_por = perfil
            nueva.save()
            messages.success(request, f'Carta {nueva.codigo} {"registrada" if carta is None else "actualizada"}.')
            return redirect('gestion:cartas')
    else:
        inicial = {'encargado': perfil.pk} if (carta is None and perfil) else None
        form = CartaForm(instance=carta, initial=inicial, **kwargs)
    titulo = 'Registrar carta' if carta is None else f'Modificar carta {carta.codigo}'
    return render(request, 'comun/mantenedor_form.html', {
        'titulo_pagina': titulo, 'accion': titulo, 'form': form, 'volver_url': '/gestion/cartas/',
        'ayuda': 'Solo el Delegado puede dejar una carta Aprobada o Finalizada. Una carta cerrada ya no se modifica.',
    })


@permission_required('gestion.add_carta', raise_exception=True)
def carta_crear(request):
    if perfil_de(request.user) is None and rol_de(request.user) != ADMINISTRADOR:
        raise PermissionDenied('Su cuenta no está asociada a una delegación.')
    return _formulario(request)


@permission_required('gestion.change_carta', raise_exception=True)
def carta_editar(request, pk):
    carta = get_object_or_404(filtrar_por_delegacion(request.user, Carta.objects.all()), pk=pk)
    if not puede_modificar_carta(request.user, carta):
        raise PermissionDenied('Solo puede modificar sus propias cartas, y solo mientras no estén aprobadas o finalizadas.')
    return _formulario(request, carta)


@permission_required('gestion.delete_carta', raise_exception=True)
def carta_eliminar(request, pk):
    carta = get_object_or_404(filtrar_por_delegacion(request.user, Carta.objects.all()), pk=pk)
    if not _es_jefe(request.user, carta) or carta.cerrada:
        raise PermissionDenied('Solo el Delegado elimina cartas que aún no están cerradas.')
    if request.method == 'POST':
        codigo = carta.codigo
        carta.delete()
        messages.success(request, f'Carta {codigo} eliminada.')
        return redirect('gestion:cartas')
    return render(request, 'confirmar_eliminar.html', {
        'titulo_pagina': 'Eliminar carta', 'accion': f'Eliminar carta {carta.codigo}', 'objeto': carta,
        'volver_url': '/gestion/cartas/',
    })


__all__ = ['cartas', 'carta_crear', 'carta_editar', 'carta_eliminar', 'Delegacion']
