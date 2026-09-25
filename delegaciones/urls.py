from django.urls import path

from . import views

app_name = 'delegaciones'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('delegaciones/', views.listado, name='listado'),
    path('delegaciones/nueva/', views.crear, name='crear'),
    path('delegaciones/<slug:slug>/', views.detalle, name='detalle'),
    path('delegaciones/<slug:slug>/editar/', views.editar, name='editar'),
    path('delegaciones/<slug:slug>/eliminar/', views.eliminar, name='eliminar'),
]
