"""Mantenedores de la versión 3.0. Usan las vistas genéricas de
comun/vistas.py (permisos, mensajes y borrado protegido) y además filtran
por la delegación del usuario."""
from django.http import JsonResponse
from django.contrib.auth.decorators import permission_required

from comun.validadores import normalizar_rut
from comun.vistas import MantenedorCrear, MantenedorEditar, MantenedorEliminar, MantenedorListado
from cuentas.perfiles import delegacion_fija, filtrar_por_delegacion

from .forms import (
    HitoForm, MembresiaForm, SubtipoAtencionForm, TerritorioForm, TipoAtencionForm, VecinoForm,
)
from .models import Hito, MembresiaOrganizacion, SubtipoAtencion, Territorio, TipoAtencion, Vecino


class PorDelegacion:
    campo_delegacion = 'delegacion_id'

    def get_queryset(self):
        return filtrar_por_delegacion(self.request.user, super().get_queryset(), self.campo_delegacion)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['delegacion'] = delegacion_fija(self.request.user)
        return kwargs


def _crud(prefijo, nombre_url):
    return (f'territorio:{nombre_url}_crear', f'territorio:{nombre_url}_editar', f'territorio:{nombre_url}_eliminar')


# ----------------------------------------------------------------- Territorios
class TerritorioConfig(PorDelegacion):
    model, form_class = Territorio, TerritorioForm
    nombre_singular, nombre_plural, url_listado = 'territorio', 'territorios', 'territorio:territorios'


class TerritorioListado(TerritorioConfig, MantenedorListado):
    campos_busqueda = ('nombre', 'descripcion', 'delegacion__nombre')
    columnas = (('Territorio', 'nombre'), ('Delegación', 'delegacion'), ('Descripción', 'descripcion'),
                ('Activo', 'activo'))
    url_crear, url_editar, url_eliminar = _crud('t', 'territorio')
    descripcion = 'Sectores o unidades vecinales de cada delegación.'


class TerritorioCrear(TerritorioConfig, MantenedorCrear):
    pass


class TerritorioEditar(TerritorioConfig, MantenedorEditar):
    pass


class TerritorioEliminar(TerritorioConfig, MantenedorEliminar):
    advertencia = 'Los vecinos e hitos de este territorio quedarán sin territorio asignado.'


# --------------------------------------------------------------------- Vecinos
class VecinoConfig(PorDelegacion):
    model, form_class = Vecino, VecinoForm
    nombre_singular, nombre_plural, url_listado = 'vecino/a', 'vecinos', 'territorio:vecinos'


class VecinoListado(VecinoConfig, MantenedorListado):
    campos_busqueda = ('rut', 'nombre', 'telefono', 'direccion')
    columnas = (('RUT', 'rut'), ('Nombre', 'nombre'), ('Teléfono', 'telefono'), ('Territorio', 'territorio'),
                ('Delegación', 'delegacion'))
    url_crear, url_editar, url_eliminar = _crud('v', 'vecino')
    descripcion = 'Personas atendidas. Se registran una vez y se reutilizan en actividades y gestiones sociales.'

    def get_queryset(self):
        return super().get_queryset().select_related('delegacion', 'territorio')


class VecinoCrear(VecinoConfig, MantenedorCrear):
    pass


class VecinoEditar(VecinoConfig, MantenedorEditar):
    pass


class VecinoEliminar(VecinoConfig, MantenedorEliminar):
    advertencia = 'Si el vecino tiene gestiones sociales registradas no se podrá eliminar.'


@permission_required('territorio.view_vecino', raise_exception=True)
def buscar_vecino(request):
    """Autocompletar (v3.0): devuelve el vecino por RUT o los que coinciden
    con el nombre, solo dentro del ámbito del usuario."""
    consulta = filtrar_por_delegacion(request.user, Vecino.objects.all())
    texto = request.GET.get('q', '').strip()
    resultados = []
    if len(texto) >= 3:
        try:
            exacto = consulta.filter(rut=normalizar_rut(texto))
        except Exception:
            exacto = consulta.none()
        encontrados = exacto if exacto.exists() else consulta.filter(nombre__icontains=texto)[:8]
        resultados = [{'id': v.pk, 'rut': v.rut, 'nombre': v.nombre, 'telefono': v.telefono} for v in encontrados]
    return JsonResponse({'resultados': resultados})


# --------------------------------------------------------- Socios y dirigentes
class MembresiaConfig(PorDelegacion):
    model, form_class = MembresiaOrganizacion, MembresiaForm
    campo_delegacion = 'organizacion__delegacion_id'
    nombre_singular, nombre_plural, url_listado = 'socio o dirigente', 'socios y dirigentes', 'territorio:membresias'


class MembresiaListado(MembresiaConfig, MantenedorListado):
    campos_busqueda = ('vecino__nombre', 'vecino__rut', 'organizacion__nombre')
    columnas = (('Organización', 'organizacion'), ('Vecino/a', 'vecino'), ('Rol', 'rol'), ('Cargo', 'cargo'),
                ('Vigente', 'vigente'))
    url_crear, url_editar, url_eliminar = _crud('m', 'membresia')
    descripcion = 'Membresía y dirigencia en juntas de vecinos y organizaciones comunitarias.'

    def get_queryset(self):
        return super().get_queryset().select_related('vecino', 'organizacion')


class MembresiaCrear(MembresiaConfig, MantenedorCrear):
    pass


class MembresiaEditar(MembresiaConfig, MantenedorEditar):
    pass


class MembresiaEliminar(MembresiaConfig, MantenedorEliminar):
    pass


# ----------------------------------------------------------------------- Hitos
class HitoConfig(PorDelegacion):
    model, form_class = Hito, HitoForm
    nombre_singular, nombre_plural, url_listado = 'hito', 'hitos', 'territorio:hitos'


class HitoListado(HitoConfig, MantenedorListado):
    campos_busqueda = ('nombre', 'descripcion', 'responsable__nombre')
    columnas = (('Fecha', 'fecha'), ('Hito', 'nombre'), ('Responsable', 'responsable'), ('Territorio', 'territorio'),
                ('Estado', 'estado'), ('Delegación', 'delegacion'))
    url_crear, url_editar, url_eliminar = _crud('h', 'hito')
    descripcion = 'Hitos y eventos del territorio, cada uno con un funcionario responsable.'

    def get_queryset(self):
        return super().get_queryset().select_related('delegacion', 'territorio', 'responsable')


class HitoCrear(HitoConfig, MantenedorCrear):
    pass


class HitoEditar(HitoConfig, MantenedorEditar):
    pass


class HitoEliminar(HitoConfig, MantenedorEliminar):
    pass


# --------------------------------------------------- Tipos y subtipos de atención
class TipoConfig:
    model, form_class = TipoAtencion, TipoAtencionForm
    nombre_singular, nombre_plural, url_listado = 'tipo de atención', 'tipos de atención', 'territorio:tipos'


class TipoListado(TipoConfig, MantenedorListado):
    campos_busqueda = ('nombre',)
    columnas = (('Tipo de atención', 'nombre'), ('Activo', 'activo'))
    url_crear, url_editar, url_eliminar = _crud('t', 'tipo')
    descripcion = 'Catálogo de atención social (por ejemplo: informes sociales, subsidios, derivaciones).'


class TipoCrear(TipoConfig, MantenedorCrear):
    pass


class TipoEditar(TipoConfig, MantenedorEditar):
    pass


class TipoEliminar(TipoConfig, MantenedorEliminar):
    advertencia = 'Si el tipo tiene subtipos no se podrá eliminar.'


class SubtipoConfig:
    model, form_class = SubtipoAtencion, SubtipoAtencionForm
    nombre_singular, nombre_plural, url_listado = 'subtipo de atención', 'subtipos de atención', 'territorio:subtipos'


class SubtipoListado(SubtipoConfig, MantenedorListado):
    campos_busqueda = ('nombre', 'tipo__nombre')
    columnas = (('Tipo', 'tipo'), ('Subtipo', 'nombre'), ('Activo', 'activo'))
    url_crear, url_editar, url_eliminar = _crud('s', 'subtipo')

    def get_queryset(self):
        return super().get_queryset().select_related('tipo')


class SubtipoCrear(SubtipoConfig, MantenedorCrear):
    pass


class SubtipoEditar(SubtipoConfig, MantenedorEditar):
    pass


class SubtipoEliminar(SubtipoConfig, MantenedorEliminar):
    advertencia = 'Si el subtipo se usó en gestiones sociales no se podrá eliminar.'
