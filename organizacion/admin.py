from django.contrib import admin

from .models import Ausencia, CargoFuncion, Funcionario, MetaProyecto, Periodo, Reconocimiento


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


@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_inicio', 'fecha_fin', 'estado')
    list_filter = ('estado',)
    search_fields = ('nombre',)


@admin.register(Reconocimiento)
class ReconocimientoAdmin(admin.ModelAdmin):
    """Versión 2.0: felicitaciones (+10) y reclamos (−20) registrados por el Delegado."""
    list_display = ('fecha', 'tipo', 'funcionario', 'periodo', 'respaldo', 'registrado_por')
    list_filter = ('tipo', 'periodo', 'respaldo')
    search_fields = ('funcionario__nombre', 'detalle')


@admin.register(Ausencia)
class AusenciaAdmin(admin.ModelAdmin):
    """Versión 2.0: ausencias que ajustan la meta esperada en el semáforo."""
    list_display = ('funcionario', 'tipo', 'desde', 'hasta', 'dias', 'registrado_por')
    list_filter = ('tipo',)
    search_fields = ('funcionario__nombre', 'observacion')
