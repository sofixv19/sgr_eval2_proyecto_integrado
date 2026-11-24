from django.urls import path

from . import dashboard, exportar, views, views_agenda, views_cartas

app_name = 'gestion'

urlpatterns = [
    path('', views.listado, name='listado'),
    path('nueva/', views.crear, name='crear'),
    path('gestion-social/nueva/', views.crear_gestion_social, name='crear_gestion_social'),   # v3.0
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
    # Versión 3.0: dashboard con gráficos y Tubo de cartas
    path('dashboard/', dashboard.dashboard, name='dashboard'),
    path('cartas/', views_cartas.cartas, name='cartas'),
    path('cartas/nueva/', views_cartas.carta_crear, name='carta_crear'),
    path('cartas/<int:pk>/editar/', views_cartas.carta_editar, name='carta_editar'),
    path('cartas/<int:pk>/eliminar/', views_cartas.carta_eliminar, name='carta_eliminar'),
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
