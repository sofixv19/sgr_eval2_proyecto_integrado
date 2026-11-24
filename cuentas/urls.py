from django.urls import path

from . import views

app_name = 'cuentas'

urlpatterns = [
    path('ingresar/', views.iniciar_sesion, name='login'),
    path('salir/', views.cerrar_sesion, name='logout'),
    # v3.0: cambio obligatorio de la contraseña temporal y recuperación por correo
    path('cambiar-clave/', views.cambiar_clave, name='cambiar_clave'),
    path('recuperar/', views.RecuperarClave.as_view(), name='recuperar'),
    path('recuperar/enviado/', views.RecuperarEnviado.as_view(), name='recuperar_enviado'),
    path('restablecer/<uidb64>/<token>/', views.RestablecerClave.as_view(), name='restablecer'),
    path('restablecer/listo/', views.RestablecerListo.as_view(), name='restablecer_listo'),
]
