from django.contrib import admin

from .models import Delegacion


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
