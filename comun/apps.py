from django.apps import AppConfig


class ComunConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'comun'
    verbose_name = 'Componentes comunes y auditoría'

    def ready(self):
        from .auditoria import conectar_senales
        conectar_senales()
