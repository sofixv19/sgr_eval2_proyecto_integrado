"""
Agenda colectiva o "tubo de trabajo" (Guía SGR 4.2; RF-016 a RF-021;
HU-12 a HU-15).

- Funcionario y Delegado ven la agenda de toda su delegación (es compartida
  por el equipo); Coordinador, Administrador y Verificador ven todas.
- Registra compromisos el equipo de la delegación (o el Administrador).
- Cambian el estado el responsable, el Delegado de la delegación o el
  Administrador; cada cambio queda en el historial.
- Reasigna y reabre solo el Delegado de la delegación o el Administrador.
"""
import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date

from cuentas.perfiles import ADMINISTRADOR, DELEGADO, filtrar_compromisos, perfil_de, rol_de, ve_todo
from delegaciones.models import Delegacion
from organizacion.models import Funcionario

from .forms import CambioEstadoCompromisoForm, CompromisoForm, ReasignarCompromisoForm
from .models import Compromiso

SITUACIONES = [
    ('abiertos', 'Abiertos (no realizados)'),
    ('vencidos', 'Vencidos'),
    ('proximos', 'Próximos a vencer'),
    ('realizados', 'Realizados'),
]


def _compromiso_visible(request, pk):
    return get_object_or_404(
        filtrar_compromisos(request.user, Compromiso.objects.select_related('responsable', 'delegacion')), pk=pk)


def _es_jefe(usuario, compromiso):
    """Delegado de la delegación del compromiso, o Administrador."""
    rol = rol_de(usuario)
    if rol == ADMINISTRADOR:
        return True
    perfil = perfil_de(usuario)
    return rol == DELEGADO and perfil is not None and perfil.delegacion_id == compromiso.delegacion_id


def _puede_actualizar(usuario, compromiso):
    perfil = perfil_de(usuario)
    es_responsable = perfil is not None and perfil.pk == compromiso.responsable_id
    return usuario.has_perm('gestion.change_compromiso') and (es_responsable or _es_jefe(usuario, compromiso))


def filtrar_agenda(request, consulta):
    """Filtros de la agenda (HU-12): responsable, estado, territorio, situación,
    rango de fechas comprometidas, delegación y texto."""
    hoy = timezone.localdate()
    filtros = {}
    valor = request.GET.get('responsable', '')
    if valor.isdigit():
        consulta = consulta.filter(responsable_id=int(valor))
        filtros['responsable'] = valor
    valor = request.GET.get('delegacion', '')
    if valor.isdigit():
        consulta = consulta.filter(delegacion_id=int(valor))
        filtros['delegacion'] = valor
    valor = request.GET.get('estado', '')
    if valor in Compromiso.Estado.values:
        consulta = consulta.filter(estado=valor)
        filtros['estado'] = valor
    valor = request.GET.get('territorio', '').strip()
    if valor:
        consulta = consulta.filter(territorio__icontains=valor)
        filtros['territorio'] = valor
    desde, hasta = parse_date(request.GET.get('desde', '') or ''), parse_date(request.GET.get('hasta', '') or '')
    if desde:
        consulta = consulta.filter(fecha_compromiso__gte=desde)
        filtros['desde'] = desde.isoformat()
    if hasta:
        consulta = consulta.filter(fecha_compromiso__lte=hasta)
        filtros['hasta'] = hasta.isoformat()
    situacion = request.GET.get('situacion', '')
    abiertos = consulta.exclude(estado=Compromiso.Estado.REALIZADO)
    if situacion == 'abiertos':
        consulta = abiertos
    elif situacion == 'vencidos':
        consulta = abiertos.filter(fecha_compromiso__lt=hoy)
    elif situacion == 'proximos':
        dias = getattr(settings, 'SGR_DIAS_AVISO_COMPROMISO', 3)
        consulta = abiertos.filter(fecha_compromiso__gte=hoy, fecha_compromiso__lte=hoy + datetime.timedelta(days=dias))
    elif situacion == 'realizados':
        consulta = consulta.filter(estado=Compromiso.Estado.REALIZADO)
    if situacion in dict(SITUACIONES):
        filtros['situacion'] = situacion
    texto = request.GET.get('q', '').strip()
    if texto:
        consulta = consulta.filter(Q(codigo__icontains=texto) | Q(solicitante__icontains=texto)
                                   | Q(descripcion__icontains=texto))
        filtros['q'] = texto
    return consulta, filtros


def resumen_por_funcionario(compromisos):
    """Resumen colectivo (RF-021): totales por responsable y estado, con %
    realizado y % pendiente. Se calcula sobre la misma lista filtrada, así los
    totales coinciden con el detalle."""
    filas = {}
    for c in compromisos:
        fila = filas.setdefault(c.responsable_id, {
            'responsable': c.responsable, 'total': 0, 'vencidos': 0,
            **{estado: 0 for estado in Compromiso.Estado.values}})
        fila['total'] += 1
        fila[c.estado] += 1
        fila['vencidos'] += int(c.vencido)
    resultado = []
    for fila in sorted(filas.values(), key=lambda f: f['responsable'].nombre):
        realizados = fila[Compromiso.Estado.REALIZADO]
        fila['pct_realizado'] = round(realizados * 100 / fila['total'], 1)
        fila['pct_pendiente'] = round(100 - fila['pct_realizado'], 1)
        fila['ingresado'] = fila[Compromiso.Estado.INGRESADO]
        fila['pendiente'] = fila[Compromiso.Estado.PENDIENTE]
        fila['en_proceso'] = fila[Compromiso.Estado.EN_PROCESO]
        fila['realizado'] = realizados
        resultado.append(fila)
    return resultado


@permission_required('gestion.view_compromiso', raise_exception=True)
def agenda(request):
    base = filtrar_compromisos(request.user, Compromiso.objects.select_related('responsable', 'delegacion'))
    compromisos, filtros = filtrar_agenda(request, base)
    compromisos = list(compromisos)
    responsables = Funcionario.objects.filter(pk__in=base.values('responsable_id')).order_by('nombre')
    contexto = {
        'titulo_pagina': 'Agenda colectiva',
        'compromisos': compromisos,
        'resumen': resumen_por_funcionario(compromisos),
        'total': len(compromisos),
        'vencidos': sum(c.vencido for c in compromisos),
        'proximos': sum(c.proximo_a_vencer for c in compromisos),
        'filtros': filtros,
        'estados': Compromiso.Estado.values,
        'situaciones': SITUACIONES,
        'responsables': responsables,
        'delegaciones': Delegacion.objects.all() if ve_todo(request.user) else None,
        'puede_crear': request.user.has_perm('gestion.add_compromiso'),
        'query_string': request.GET.urlencode(),
    }
    return render(request, 'gestion/agenda.html', contexto)


@permission_required('gestion.add_compromiso', raise_exception=True)
def compromiso_crear(request):
    perfil = perfil_de(request.user)
    if perfil is None and rol_de(request.user) != ADMINISTRADOR:
        raise PermissionDenied('Su cuenta no está asociada a una delegación.')
    delegacion = perfil.delegacion if perfil else None
    inicial = {'responsable': perfil.pk if perfil else None}
    origen = request.GET.get('actividad', '')
    actividad_origen = None
    if origen.isdigit():
        from cuentas.perfiles import filtrar_actividades

        from .models import Actividad
        actividad_origen = filtrar_actividades(request.user, Actividad.objects.all()).filter(pk=int(origen)).first()
        if actividad_origen:
            inicial.update({'solicitante': actividad_origen.contacto, 'descripcion': actividad_origen.solicitud_problema
                            or actividad_origen.descripcion, 'organizacion': actividad_origen.organizacion_id})
    if request.method == 'POST':
        form = CompromisoForm(request.POST, delegacion=delegacion)
        if form.is_valid():
            compromiso = form.save(commit=False)
            compromiso.creado_por = request.user
            compromiso.actividad_origen = actividad_origen
            compromiso.save()
            messages.success(request, f'Compromiso {compromiso.codigo} agregado a la agenda colectiva.')
            return redirect(compromiso)
    else:
        form = CompromisoForm(initial=inicial, delegacion=delegacion)
    return render(request, 'comun/mantenedor_form.html', {
        'titulo_pagina': 'Nuevo compromiso', 'accion': 'Nuevo compromiso en la agenda colectiva', 'form': form,
        'volver_url': reverse('gestion:agenda'),
        'ayuda': ('El compromiso queda visible para todo el equipo de la delegación. Se destaca en amarillo cuando '
                  'está próximo a vencer y en rojo cuando vence sin realizarse.'),
    })


@permission_required('gestion.change_compromiso', raise_exception=True)
def compromiso_editar(request, pk):
    compromiso = _compromiso_visible(request, pk)
    if not _puede_actualizar(request.user, compromiso) or (compromiso.esta_cerrado and not _es_jefe(request.user, compromiso)):
        raise PermissionDenied('Solo el responsable o el Delegado pueden modificar este compromiso.')
    if request.method == 'POST':
        form = CompromisoForm(request.POST, instance=compromiso)
        if form.is_valid():
            form.save()
            messages.success(request, f'Compromiso {compromiso.codigo} actualizado.')
            return redirect(compromiso)
    else:
        form = CompromisoForm(instance=compromiso)
    return render(request, 'comun/mantenedor_form.html', {
        'titulo_pagina': f'Modificar {compromiso.codigo}', 'accion': f'Modificar compromiso {compromiso.codigo}',
        'form': form, 'volver_url': compromiso.get_absolute_url(),
        'ayuda': 'El estado y el responsable se cambian desde la ficha del compromiso, para que queden en el historial.',
    })


@permission_required('gestion.view_compromiso', raise_exception=True)
def compromiso_detalle(request, pk):
    compromiso = _compromiso_visible(request, pk)
    puede_actualizar = _puede_actualizar(request.user, compromiso)
    es_jefe = _es_jefe(request.user, compromiso)
    estado_form = reasignar_form = None
    if puede_actualizar and compromiso.estados_siguientes(es_jefe):
        estado_form = CambioEstadoCompromisoForm(compromiso=compromiso, puede_reabrir=es_jefe)
    if es_jefe and not compromiso.esta_cerrado:
        reasignar_form = ReasignarCompromisoForm(compromiso=compromiso)

    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'estado' and estado_form is not None:
            estado_form = CambioEstadoCompromisoForm(request.POST, compromiso=compromiso, puede_reabrir=es_jefe)
            if estado_form.is_valid():
                try:
                    compromiso.cambiar_estado(estado_form.cleaned_data['estado'], request.user,
                                              estado_form.cleaned_data['observacion'], puede_reabrir=es_jefe)
                except ValidationError as error:
                    messages.error(request, ' '.join(error.messages))
                else:
                    messages.success(request, f'{compromiso.codigo} pasó a "{compromiso.estado}".')
                    return redirect(compromiso)
        elif accion == 'reasignar' and reasignar_form is not None:
            reasignar_form = ReasignarCompromisoForm(request.POST, compromiso=compromiso)
            if reasignar_form.is_valid():
                compromiso.reasignar(reasignar_form.cleaned_data['responsable'], request.user,
                                     reasignar_form.cleaned_data['motivo'])
                messages.success(request, f'{compromiso.codigo} reasignado a {compromiso.responsable.nombre}.')
                return redirect(compromiso)
        else:
            raise PermissionDenied('No tiene permiso para esta acción.')

    return render(request, 'gestion/compromiso_detalle.html', {
        'titulo_pagina': compromiso.codigo,
        'compromiso': compromiso,
        'cambios': compromiso.cambios.select_related('autor'),
        'actividades': compromiso.actividades.all(),
        'estado_form': estado_form,
        'reasignar_form': reasignar_form,
        'puede_editar': puede_actualizar and (not compromiso.esta_cerrado or es_jefe),
        'puede_eliminar': es_jefe and request.user.has_perm('gestion.delete_compromiso'),
        'puede_registrar_actividad': (perfil_de(request.user) is not None
                                      and perfil_de(request.user).pk == compromiso.responsable_id
                                      and request.user.has_perm('gestion.add_actividad')
                                      and not compromiso.actividades.exists()),
    })


@permission_required('gestion.delete_compromiso', raise_exception=True)
def compromiso_eliminar(request, pk):
    compromiso = _compromiso_visible(request, pk)
    if not _es_jefe(request.user, compromiso):
        raise PermissionDenied('Solo el Delegado de la delegación puede eliminar compromisos.')
    if request.method == 'POST':
        codigo = compromiso.codigo
        compromiso.delete()
        messages.success(request, f'Compromiso {codigo} eliminado de la agenda.')
        return redirect('gestion:agenda')
    return render(request, 'confirmar_eliminar.html', {
        'titulo_pagina': 'Eliminar compromiso', 'accion': f'Eliminar compromiso: {compromiso}',
        'objeto': compromiso, 'volver_url': compromiso.get_absolute_url(),
        'advertencia': 'Se eliminará también su historial de cambios.',
    })
