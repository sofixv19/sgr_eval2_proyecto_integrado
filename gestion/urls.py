from django.urls import path

from . import views

app_name = 'gestion'

urlpatterns = [
    path('', views.listado, name='listado'),
    path('resumen/', views.resumen, name='resumen'),
    path('nueva/', views.crear, name='crear'),
    path('<int:actividad_id>/', views.detalle, name='detalle'),
    path('<int:actividad_id>/editar/', views.editar, name='editar'),
    path('<int:actividad_id>/eliminar/', views.eliminar, name='eliminar'),
    # Tabla maestra Categoría
    path('categorias/', views.CategoriaListado.as_view(), name='categorias'),
    path('categorias/nueva/', views.CategoriaCrear.as_view(), name='categoria_crear'),
    path('categorias/<int:pk>/editar/', views.CategoriaEditar.as_view(), name='categoria_editar'),
    path('categorias/<int:pk>/eliminar/', views.CategoriaEliminar.as_view(), name='categoria_eliminar'),
]
