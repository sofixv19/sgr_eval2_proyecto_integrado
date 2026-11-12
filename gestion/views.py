"""
Vistas de la app 'gestion' (Aplicación 2).

Evaluación Sumativa 2: todas las vistas obtienen la información mediante
consultas Django ORM (antes se leía desde data/actividades.json).
"""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date

from comun.vistas import MantenedorCrear, MantenedorEditar, MantenedorEliminar, MantenedorListado
from cuentas.perfiles import (
    ADMINISTRADOR, DELEGADO, FUNCIONARIO, es_delegado_de, filtrar_actividades, perfil_de, rol_de, ve_todo,
)
from delegaciones.models import Delegacion
from organizacion.models import Funcionario, Periodo

from .forms import (
    ActividadForm, CategoriaForm, EvidenciaForm, RevisionForm, inicio_ventana_registro, ingresos_de_hoy,
)
from .models import Actividad, Categoria, Compromiso, Evidencia
from .services import grados_donut, resumen_por_estado


def _actividad_visible(request, actividad_id):
    """Devuelve la actividad solo si está dentro del ámbito del usuario;
    si no, 404 (no se revela que existe)."""
    consulta = filtrar_actividades(
        request.user,
        Actividad.objects.select_related('delegacion', 'categoria', 'funcionario', 'validado_por'),
    )
    return get_object_or_404(consulta, pk=actividad_id)


def _es_duenio(request, actividad):
    perfil = perfil_de(request.user)
    return perfil is not None and perfil.pk == actividad.funcionario_id


def filtrar_listado_actividades(request, actividades):
    """Filtros del listado (RF-032 / HU-29), compartidos con la exportación:
    estado, validación, delegación, funcionario, ítem (categoría), período,
    rango de fechas y texto. Devuelve (consulta, filtros aplicados)."""
    filtros = {}
    valor = request.GET.get('estado')
    if valor in Actividad.Estado.values:
        actividades = actividades.filter(estado=valor)
        filtros['estado'] = valor
    valor = request.GET.get('validacion')
    if valor in Actividad.EstadoValidacion.values:
        actividades = actividades.filter(estado_validacion=valor)
        filtros['validacion'] = valor
    for campo, nombre in (('delegacion', 'delegacion_id'), ('funcionario', 'funcionario_id'),
                          ('categoria', 'categoria_id')):
        valor = request.GET.get(campo, '')
        if valor.isdigit():
            actividades = actividades.filter(**{nombre: int(valor)})
            filtros[campo] = valor
    valor = request.GET.get('periodo', '')
    if valor.isdigit():
        periodo = Periodo.objects.filter(pk=int(valor)).first()
        if periodo:
            actividades = actividades.filter(fecha__range=(periodo.fecha_inicio, periodo.fecha_fin))
            filtros['periodo'] = valor
    for campo, condicion in (('desde', 'fecha__gte'), ('hasta', 'fecha__lte')):
        fecha = parse_date(request.GET.get(campo, '') or '')
        if fecha:
            actividades = actividades.filter(**{condicion: fecha})
            filtros[campo] = fecha.isoformat()
    query = request.GET.get('q', '').strip()
    if query:
        actividades = actividades.filter(
            Q(codigo__icontains=query)
            | Q(descripcion__icontains=query)
            | Q(delegacion__nombre__icontains=query)
            | Q(categoria__nombre__icontains=query)
            | Q(funcionario__nombre__icontains=query)
        )
        filtros['q'] = query
    return actividades, filtros


@permission_required('gestion.view_actividad', raise_exception=True)
def listado(request):
    """Actividades según el rol: el Funcionario ve solo las suyas, el
    Delegado las de su delegación y el Coordinador/Administrador todas."""

    base = filtrar_actividades(
        request.user, Actividad.objects.select_related('delegacion', 'categoria', 'funcionario'),
    )
    actividades, filtros = filtrar_listado_actividades(request, base)

    rol = rol_de(request.user)
    titulos = {FUNCIONARIO: 'Mis actividades', DELEGADO: 'Actividades de mi delegación'}
    contexto = {
        'titulo_pagina': titulos.get(rol, 'Actividades registradas'),
        'actividades': actividades.annotate(total_evidencias=Count('evidencias')),
        'estados': Actividad.Estado.values,
        'estados_validacion': Actividad.EstadoValidacion.choices,
        'estado_seleccionado': filtros.get('estado'),
        'validacion_seleccionada': filtros.get('validacion'),
        'query': filtros.get('q', ''),
        'filtros': filtros,
        'total': actividades.count(),
        'puede_registrar': _puede_registrar(request.user),
        # Filtros adicionales (RF-032)
        'opciones_delegacion': Delegacion.objects.all() if ve_todo(request.user) else None,
        'opciones_funcionario': (Funcionario.objects.filter(pk__in=base.values('funcionario_id')).order_by('nombre')
                                 if rol != FUNCIONARIO else None),
        'opciones_categoria': Categoria.objects.all(),
        'opciones_periodo': Periodo.objects.all(),
        'query_string': request.GET.urlencode(),
    }
    return render(request, 'gestion/listado.html', contexto)


def _puede_registrar(usuario):
    if not usuario.has_perm('gestion.add_actividad'):
        return False
    rol = rol_de(usuario)
    perfil = perfil_de(usuario)
    return rol == ADMINISTRADOR or (rol == FUNCIONARIO and perfil is not None and perfil.activo)


@permission_required('gestion.view_actividad', raise_exception=True)
def detalle(request, actividad_id):
    """Ficha de una actividad con sus evidencias.

    - El Funcionario dueño puede subir evidencia mientras no esté validada.
    - El Delegado de esa delegación revisa la evidencia: aprueba o rechaza
      con observación (es "la pega" del Delegado, según el profesor).
    """
    actividad = _actividad_visible(request, actividad_id)
    duenio = _es_duenio(request, actividad)
    puede_subir = duenio and actividad.editable_por_funcionario
    periodo_cerrado = actividad.periodo_cerrado
    puede_revisar = (request.user.has_perm('gestion.validar_actividad')
                     and es_delegado_de(request.user, actividad.delegacion_id)
                     and not duenio
                     and actividad.estado_validacion != Actividad.EstadoValidacion.VALIDADA
                     and periodo_cerrado is None)

    evidencia_form = EvidenciaForm() if puede_subir else None
    revision_form = RevisionForm(actividad=actividad) if puede_revisar else None

    if request.method == 'POST' and 'subir_evidencia' in request.POST and puede_subir:
        evidencia_form = EvidenciaForm(request.POST, request.FILES)
        if evidencia_form.is_valid():
            evidencia = evidencia_form.save(commit=False)
            evidencia.actividad = actividad
            evidencia.subida_por = request.user
            evidencia.save()
            if actividad.estado_validacion == Actividad.EstadoValidacion.RECHAZADA:
                # Al corregir, la actividad vuelve a quedar pendiente de revisión.
                actividad.estado_validacion = Actividad.EstadoValidacion.PENDIENTE
                actividad.save(update_fields=['estado_validacion'])
            messages.success(request, f'Evidencia {evidencia} subida. Queda pendiente de validación del Delegado.')
            return redirect('gestion:detalle', actividad_id=actividad.id)

    if request.method == 'POST' and 'revisar' in request.POST and puede_revisar:
        revision_form = RevisionForm(request.POST, actividad=actividad)
        if revision_form.is_valid():
            delegado = perfil_de(request.user)
            if revision_form.cleaned_data['decision'] == 'aprobar':
                actividad.marcar_validado(delegado)
                messages.success(request, f'Actividad {actividad.codigo} validada: ahora suma al avance del funcionario.')
            else:
                actividad.rechazar(delegado, revision_form.cleaned_data['observacion'])
                messages.warning(request, f'Actividad {actividad.codigo} rechazada. El funcionario verá la observación.')
            return redirect('gestion:detalle', actividad_id=actividad.id)

    contexto = {
        'titulo_pagina': f'Actividad {actividad.codigo}',
        'actividad': actividad,
        'evidencias': actividad.evidencias.all(),
        'evidencia_form': evidencia_form,
        'revision_form': revision_form,
        'periodo_cerrado': periodo_cerrado,
        'puede_editar': periodo_cerrado is None and (
            duenio and actividad.editable_por_funcionario or rol_de(request.user) == ADMINISTRADOR),
        'puede_eliminar': periodo_cerrado is None and request.user.has_perm('gestion.delete_actividad') and (
            rol_de(request.user) == ADMINISTRADOR
            or (duenio and actividad.estado_validacion == Actividad.EstadoValidacion.PENDIENTE)),
        # RF-009: la actividad puede originar un compromiso futuro en la agenda colectiva.
        'puede_agendar': duenio and request.user.has_perm('gestion.add_compromiso'),
        'compromisos_generados': actividad.compromisos_generados.all(),
    }
    return render(request, 'gestion/detalle.html', contexto)


@permission_required('gestion.view_actividad', raise_exception=True)
def evidencia(request, evidencia_id):
    """Entrega el archivo de una evidencia solo a quien puede ver la
    actividad (no hay una carpeta pública de archivos)."""
    evidencia = get_object_or_404(Evidencia.objects.select_related('actividad'), pk=evidencia_id)
    _actividad_visible(request, evidencia.actividad_id)
    try:
        archivo = evidencia.archivo.open('rb')
    except FileNotFoundError:
        raise Http404('El archivo de la evidencia no está disponible.')
    return FileResponse(archivo, as_attachment=False, filename=str(evidencia))


@permission_required('gestion.view_actividad', raise_exception=True)
def resumen(request):
    """Vista tipo 'semáforo': totaliza las actividades visibles por estado."""

    conteo, total = resumen_por_estado(filtrar_actividades(request.user, Actividad.objects.all()))

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
# Registro, modificación y eliminación de actividades
# ---------------------------------------------------------------------------

@permission_required('gestion.add_actividad', raise_exception=True)
def crear(request):
    """Solo el Funcionario registra SUS actividades (el Administrador puede
    hacerlo en nombre de otro). El Delegado y el Coordinador no registran."""
    if not _puede_registrar(request.user):
        raise PermissionDenied('Su cuenta no está asociada a un funcionario activo.')
    es_admin = rol_de(request.user) == ADMINISTRADOR and perfil_de(request.user) is None
    funcionario = None if es_admin else perfil_de(request.user)

    # RF-020: la actividad puede cumplir un compromiso de la agenda colectiva
    # del que el funcionario es responsable (una sola actividad por compromiso).
    compromiso = None
    id_compromiso = request.POST.get('compromiso') or request.GET.get('compromiso', '')
    if str(id_compromiso).isdigit() and funcionario is not None:
        compromiso = (Compromiso.objects.filter(pk=int(id_compromiso), responsable=funcionario)
                      .exclude(actividades__isnull=False).first())
    inicial = {}
    if compromiso:
        inicial = {'descripcion': '', 'solicitud_problema': compromiso.descripcion, 'contacto': compromiso.solicitante,
                   'organizacion': compromiso.organizacion_id,
                   'tipo_solicitante': (Actividad.TipoSolicitante.ORGANIZACION if compromiso.organizacion_id
                                        else Actividad.TipoSolicitante.VECINO)}

    if request.method == 'POST':
        form = ActividadForm(request.POST, request.FILES, funcionario=funcionario, elegir_funcionario=es_admin)
        if form.is_valid():
            actividad = form.save(usuario=request.user)
            mensaje = f'Actividad registrada con el código {actividad.codigo}.'
            if compromiso:
                actividad.compromiso = compromiso
                actividad.save(update_fields=['compromiso'])
                if not compromiso.esta_cerrado:
                    compromiso.cambiar_estado(Compromiso.Estado.REALIZADO, request.user,
                                              f'Cumplido con la actividad {actividad.codigo}.', puede_reabrir=False)
                mensaje += f' El compromiso {compromiso.codigo} quedó Realizado.'
            messages.success(request, mensaje)
            return redirect('gestion:detalle', actividad_id=actividad.id)
    else:
        form = ActividadForm(initial=inicial, funcionario=funcionario, elegir_funcionario=es_admin)

    contexto = {
        'titulo_pagina': 'Registrar actividad',
        'accion': 'Registrar actividad',
        'form': form,
        'funcionario': funcionario,
        'volver_url': reverse('gestion:listado'),
        # Versión 2.0: ventana de la semana y ingresos del día
        'inicio_ventana': inicio_ventana_registro(),
        'ingresos_hoy': ingresos_de_hoy(funcionario) if funcionario else None,
        'max_ingresos': settings.SGR_MAX_INGRESOS_DIARIOS,
        'compromiso': compromiso,
    }
    return render(request, 'gestion/form.html', contexto)


@permission_required('gestion.change_actividad', raise_exception=True)
def editar(request, actividad_id):
    actividad = _actividad_visible(request, actividad_id)
    es_admin = rol_de(request.user) == ADMINISTRADOR
    if actividad.periodo_cerrado is not None:
        raise PermissionDenied(f'El período {actividad.periodo_cerrado} está cerrado: reábralo para corregir (RN-013).')
    if not es_admin and not (_es_duenio(request, actividad) and actividad.editable_por_funcionario):
        raise PermissionDenied('Solo el funcionario que registró la actividad puede modificarla, y solo si no está validada.')

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
        'funcionario': actividad.funcionario,
        'volver_url': reverse('gestion:detalle', args=[actividad.pk]),
    }
    return render(request, 'gestion/form.html', contexto)


@permission_required('gestion.delete_actividad', raise_exception=True)
def eliminar(request, actividad_id):
    actividad = _actividad_visible(request, actividad_id)
    if actividad.periodo_cerrado is not None:
        raise PermissionDenied(f'El período {actividad.periodo_cerrado} está cerrado: reábralo para corregir (RN-013).')
    if rol_de(request.user) != ADMINISTRADOR and not (
            _es_duenio(request, actividad) and actividad.estado_validacion == Actividad.EstadoValidacion.PENDIENTE):
        raise PermissionDenied('No puede eliminar esta actividad.')

    if request.method == 'POST':
        codigo = actividad.codigo
        actividad.delete()
        messages.success(request, f'Actividad "{codigo}" eliminada correctamente.')
        return redirect('gestion:listado')

    contexto = {
        'titulo_pagina': f'Eliminar {actividad.codigo}',
        'accion': f'Eliminar actividad: {actividad.codigo}',
        'objeto': actividad,
        'advertencia': 'También se eliminarán sus evidencias.',
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
