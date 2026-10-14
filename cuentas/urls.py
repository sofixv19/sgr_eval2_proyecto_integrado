from django.urls import path

from . import views

app_name = 'cuentas'

urlpatterns = [
    path('ingresar/', views.iniciar_sesion, name='login'),
    path('salir/', views.cerrar_sesion, name='logout'),
]
