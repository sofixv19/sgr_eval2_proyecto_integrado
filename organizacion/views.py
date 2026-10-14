"""
Vistas de la app 'organizacion': mantenedores (CRUD) de las tablas maestras
Cargo, Funcionario y Meta.

Las tres usan las vistas genéricas de comun/vistas.py, que ya resuelven el
control de acceso por permisos, los mensajes y el manejo de errores al
eliminar. Aquí solo se configura qué modelo, formulario y columnas usa cada
mantenedor.
"""
from django.db.models import Count

from comun.vistas import (
    MantenedorCrear, MantenedorDetalle, MantenedorEditar, MantenedorEliminar, MantenedorListado,
)

from .forms import CargoFuncionForm, FuncionarioForm, MetaProyectoForm, PeriodoForm
from .models import CargoFuncion, Funcionario, MetaProyecto, Periodo


# --------------------------------------------------------------------- Cargos
class CargoConfig:
    model = CargoFuncion
    form_class = CargoFuncionForm
    nombre_singular = 'cargo'
    nombre_plural = 'cargos y funciones'
    url_listado = 'organizacion:cargos'


class CargoListado(CargoConfig, MantenedorListado):
    campos_busqueda = ('nombre_cargo', 'descripcion')
    columnas = (('Cargo', 'nombre_cargo'), ('Descripción', 'descripcion'), ('Vigente', 'active'))
    url_crear, url_editar, url_eliminar = 'organizacion:cargo_crear', 'organizacion:cargo_editar', 'organizacion:cargo_eliminar'


class CargoCrear(CargoConfig, MantenedorCrear):
    pass


class CargoEditar(CargoConfig, MantenedorEditar):
    pass


class CargoEliminar(CargoConfig, MantenedorEliminar):
    advertencia = 'Si el cargo tiene funcionarios asignados no se podrá eliminar. Sus metas se eliminan junto con el cargo.'


# --------------------------------------------------------------- Funcionarios
class FuncionarioConfig:
    model = Funcionario
    form_class = FuncionarioForm
    nombre_singular = 'funcionario'
    nombre_plural = 'funcionarios'
    url_listado = 'organizacion:listado'


class FuncionarioListado(FuncionarioConfig, MantenedorListado):
    template_name = 'organizacion/listado.html'
    campos_busqueda = ('nombre', 'rut', 'email', 'cargo__nombre_cargo', 'delegacion__nombre')
    url_crear, url_editar, url_eliminar, url_detalle = (
        'organizacion:funcionario_crear', 'organizacion:funcionario_editar',
        'organizacion:funcionario_eliminar', 'organizacion:funcionario_detalle',
    )

    def get_queryset(self):
        return super().get_queryset().select_related('delegacion', 'cargo')


class FuncionarioDetalle(FuncionarioConfig, MantenedorDetalle):
    campos_detalle = (
        ('RUT', 'rut'), ('Correo', 'email'), ('Delegación', 'delegacion'),
        ('Cargo', 'cargo.nombre_cargo'), ('Rol del sistema', 'rol'), ('Activo', 'activo'),
        ('Fecha de creación', 'creado'),
    )
    url_editar, url_eliminar = 'organizacion:funcionario_editar', 'organizacion:funcionario_eliminar'


class FuncionarioCrear(FuncionarioConfig, MantenedorCrear):
    pass


class FuncionarioEditar(FuncionarioConfig, MantenedorEditar):
    pass


class FuncionarioEliminar(FuncionarioConfig, MantenedorEliminar):
    advertencia = ('Si el funcionario tiene actividades registradas o validadas no se podrá eliminar; '
                   'en ese caso márquelo como inactivo.')


# ---------------------------------------------------------------------- Metas
class MetaConfig:
    model = MetaProyecto
    form_class = MetaProyectoForm
    nombre_singular = 'meta'
    nombre_plural = 'metas institucionales'
    url_listado = 'organizacion:metas'


class MetaListado(MetaConfig, MantenedorListado):
    campos_busqueda = ('item_medible', 'cargo__nombre_cargo')
    columnas = (
        ('Cargo', 'cargo.nombre_cargo'), ('Período', 'periodo'), ('Meta', 'item_medible'), ('Valor objetivo', 'valor_objetivo'),
        ('Unidad', 'unidad'), ('Ponderador (%)', 'ponderador'),
    )
    url_crear, url_editar, url_eliminar = 'organizacion:meta_crear', 'organizacion:meta_editar', 'organizacion:meta_eliminar'
    descripcion = 'La suma de ponderadores de cada cargo en un período no puede superar 100 %.'

    def get_queryset(self):
        return super().get_queryset().select_related('cargo', 'periodo')


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
