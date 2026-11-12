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
from django.conf import settings
from django.db import models
from django.utils import timezone

from delegaciones.models import Delegacion

from .choices import AREAS, ROLES_SISTEMA


class CargoFuncion(models.Model):
    """Catálogo de cargos/funciones municipales (diseño original: compañero)."""

    nombre_cargo = models.CharField(max_length=100, unique=True, verbose_name='Cargo Municipal')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción de Funciones')
    area = models.CharField(
        max_length=2, choices=AREAS, default='AD', verbose_name='Área',
        help_text='Su sigla se usa para generar el código de las actividades (por ejemplo, TR-0001).',
    )
    active = models.BooleanField(default=True, verbose_name='¿Vigente?')
    creado = models.DateTimeField(default=timezone.now, verbose_name='Fecha de Creación')

    class Meta:
        db_table = 'cargos'
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos y Funciones'
        ordering = ['nombre_cargo']

    def __str__(self):
        return self.nombre_cargo


class Periodo(models.Model):
    """Período de medición de la gestión (por ejemplo, "Segundo semestre 2026").

    Corresponde a la tabla 'periodo' del MER y del script de base de datos
    de la Evaluación 1. Las metas se definen para un cargo y un período
    (regla RN-001: la suma de ponderadores de un cargo en un período no
    puede superar 100 %).
    """

    class Estado(models.TextChoices):
        PLANIFICADO = 'Planificado', 'Planificado'
        ABIERTO = 'Abierto', 'Abierto'
        CERRADO = 'Cerrado', 'Cerrado'

    nombre = models.CharField(max_length=60, unique=True, verbose_name='Nombre del período')
    fecha_inicio = models.DateField(verbose_name='Fecha de inicio')
    fecha_fin = models.DateField(verbose_name='Fecha de término')
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PLANIFICADO, verbose_name='Estado')

    class Meta:
        db_table = 'periodos'
        verbose_name = 'Período'
        verbose_name_plural = 'Períodos de medición'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return self.nombre


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
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='funcionario', verbose_name='Cuenta de acceso',
        help_text='Usuario con el que este funcionario inicia sesión en el sistema.',
    )
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
    # Retroalimentación Eval 2: el Delegado asigna las metas a cada
    # funcionario de su delegación, y cada meta mide una categoría de
    # actividad (el "ítem"), para poder calcular el avance con las
    # actividades validadas.
    funcionario = models.ForeignKey(
        'organizacion.Funcionario', on_delete=models.CASCADE, null=True, blank=True,
        related_name='metas', verbose_name='Funcionario',
    )
    categoria = models.ForeignKey(
        'gestion.Categoria', on_delete=models.PROTECT, null=True, blank=True,
        related_name='metas', verbose_name='Ítem medido (categoría de actividad)',
    )
    periodo = models.ForeignKey(
        Periodo, on_delete=models.PROTECT, null=True, blank=True,
        related_name='metas', verbose_name='Período de medición',
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
        quien = self.funcionario.nombre if self.funcionario_id else self.cargo.nombre_cargo
        return f'{quien} - {self.item_medible}'

    @property
    def valor_numerico(self):
        try:
            return float(str(self.valor_objetivo).replace(',', '.'))
        except ValueError:
            return 0.0
