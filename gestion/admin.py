from django.contrib import admin

from .models import Actividad, Categoria


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'total_actividades')
    search_fields = ('nombre',)
    ordering = ('nombre',)

    @admin.display(description='N° actividades')
    def total_actividades(self, obj):
        return obj.actividades.count()


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    """Administración completa de Actividad, con navegación hacia sus
    entidades relacionadas (Delegacion y Categoria) mediante autocomplete."""

    list_display = ('codigo', 'fecha', 'delegacion', 'categoria', 'estado')
    list_filter = ('estado', 'categoria', 'delegacion')
    search_fields = ('codigo', 'descripcion', 'funcionario', 'delegacion__nombre')
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)

    # autocomplete_fields permite navegar/buscar la delegación y la
    # categoría relacionadas directamente desde el formulario de Actividad.
    autocomplete_fields = ('delegacion', 'categoria')

    fieldsets = (
        ('Identificación', {
            'fields': ('codigo', 'fecha', 'estado'),
        }),
        ('Relaciones', {
            'fields': ('delegacion', 'categoria'),
        }),
        ('Detalle', {
            'fields': ('descripcion', 'funcionario'),
        }),
    )
