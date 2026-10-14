from django.contrib import admin, messages
from django.utils import timezone

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

    list_display = ('codigo', 'fecha', 'delegacion', 'categoria', 'funcionario', 'estado', 'validado')
    list_filter = ('estado', 'validado', 'categoria', 'delegacion')
    search_fields = (
        'codigo', 'descripcion', 'funcionario__nombre', 'delegacion__nombre',
        'solicitud_problema', 'contacto',
    )
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)
    readonly_fields = ('fecha_validacion',)
    actions = ['marcar_validadas']

    # autocomplete_fields permite navegar/buscar la delegación, la
    # categoría, el funcionario y el delegado validador relacionados
    # directamente desde el formulario de Actividad.
    autocomplete_fields = ('delegacion', 'categoria', 'funcionario', 'validado_por')

    fieldsets = (
        ('Identificación', {
            'fields': ('codigo', 'fecha', 'estado'),
        }),
        ('Relaciones', {
            'fields': ('delegacion', 'categoria', 'funcionario'),
        }),
        ('Detalle', {
            'fields': ('descripcion',),
        }),
        ('Validación del Delegado', {
            'fields': ('validado', 'validado_por', 'fecha_validacion'),
            'description': (
                'El Delegado de la delegación valida la actividad; el Funcionario '
                'que la registró no puede validarse a sí mismo (regla pedida por '
                'el profesor Ciceo tras la retroalimentación de la Evaluación 1).'
            ),
        }),
        ('Solicitud vecinal (opcional)', {
            'fields': ('solicitud_problema', 'contacto', 'telefono_contacto'),
            'classes': ('collapse',),
        }),
    )

    @admin.action(description='Marcar como validadas (requiere Delegado asignado)')
    def marcar_validadas(self, request, queryset):
        validadas, sin_delegado = 0, 0
        for actividad in queryset:
            if actividad.validado_por and actividad.validado_por.rol == 'Delegado':
                actividad.validado = True
                actividad.fecha_validacion = timezone.now()
                actividad.save(update_fields=['validado', 'fecha_validacion'])
                validadas += 1
            else:
                sin_delegado += 1
        if validadas:
            self.message_user(request, f'{validadas} actividad(es) marcadas como validadas.', messages.SUCCESS)
        if sin_delegado:
            self.message_user(
                request,
                f'{sin_delegado} actividad(es) no se validaron: primero asigna un "Validado por" con rol Delegado.',
                messages.WARNING,
            )
