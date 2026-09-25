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
]
