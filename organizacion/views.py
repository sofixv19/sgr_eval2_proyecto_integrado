"""
Vistas de la app 'organizacion': mantenedores (CRUD) de las tablas maestras
Cargo, Funcionario y Meta.

Las tres usan las vistas genéricas de comun/vistas.py, que ya resuelven el
control de acceso por permisos, los mensajes y el manejo de errores al
eliminar. Aquí solo se configura qué modelo, formulario y columnas usa cada
mantenedor.
"""
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from comun.vistas import (
    MantenedorCrear, MantenedorDetalle, MantenedorEditar, MantenedorEliminar, MantenedorListado,
)
from cuentas.perfiles import (
    COORDINADOR, DELEGADO, filtrar_funcionarios, filtrar_metas, filtrar_por_funcionario, generar_clave, perfil_de,
    rol_de, sincronizar_cuenta,
)
from gestion.indicadores import cumplimiento_funcionario

from .forms import (
    AusenciaForm, CargoFuncionForm, FuncionarioForm, MetaFuncionarioForm, PeriodoForm, ReconocimientoForm,
)
from .models import Ausencia, CargoFuncion, Funcionario, MetaProyecto, Periodo, Reconocimiento


# --------------------------------------------------------------------- Cargos
class CargoConfig:
    model = CargoFuncion
    form_class = CargoFuncionForm
    nombre_singular = 'cargo'
    nombre_plural = 'cargos y funciones'
    url_listado = 'organizacion:cargos'


class CargoListado(CargoConfig, MantenedorListado):
    campos_busqueda = ('nombre_cargo', 'descripcion')
    columnas = (('Cargo', 'nombre_cargo'), ('Área', 'area'), ('Descripción', 'descripcion'), ('Vigente', 'active'))
    url_crear, url_editar, url_eliminar = 'organizacion:cargo_crear', 'organizacion:cargo_editar', 'organizacion:cargo_eliminar'


class CargoCrear(CargoConfig, MantenedorCrear):
    pass


class CargoEditar(CargoConfig, MantenedorEditar):
    pass


class CargoEliminar(CargoConfig, MantenedorEliminar):
    advertencia = 'Si el cargo tiene funcionarios asignados no se podrá eliminar. Sus metas se eliminan junto con el cargo.'


# --------------------------------------------------------------- Funcionarios
def _modo_funcionario(usuario):
    rol = rol_de(usuario)
    if rol == DELEGADO:
        return 'delegado'
    if rol == COORDINADOR:
        return 'coordinador'
    return 'admin'


def _mensaje_credenciales(request, funcionario, clave):
    messages.info(
        request,
        f'Credenciales para entregar a {funcionario.nombre}: usuario «{funcionario.usuario.username}», '
        f'contraseña temporal «{clave}». Cópielas ahora: la contraseña no se volverá a mostrar.',
    )


def _funcionarios_gestionables(usuario, consulta):
    """Cada rol solo crea o modifica a quienes le corresponden: el Delegado a
    los funcionarios de su delegación y el Coordinador a los Delegados."""
    consulta = filtrar_funcionarios(usuario, consulta)
    modo = _modo_funcionario(usuario)
    if modo == 'delegado':
        return consulta.filter(rol='Funcionario')
    if modo == 'coordinador':
        return consulta.filter(rol='Delegado')
    return consulta


class FuncionarioConfig:
    model = Funcionario
    form_class = FuncionarioForm
    nombre_singular = 'funcionario'
    nombre_plural = 'funcionarios'
    url_listado = 'organizacion:listado'

    def get_queryset(self):
        consulta = super().get_queryset().select_related('delegacion', 'cargo', 'usuario')
        if self.accion_permiso in ('add', 'change', 'delete'):
            return _funcionarios_gestionables(self.request.user, consulta)
        return filtrar_funcionarios(self.request.user, consulta)


class FuncionarioFormMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        modo = _modo_funcionario(self.request.user)
        kwargs['modo'] = modo
        if modo == 'delegado':
            perfil = perfil_de(self.request.user)
            if perfil is None:
                raise PermissionDenied('Su cuenta no está asociada a una delegación.')
            kwargs['delegacion'] = perfil.delegacion
        return kwargs

    def get_initial(self):
        inicial = super().get_initial()
        delegacion = self.request.GET.get('delegacion', '')
        if delegacion.isdigit():
            inicial['delegacion'] = int(delegacion)
        return inicial

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        modo = _modo_funcionario(self.request.user)
        if modo == 'coordinador' and isinstance(self, MantenedorCrear):
            contexto['titulo_pagina'] = contexto['accion'] = 'Crear Delegado'
        if modo == 'coordinador':
            contexto['ayuda'] = ('Como Coordinador, aquí crea a los Delegados y los asigna a una delegación. '
                                 'Al guardar se crea su cuenta de acceso.')
        elif modo == 'delegado':
            contexto['ayuda'] = (f'El funcionario quedará en su delegación ({perfil_de(self.request.user).delegacion}). '
                                 'Al guardar se crea su cuenta de acceso para entregarle las credenciales.')
        return contexto


class FuncionarioListado(FuncionarioConfig, MantenedorListado):
    template_name = 'organizacion/listado.html'
    campos_busqueda = ('nombre', 'rut', 'email', 'cargo__nombre_cargo', 'delegacion__nombre')
    url_crear, url_editar, url_eliminar, url_detalle = (
        'organizacion:funcionario_crear', 'organizacion:funcionario_editar',
        'organizacion:funcionario_eliminar', 'organizacion:funcionario_detalle',
    )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        gestionables = _funcionarios_gestionables(self.request.user, Funcionario.objects.all())
        contexto['ids_gestionables'] = set(gestionables.values_list('pk', flat=True))
        return contexto


class FuncionarioDetalle(FuncionarioConfig, MantenedorDetalle):
    template_name = 'organizacion/funcionario_detalle.html'
    campos_detalle = (
        ('RUT', 'rut'), ('Correo', 'email'), ('Delegación', 'delegacion'),
        ('Cargo', 'cargo.nombre_cargo'), ('Área', 'cargo.area'), ('Rol del sistema', 'rol'), ('Activo', 'activo'),
        ('Usuario de acceso', 'usuario.username'), ('Fecha de creación', 'creado'),
    )
    url_editar, url_eliminar = 'organizacion:funcionario_editar', 'organizacion:funcionario_eliminar'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        gestionables = _funcionarios_gestionables(self.request.user, Funcionario.objects.filter(pk=self.object.pk))
        contexto['puede_gestionar'] = (self.request.user.has_perm('organizacion.change_funcionario')
                                       and gestionables.exists())
        if self.object.rol != 'Delegado':
            contexto['resultado'] = cumplimiento_funcionario(self.object)
        return contexto


class FuncionarioCrear(FuncionarioFormMixin, FuncionarioConfig, MantenedorCrear):
    def form_valid(self, form):
        respuesta = super().form_valid(form)
        _, clave = sincronizar_cuenta(self.object)
        _mensaje_credenciales(self.request, self.object, clave)
        return respuesta

    def get_success_url(self):
        return reverse('organizacion:funcionario_detalle', args=[self.object.pk])


class FuncionarioEditar(FuncionarioFormMixin, FuncionarioConfig, MantenedorEditar):
    def form_valid(self, form):
        respuesta = super().form_valid(form)
        _, clave = sincronizar_cuenta(self.object)
        if clave:
            _mensaje_credenciales(self.request, self.object, clave)
        return respuesta


class FuncionarioEliminar(FuncionarioConfig, MantenedorEliminar):
    advertencia = ('Si el funcionario tiene actividades registradas o validadas no se podrá eliminar; '
                   'en ese caso márquelo como inactivo.')


@require_POST
@permission_required('organizacion.change_funcionario', raise_exception=True)
def nueva_clave(request, pk):
    """Genera una nueva contraseña temporal para entregarla al funcionario."""
    funcionario = get_object_or_404(_funcionarios_gestionables(request.user, Funcionario.objects.all()), pk=pk)
    _, clave = sincronizar_cuenta(funcionario, clave=generar_clave())
    _mensaje_credenciales(request, funcionario, clave)
    return redirect('organizacion:funcionario_detalle', pk=pk)


# ---------------------------------------------------------------------- Metas
class MetaConfig:
    model = MetaProyecto
    form_class = MetaFuncionarioForm
    nombre_singular = 'meta'
    nombre_plural = 'metas de los funcionarios'
    url_listado = 'organizacion:metas'

    def get_queryset(self):
        return filtrar_metas(self.request.user, super().get_queryset().select_related(
            'cargo', 'periodo', 'funcionario', 'funcionario__delegacion', 'categoria'))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.get_form_class() is MetaFuncionarioForm:
            kwargs['funcionarios'] = filtrar_funcionarios(self.request.user, Funcionario.objects.all())
        return kwargs


class MetaListado(MetaConfig, MantenedorListado):
    campos_busqueda = ('item_medible', 'funcionario__nombre', 'cargo__nombre_cargo')
    columnas = (
        ('Funcionario', 'funcionario.nombre'), ('Delegación', 'funcionario.delegacion'), ('Período', 'periodo'),
        ('Ítem medido', 'item_medible'), ('Meta', 'valor_objetivo'), ('Ponderador (%)', 'ponderador'),
    )
    url_crear, url_editar, url_eliminar = 'organizacion:meta_crear', 'organizacion:meta_editar', 'organizacion:meta_eliminar'
    descripcion = ('El Delegado asigna las metas a los funcionarios de su delegación. El avance de cada meta '
                   'es la cantidad de actividades validadas de esa categoría en el período, y la suma de '
                   'ponderadores de un funcionario no puede superar 100 %. Versión 2.0: cada ítem llega como '
                   'máximo a 120 %; pasado eso, más actividades no suben el puntaje.')


class MetaCrear(MetaConfig, MantenedorCrear):
    pass


class MetaEditar(MetaConfig, MantenedorEditar):
    pass


class MetaEliminar(MetaConfig, MantenedorEliminar):
    pass


# ------------------------------------------------------------------- Períodos
class PeriodoConfig:
    model = Periodo
    form_class = PeriodoForm
    nombre_singular = 'período'
    nombre_plural = 'períodos de medición'
    url_listado = 'organizacion:periodos'


class PeriodoListado(PeriodoConfig, MantenedorListado):
    campos_busqueda = ('nombre', 'estado')
    columnas = (('Período', 'nombre'), ('Inicio', 'fecha_inicio'), ('Término', 'fecha_fin'), ('Estado', 'estado'),
                ('N.º de metas', 'total_metas'))
    url_crear, url_editar, url_eliminar = (
        'organizacion:periodo_crear', 'organizacion:periodo_editar', 'organizacion:periodo_eliminar',
    )
    descripcion = 'Solo puede haber un período Abierto y los períodos no pueden solaparse.'

    def get_queryset(self):
        return super().get_queryset().annotate(total_metas=Count('metas'))


class PeriodoCrear(PeriodoConfig, MantenedorCrear):
    pass


class PeriodoEditar(PeriodoConfig, MantenedorEditar):
    pass


class PeriodoEliminar(PeriodoConfig, MantenedorEliminar):
    advertencia = 'Si el período tiene metas asociadas no se podrá eliminar.'


# ------------------------------------- Versión 2.0: felicitaciones y ausencias
class _RegistroDelEquipoConfig:
    """Felicitaciones/reclamos y ausencias: las registra el Delegado para los
    funcionarios de su delegación (Nuevos requerimientos, reglas 8 y 9)."""

    def get_queryset(self):
        return filtrar_por_funcionario(self.request.user, super().get_queryset().select_related(
            'funcionario', 'funcionario__delegacion', 'registrado_por'))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.get_form_class() is self.form_class:
            kwargs['funcionarios'] = filtrar_funcionarios(self.request.user, Funcionario.objects.all())
        return kwargs

    def form_valid(self, form):
        if rol_de(self.request.user) == DELEGADO:
            form.instance.registrado_por = perfil_de(self.request.user)
        return super().form_valid(form)


class ReconocimientoConfig(_RegistroDelEquipoConfig):
    model = Reconocimiento
    form_class = ReconocimientoForm
    nombre_singular = 'felicitación o reclamo'
    nombre_plural = 'felicitaciones y reclamos'
    url_listado = 'organizacion:reconocimientos'


class ReconocimientoListado(ReconocimientoConfig, MantenedorListado):
    campos_busqueda = ('funcionario__nombre', 'detalle')
    columnas = (('Fecha', 'fecha'), ('Tipo', 'tipo'), ('Funcionario', 'funcionario.nombre'),
                ('Delegación', 'funcionario.delegacion'), ('Respaldo', 'respaldo'),
                ('Registrado por', 'registrado_por.nombre'))
    url_crear, url_editar, url_eliminar = (
        'organizacion:reconocimiento_crear', 'organizacion:reconocimiento_editar',
        'organizacion:reconocimiento_eliminar')
    descripcion = ('Versión 2.0: cada felicitación suma 10 puntos al cumplimiento del funcionario (máximo 3 por '
                   'período) y cada reclamo resta 20. Las registra solo el Delegado, con respaldo formal: '
                   'una felicitación enviada por mensaje directo al funcionario no es válida.')


class ReconocimientoCrear(ReconocimientoConfig, MantenedorCrear):
    pass


class ReconocimientoEditar(ReconocimientoConfig, MantenedorEditar):
    pass


class ReconocimientoEliminar(ReconocimientoConfig, MantenedorEliminar):
    pass


class AusenciaConfig(_RegistroDelEquipoConfig):
    model = Ausencia
    form_class = AusenciaForm
    nombre_singular = 'ausencia'
    nombre_plural = 'ausencias del equipo'
    url_listado = 'organizacion:ausencias'


class AusenciaListado(AusenciaConfig, MantenedorListado):
    campos_busqueda = ('funcionario__nombre', 'observacion')
    columnas = (('Funcionario', 'funcionario.nombre'), ('Tipo', 'tipo'), ('Desde', 'desde'),
                ('Hasta', 'hasta'), ('Días', 'dias'), ('Registrado por', 'registrado_por.nombre'))
    url_crear, url_editar, url_eliminar = (
        'organizacion:ausencia_crear', 'organizacion:ausencia_editar', 'organizacion:ausencia_eliminar')
    descripcion = ('Versión 2.0: los días libres, vacaciones, días administrativos y licencias los ingresa el '
                   'Delegado. Esos días se descuentan del período y así se ajusta la meta esperada del '
                   'funcionario en el semáforo.')


class AusenciaCrear(AusenciaConfig, MantenedorCrear):
    pass


class AusenciaEditar(AusenciaConfig, MantenedorEditar):
    pass


class AusenciaEliminar(AusenciaConfig, MantenedorEliminar):
    pass
