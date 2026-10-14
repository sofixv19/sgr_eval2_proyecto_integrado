"""
Vistas genéricas para los mantenedores (CRUD) de las tablas maestras.

Cada tabla maestra (Categoría, Cargo, Funcionario, Meta) define solo su
modelo, su formulario y sus columnas; el comportamiento común se escribe una
sola vez aquí:

- exige sesión iniciada y el permiso de Django que corresponde a la acción
  (view / add / change / delete), y responde 403 si el usuario no lo tiene;
- muestra mensajes de éxito o de error con django.contrib.messages;
- no deja eliminar un registro que está en uso por otra tabla
  (ProtectedError / RestrictedError) y lo informa al usuario en vez de
  mostrar un error 500.
"""
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import ProtectedError, Q, RestrictedError
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView


class MantenedorMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """Configuración compartida por las vistas de un mantenedor."""

    accion_permiso = 'view'          # view / add / change / delete
    nombre_singular = 'registro'     # para títulos y mensajes
    nombre_plural = 'registros'
    url_listado = None               # nombre de la URL del listado
    raise_exception = True           # sin permiso -> 403 (no redirige al login)

    def get_permission_required(self):
        opts = self.model._meta
        return [f'{opts.app_label}.{self.accion_permiso}_{opts.model_name}']

    def get_success_url(self):
        return reverse(self.url_listado)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        opts = self.model._meta
        usuario = self.request.user
        contexto.update({
            'nombre_singular': self.nombre_singular,
            'nombre_plural': self.nombre_plural,
            'volver_url': reverse(self.url_listado),
            'puede_agregar': usuario.has_perm(f'{opts.app_label}.add_{opts.model_name}'),
            'puede_editar': usuario.has_perm(f'{opts.app_label}.change_{opts.model_name}'),
            'puede_eliminar': usuario.has_perm(f'{opts.app_label}.delete_{opts.model_name}'),
        })
        return contexto


class MantenedorListado(MantenedorMixin, ListView):
    """Listado con búsqueda (?q=) sobre los campos indicados."""

    template_name = 'comun/mantenedor_listado.html'
    campos_busqueda = ()
    columnas = ()            # tuplas (título, atributo)
    url_crear = url_editar = url_eliminar = url_detalle = None
    descripcion = ''

    def get_queryset(self):
        consulta = super().get_queryset()
        texto = self.request.GET.get('q', '').strip()
        if texto and self.campos_busqueda:
            filtro = Q()
            for campo in self.campos_busqueda:
                filtro |= Q(**{f'{campo}__icontains': texto})
            consulta = consulta.filter(filtro)
        return consulta

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update({
            'titulo_pagina': self.nombre_plural.capitalize(),
            'columnas': self.columnas,
            'query': self.request.GET.get('q', '').strip(),
            'url_crear': self.url_crear,
            'url_editar': self.url_editar,
            'url_eliminar': self.url_eliminar,
            'url_detalle': self.url_detalle,
            'descripcion': self.descripcion,
        })
        return contexto


class MantenedorDetalle(MantenedorMixin, DetailView):
    template_name = 'comun/mantenedor_detalle.html'
    campos_detalle = ()      # tuplas (título, atributo)
    url_editar = url_eliminar = None

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update({
            'titulo_pagina': str(self.object),
            'campos_detalle': self.campos_detalle,
            'url_editar': self.url_editar,
            'url_eliminar': self.url_eliminar,
        })
        return contexto


class MantenedorCrear(MantenedorMixin, CreateView):
    accion_permiso = 'add'
    template_name = 'comun/mantenedor_form.html'

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, f'{self.nombre_singular.capitalize()} "{self.object}" creado/a correctamente.')
        return respuesta

    def form_invalid(self, form):
        messages.error(self.request, 'El formulario tiene errores. Revise los campos marcados en rojo.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['titulo_pagina'] = contexto['accion'] = f'Agregar {self.nombre_singular}'
        return contexto


class MantenedorEditar(MantenedorMixin, UpdateView):
    accion_permiso = 'change'
    template_name = 'comun/mantenedor_form.html'

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, f'{self.nombre_singular.capitalize()} "{self.object}" actualizado/a correctamente.')
        return respuesta

    def form_invalid(self, form):
        messages.error(self.request, 'El formulario tiene errores. Revise los campos marcados en rojo.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['titulo_pagina'] = contexto['accion'] = f'Modificar {self.nombre_singular}: {self.object}'
        return contexto


class MantenedorEliminar(MantenedorMixin, DeleteView):
    accion_permiso = 'delete'
    template_name = 'confirmar_eliminar.html'
    advertencia = ''

    def get_form_class(self):
        # La confirmación de borrado no usa el formulario del mantenedor
        # (que la clase de configuración define para crear/editar).
        return forms.Form

    def form_valid(self, form):
        nombre = str(self.object)
        try:
            self.object.delete()
        except (ProtectedError, RestrictedError):
            messages.error(
                self.request,
                f'No se puede eliminar {self.nombre_singular} "{nombre}" porque tiene registros '
                'asociados en otras tablas. Primero elimine o reasigne esos registros.',
            )
            return redirect(self.get_success_url())
        messages.success(self.request, f'{self.nombre_singular.capitalize()} "{nombre}" eliminado/a correctamente.')
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update({
            'titulo_pagina': f'Eliminar {self.nombre_singular}',
            'accion': f'Eliminar {self.nombre_singular}: {self.object}',
            'objeto': self.object,
            'advertencia': self.advertencia,
        })
        return contexto
