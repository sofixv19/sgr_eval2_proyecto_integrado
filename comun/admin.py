from django.contrib import admin

from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    """Auditoría de solo lectura (HU-30): nadie puede agregar, modificar ni
    eliminar registros, ni siquiera el Administrador."""
    list_display = ('fecha', 'usuario_texto', 'accion', 'entidad', 'objeto', 'ip')
    list_filter = ('accion', 'entidad')
    search_fields = ('usuario_texto', 'objeto', 'detalle')
    date_hierarchy = 'fecha'
    readonly_fields = [f.name for f in RegistroAuditoria._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
