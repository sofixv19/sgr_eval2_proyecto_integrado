from django.urls import path

from . import views

app_name = 'organizacion'

urlpatterns = [
    # Funcionarios
    path('funcionarios/', views.FuncionarioListado.as_view(), name='listado'),
    path('funcionarios/nuevo/', views.FuncionarioCrear.as_view(), name='funcionario_crear'),
    path('funcionarios/<int:pk>/', views.FuncionarioDetalle.as_view(), name='funcionario_detalle'),
    path('funcionarios/<int:pk>/editar/', views.FuncionarioEditar.as_view(), name='funcionario_editar'),
    path('funcionarios/<int:pk>/eliminar/', views.FuncionarioEliminar.as_view(), name='funcionario_eliminar'),
    # Cargos
    path('cargos/', views.CargoListado.as_view(), name='cargos'),
    path('cargos/nuevo/', views.CargoCrear.as_view(), name='cargo_crear'),
    path('cargos/<int:pk>/editar/', views.CargoEditar.as_view(), name='cargo_editar'),
    path('cargos/<int:pk>/eliminar/', views.CargoEliminar.as_view(), name='cargo_eliminar'),
    # Períodos
    path('periodos/', views.PeriodoListado.as_view(), name='periodos'),
    path('periodos/nuevo/', views.PeriodoCrear.as_view(), name='periodo_crear'),
    path('periodos/<int:pk>/editar/', views.PeriodoEditar.as_view(), name='periodo_editar'),
    path('periodos/<int:pk>/eliminar/', views.PeriodoEliminar.as_view(), name='periodo_eliminar'),
    # Metas
    path('metas/', views.MetaListado.as_view(), name='metas'),
    path('metas/nueva/', views.MetaCrear.as_view(), name='meta_crear'),
    path('metas/<int:pk>/editar/', views.MetaEditar.as_view(), name='meta_editar'),
    path('metas/<int:pk>/eliminar/', views.MetaEliminar.as_view(), name='meta_eliminar'),
]
