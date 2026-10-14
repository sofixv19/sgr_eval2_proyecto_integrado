from django.contrib import admin

from .models import CargoFuncion, Funcionario, MetaProyecto


class MetaProyectoInline(admin.TabularInline):
    model = MetaProyecto
    extra = 0


@admin.register(CargoFuncion)
class CargoFuncionAdmin(admin.ModelAdmin):
    list_display = ('nombre_cargo', 'active', 'total_funcionarios', 'total_metas')
    list_filter = ('active',)
    search_fields = ('nombre_cargo', 'descripcion')
    ordering = ('nombre_cargo',)
    inlines = [MetaProyectoInline]

    @admin.display(description='N° funcionarios')
    def total_funcionarios(self, obj):
        return obj.funcionarios.count()

    @admin.display(description='N° metas')
    def total_metas(self, obj):
        return obj.metas.count()


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'cargo', 'delegacion', 'rol', 'activo')
    list_filter = ('rol', 'activo', 'cargo', 'delegacion')
    search_fields = ('nombre', 'rut', 'email')
    autocomplete_fields = ('delegacion', 'cargo')
    ordering = ('nombre',)


@admin.register(MetaProyecto)
class MetaProyectoAdmin(admin.ModelAdmin):
    list_display = ('cargo', 'item_medible', 'valor_objetivo', 'unidad', 'ponderador')
    list_filter = ('cargo',)
    search_fields = ('item_medible',)
    autocomplete_fields = ('cargo',)
