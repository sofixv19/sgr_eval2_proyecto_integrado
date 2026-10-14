"""
Validadores reutilizables del SGR.

Se usan en los formularios de las tablas maestras (Delegación, Categoría,
Cargo, Funcionario y Meta) para que todas las pantallas apliquen las mismas
reglas y los mismos mensajes de error.
"""
import re

from django.core.exceptions import ValidationError

# Letras (incluye tildes y ñ), espacios, punto, guion, apóstrofo y paréntesis.
_PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ .'()\-]+$")
# Teléfono chileno: 9 dígitos, opcionalmente precedidos de +56 o 56.
_PATRON_TELEFONO = re.compile(r'^(\+?56)?\d{9}$')
# RUT: cuerpo de 7 u 8 dígitos (con o sin puntos) + guion opcional + DV.
_PATRON_RUT = re.compile(r'^(\d{1,2}\.?\d{3}\.?\d{3})-?([\dkK])$')


def calcular_dv(cuerpo):
    """Calcula el dígito verificador de un RUT chileno (módulo 11)."""
    suma, multiplicador = 0, 2
    for digito in reversed(str(cuerpo)):
        suma += int(digito) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2
    resto = 11 - (suma % 11)
    if resto == 11:
        return '0'
    if resto == 10:
        return 'K'
    return str(resto)


def normalizar_rut(valor):
    """Devuelve el RUT con formato 12.345.678-5. Lanza ValidationError si
    el formato no es válido o si el dígito verificador no corresponde."""
    texto = (valor or '').strip().replace(' ', '')
    coincidencia = _PATRON_RUT.match(texto)
    if not coincidencia:
        raise ValidationError(
            'Formato de RUT inválido. Use el formato 12.345.678-5.', code='rut_formato',
        )
    cuerpo = coincidencia.group(1).replace('.', '')
    dv = coincidencia.group(2).upper()
    if calcular_dv(cuerpo) != dv:
        raise ValidationError(
            'El dígito verificador del RUT no es correcto.', code='rut_dv',
        )
    cuerpo_con_puntos = f'{int(cuerpo):,}'.replace(',', '.')
    return f'{cuerpo_con_puntos}-{dv}'


def validar_rut(valor):
    """Validador de Django: solo comprueba, no transforma."""
    normalizar_rut(valor)


def validar_telefono(valor):
    """Acepta teléfonos chilenos de 9 dígitos, con o sin +56, y con
    espacios, guiones o paréntesis como separadores."""
    limpio = re.sub(r'[\s\-()]', '', valor or '')
    if not _PATRON_TELEFONO.match(limpio):
        raise ValidationError(
            'Teléfono inválido. Debe tener 9 dígitos (por ejemplo 512 206518 o +56 9 1234 5678).',
            code='telefono',
        )


def validar_nombre(valor, minimo=3, campo='nombre'):
    """Nombres de personas o catálogos: solo letras y signos básicos, sin
    números ni símbolos, con un largo mínimo."""
    texto = (valor or '').strip()
    if len(texto) < minimo:
        raise ValidationError(
            f'El {campo} debe tener al menos {minimo} caracteres.', code='largo_minimo',
        )
    if not _PATRON_NOMBRE.match(texto):
        raise ValidationError(
            f'El {campo} solo puede contener letras, espacios y los signos . - \' ( ).',
            code='caracteres',
        )
    return re.sub(r'\s+', ' ', texto)


def validar_texto_minimo(valor, minimo=3, campo='texto'):
    """Texto libre obligatorio con un largo mínimo (sin solo espacios)."""
    texto = re.sub(r'\s+', ' ', (valor or '').strip())
    if len(texto) < minimo:
        raise ValidationError(
            f'El {campo} debe tener al menos {minimo} caracteres.', code='largo_minimo',
        )
    return texto


def nombre_repetido(queryset, campo, valor, excluir_pk=None):
    """True si en el queryset ya existe otro registro con el mismo texto en
    'campo', sin distinguir mayúsculas ni tildes en mayúscula (casefold).
    Se compara en Python para que funcione igual en SQLite y en MariaDB."""
    buscado = (valor or '').strip().casefold()
    otros = queryset.exclude(pk=excluir_pk) if excluir_pk else queryset
    return any((texto or '').strip().casefold() == buscado for texto in otros.values_list(campo, flat=True))
