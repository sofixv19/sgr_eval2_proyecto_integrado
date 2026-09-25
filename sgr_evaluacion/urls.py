"""
Rutas principales del proyecto SGR - Evaluación 2 (Programación Backend).

Este archivo actúa como punto de entrada: además de Django Admin, no define
vistas propias, solo delega ("include") hacia las rutas de cada aplicación.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('delegaciones.urls')),
    path('gestion/', include('gestion.urls')),
]
