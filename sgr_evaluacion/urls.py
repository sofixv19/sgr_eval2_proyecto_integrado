"""
Rutas principales del proyecto SGR - Evaluación 2 (Programación Backend).

Este archivo actúa como punto de entrada: además de Django Admin, no define
vistas propias, solo delega ("include") hacia las rutas de cada aplicación.
"""
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'SGR La Serena — Administración'
admin.site.site_title = 'SGR La Serena'
admin.site.index_title = 'Panel de administración (acceso restringido)'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cuentas/', include('cuentas.urls')),
    path('', include('delegaciones.urls')),
    path('gestion/', include('gestion.urls')),
    path('organizacion/', include('organizacion.urls')),
    path('auditoria/', include('comun.urls')),   # v2.1: auditoría (RF-036)
]
