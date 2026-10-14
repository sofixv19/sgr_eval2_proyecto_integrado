"""Filtros de plantilla para mostrar columnas de los mantenedores."""
from django import template

register = template.Library()


@register.filter
def atributo(objeto, ruta):
    """Lee un atributo por nombre, admitiendo rutas con punto
    (por ejemplo 'cargo.nombre_cargo') y campos con opciones
    (usa get_<campo>_display cuando existe). Los booleanos se muestran
    como Sí / No."""
    valor = objeto
    for parte in ruta.split('.'):
        if valor is None:
            return '—'
        mostrar = getattr(valor, f'get_{parte}_display', None)
        valor = mostrar() if callable(mostrar) else getattr(valor, parte, None)
        if callable(valor):
            valor = valor()
    if valor is True:
        return 'Sí'
    if valor is False:
        return 'No'
    if valor in (None, ''):
        return '—'
    return valor
