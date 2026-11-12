from django.contrib import admin

from .models import Delegacion, OrganizacionComunitaria


@admin.register(Delegacion)
class DelegacionAdmin(admin.ModelAdmin):
    """Administración completa (crear/editar/eliminar/buscar) de Delegacion."""

    list_display = ('nombre', 'encargado', 'telefono', 'email', 'total_actividades')
    search_fields = ('nombre', 'encargado', 'direccion', 'email', 'territorio')
    list_filter = ('territorio',)
    prepopulated_fields = {'slug': ('nombre',)}
    ordering = ('nombre',)

    fieldsets = (
        ('Identificación', {
            'fields': ('nombre', 'slug'),
        }),
        ('Contacto', {
            'fields': ('encargado', 'direccion', 'telefono', 'email'),
        }),
        ('Gestión territorial', {
            'fields': ('territorio', 'enfoque'),
        }),
    )

    @admin.display(description='N° actividades')
    def total_actividades(self, obj):
        return obj.total_actividades


@admin.register(OrganizacionComunitaria)
class OrganizacionComunitariaAdmin(admin.ModelAdmin):
    """Versión 2.0: organizaciones territoriales (JJVV) y funcionales."""
    list_display = ('nombre', 'tipo', 'delegacion', 'socios_activos', 'activa')
    list_filter = ('tipo', 'delegacion', 'activa')
    search_fields = ('nombre', 'domicilio', 'registro_pj')
