from django.urls import path

from . import exportar, views, views_agenda

app_name = 'gestion'

urlpatterns = [
    path('', views.listado, name='listado'),
    path('nueva/', views.crear, name='crear'),
    path('<int:actividad_id>/', views.detalle, name='detalle'),
    path('<int:actividad_id>/editar/', views.editar, name='editar'),
    path('<int:actividad_id>/eliminar/', views.eliminar, name='eliminar'),
    path('evidencias/<int:evidencia_id>/', views.evidencia, name='evidencia'),
    # Versión 2.1: agenda colectiva (RF-016 a RF-021)
    path('agenda/', views_agenda.agenda, name='agenda'),
    path('agenda/nuevo/', views_agenda.compromiso_crear, name='compromiso_crear'),
    path('agenda/<int:pk>/', views_agenda.compromiso_detalle, name='compromiso_detalle'),
    path('agenda/<int:pk>/editar/', views_agenda.compromiso_editar, name='compromiso_editar'),
    path('agenda/<int:pk>/eliminar/', views_agenda.compromiso_eliminar, name='compromiso_eliminar'),
    # Versión 2.1: exportación de informes (RF-033)
    path('exportar/actividades/', exportar.exportar_actividades, name='exportar_actividades'),
    path('exportar/agenda/', exportar.exportar_agenda, name='agenda_exportar'),
    path('exportar/cumplimiento/', exportar.exportar_cumplimiento, name='exportar_cumplimiento'),
    # Tabla maestra Categoría
    path('categorias/', views.CategoriaListado.as_view(), name='categorias'),
    path('categorias/nueva/', views.CategoriaCrear.as_view(), name='categoria_crear'),
    path('categorias/<int:pk>/editar/', views.CategoriaEditar.as_view(), name='categoria_editar'),
    path('categorias/<int:pk>/eliminar/', views.CategoriaEliminar.as_view(), name='categoria_eliminar'),
]
