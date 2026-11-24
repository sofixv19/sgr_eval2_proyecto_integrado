from django.urls import path

from . import views

app_name = 'territorio'

urlpatterns = [
    path('territorios/', views.TerritorioListado.as_view(), name='territorios'),
    path('territorios/nuevo/', views.TerritorioCrear.as_view(), name='territorio_crear'),
    path('territorios/<int:pk>/editar/', views.TerritorioEditar.as_view(), name='territorio_editar'),
    path('territorios/<int:pk>/eliminar/', views.TerritorioEliminar.as_view(), name='territorio_eliminar'),
    path('vecinos/', views.VecinoListado.as_view(), name='vecinos'),
    path('vecinos/nuevo/', views.VecinoCrear.as_view(), name='vecino_crear'),
    path('vecinos/<int:pk>/editar/', views.VecinoEditar.as_view(), name='vecino_editar'),
    path('vecinos/<int:pk>/eliminar/', views.VecinoEliminar.as_view(), name='vecino_eliminar'),
    path('membresias/', views.MembresiaListado.as_view(), name='membresias'),
    path('membresias/nuevo/', views.MembresiaCrear.as_view(), name='membresia_crear'),
    path('membresias/<int:pk>/editar/', views.MembresiaEditar.as_view(), name='membresia_editar'),
    path('membresias/<int:pk>/eliminar/', views.MembresiaEliminar.as_view(), name='membresia_eliminar'),
    path('hitos/', views.HitoListado.as_view(), name='hitos'),
    path('hitos/nuevo/', views.HitoCrear.as_view(), name='hito_crear'),
    path('hitos/<int:pk>/editar/', views.HitoEditar.as_view(), name='hito_editar'),
    path('hitos/<int:pk>/eliminar/', views.HitoEliminar.as_view(), name='hito_eliminar'),
    path('tipos-atencion/', views.TipoListado.as_view(), name='tipos'),
    path('tipos-atencion/nuevo/', views.TipoCrear.as_view(), name='tipo_crear'),
    path('tipos-atencion/<int:pk>/editar/', views.TipoEditar.as_view(), name='tipo_editar'),
    path('tipos-atencion/<int:pk>/eliminar/', views.TipoEliminar.as_view(), name='tipo_eliminar'),
    path('subtipos-atencion/', views.SubtipoListado.as_view(), name='subtipos'),
    path('subtipos-atencion/nuevo/', views.SubtipoCrear.as_view(), name='subtipo_crear'),
    path('subtipos-atencion/<int:pk>/editar/', views.SubtipoEditar.as_view(), name='subtipo_editar'),
    path('subtipos-atencion/<int:pk>/eliminar/', views.SubtipoEliminar.as_view(), name='subtipo_eliminar'),
    path('vecinos/buscar/', views.buscar_vecino, name='buscar_vecino'),
]
