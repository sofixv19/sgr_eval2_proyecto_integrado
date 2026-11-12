"""
Funciones de apoyo para la app 'gestion', construidas sobre el ORM de
Django (reemplazan a las funciones de agregación que en la Evaluación 1
trabajaban directamente sobre las listas cargadas desde JSON).
"""
from django.db.models import Count

from .models import Actividad

# Mapa entre el valor guardado en el campo 'estado' y la clave interna que
# usan los templates (sin espacios, para poder escribir conteo.en_proceso).
_CLAVES_POR_ESTADO = {
    Actividad.Estado.PENDIENTE: 'pendiente',
    Actividad.Estado.EN_PROCESO: 'en_proceso',
    Actividad.Estado.REALIZADO: 'realizado',
}


def resumen_por_estado(consulta=None):
    """Cuenta, mediante una única consulta ORM agregada (GROUP BY estado),
    cuántas actividades hay en cada estado. Si se entrega una consulta, se
    cuenta solo sobre ella (por ejemplo, las actividades visibles para el
    usuario según su rol)."""
    conteo = {'pendiente': 0, 'en_proceso': 0, 'realizado': 0}

    consulta = Actividad.objects.all() if consulta is None else consulta
    filas = consulta.values('estado').annotate(cantidad=Count('id')).order_by()
    for fila in filas:
        clave = _CLAVES_POR_ESTADO.get(fila['estado'])
        if clave is not None:
            conteo[clave] = fila['cantidad']

    total = sum(conteo.values())
    return conteo, total


def grados_donut(conteo, total):
    """Calcula los puntos de corte (en grados, 0-360) para dibujar el donut
    de estados con conic-gradient, a partir del conteo por estado."""
    if total == 0:
        return {'pendiente': 0, 'en_proceso': 0, 'realizado': 0}

    grado_pendiente = round(conteo['pendiente'] / total * 360)
    grado_en_proceso = grado_pendiente + round(conteo['en_proceso'] / total * 360)
    return {
        'pendiente': grado_pendiente,
        'en_proceso': grado_en_proceso,
        'realizado': 360,
    }
