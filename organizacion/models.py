"""
Modelos de la app 'organizacion'.

Esta app nace de FUSIONAR en un solo proyecto el trabajo que cada
integrante hizo por separado en el ramo de Alex (Programación Back End):

- CargoFuncion y MetaProyecto: tal como los diseñó el compañero de equipo
  en su app 'gestionCargosApp' (se mantienen sus nombres de modelo y de
  tabla originales).
- Funcionario: el compañero lo había modelado en 'registroActividadesApp'
  junto a una Delegacion propia; aquí se mantiene su diseño de Funcionario
  pero apuntando a la ÚNICA Delegacion del proyecto (la de la app
  'delegaciones', ya con slug/territorio/enfoque), para no tener dos
  tablas de delegaciones distintas en el proyecto fusionado.

Con esto, 'Actividad' (en la app 'gestion') puede referenciar a un
Funcionario real en vez de un simple texto libre, que era la limitación
original del proyecto de Sofía.
"""
from django.db import models
from django.utils import timezone

from delegaciones.models import Delegacion

from .choices import ROLES_SISTEMA


class CargoFuncion(models.Model):
    """Catálogo de cargos/funciones municipales (diseño original: compañero)."""

    nombre_cargo = models.CharField(max_length=100, unique=True, verbose_name='Cargo Municipal')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción de Funciones')
    active = models.BooleanField(default=True, verbose_name='¿Vigente?')
    creado = models.DateTimeField(default=timezone.now, verbose_name='Fecha de Creación')

    class Meta:
        db_table = 'cargos'
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos y Funciones'
        ordering = ['nombre_cargo']

    def __str__(self):
        return self.nombre_cargo


class Funcionario(models.Model):
    """Funcionario municipal, asociado a una delegación y a un cargo."""

    delegacion = models.ForeignKey(
        Delegacion, on_delete=models.RESTRICT,
        related_name='funcionarios', verbose_name='Delegación Asignada',
    )
    cargo = models.ForeignKey(
        CargoFuncion, on_delete=models.RESTRICT,
        related_name='funcionarios', verbose_name='Cargo Ocupado',
    )
    nombre = models.CharField(max_length=100, verbose_name='Nombre Completo')
    rut = models.CharField(max_length=12, unique=True, verbose_name='RUT')
    email = models.EmailField(max_length=100, unique=True, verbose_name='Correo Electrónico')
    rol = models.CharField(
        max_length=50, choices=ROLES_SISTEMA, default='Funcionario',
        verbose_name='Rol del Sistema',
    )
    activo = models.BooleanField(default=True, verbose_name='¿Funcionario Activo?')
    creado = models.DateTimeField(default=timezone.now, verbose_name='Fecha de Creación')

    class Meta:
        db_table = 'funcionarios'
        verbose_name = 'Funcionario'
        verbose_name_plural = 'Funcionarios'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.cargo.nombre_cargo})'


class MetaProyecto(models.Model):
    """Meta institucional asignada a un cargo (diseño original: compañero).

    Conceptualmente equivalente a la entidad "Meta" del MER de la
    Evaluación 1 de Caiceo: un objetivo medible, con su ponderador, que
    luego se cruza con el cumplimiento real de cada funcionario.
    """

    cargo = models.ForeignKey(
        CargoFuncion, on_delete=models.CASCADE,
        related_name='metas', verbose_name='Cargo Relacionado',
    )
    item_medible = models.CharField(max_length=100, verbose_name='Ítem / Nombre de la Meta')
    valor_objetivo = models.CharField(max_length=255, verbose_name='Meta Asignada (Valor Objetivo)')
    unidad = models.CharField(max_length=50, default='Porcentaje', verbose_name='Unidad de Medida')
    ponderador = models.IntegerField(default=0, verbose_name='Ponderación Total (%)')
    creado = models.DateTimeField(default=timezone.now, verbose_name='Fecha de Registro')

    class Meta:
        db_table = 'metas'
        verbose_name = 'Meta'
        verbose_name_plural = 'Metas Institucionales'
        ordering = ['cargo', 'item_medible']

    def __str__(self):
        return f'{self.cargo.nombre_cargo} - {self.item_medible}'
