"""
Pruebas de la versión 2.0 — Nuevos requerimientos (octubre 2026).

Cada caso indica el requisito de REQUISITOS_V2.md que verifica:
RF-039 organizaciones comunitarias, RF-040 a RF-044 reglas de registro y
puntaje, RF-045 tope por ítem, RF-046 felicitaciones y reclamos, RF-047
ausencias y RF-048 versión de reglas por actividad.
"""
import datetime

from django.test import override_settings
from django.urls import reverse

from comun.pruebas import MEDIA_PRUEBAS
from delegaciones.forms import OrganizacionForm
from delegaciones.models import OrganizacionComunitaria
from organizacion.forms import AusenciaForm, ReconocimientoForm
from organizacion.models import Ausencia, MetaProyecto, Reconocimiento

from .forms import ActividadForm, inicio_ventana_registro
from .indicadores import cumplimiento_funcionario, porcentaje_esperado_funcionario
from .models import Actividad
from .tests_roles import HOY, EscenarioBase


@override_settings(MEDIA_ROOT=MEDIA_PRUEBAS)
class ReglasDePuntajeTests(EscenarioBase):
    """Unidades: Actividad.actualizar_puntaje() y ActividadForm (RF-040 a RF-044)."""

    def test_cp_v2_001_solicitante_delegado_no_suma(self):
        """CP-V2-001: RF-040. Si el solicitante es el propio Delegado, la actividad no suma puntaje."""
        actividad = self._actividad(self.ana, tipo_solicitante=Actividad.TipoSolicitante.DELEGADO)
        self.assertFalse(actividad.puntuable)
        self.assertIn('propio Delegado', actividad.motivo_sin_puntaje)

    def test_cp_v2_002_sin_nombre_o_telefono_no_suma(self):
        """CP-V2-002: RF-041. Sin nombre o teléfono del usuario la actividad no suma; con ambos, sí."""
        sin_telefono = self._actividad(self.ana, telefono_contacto='')
        sin_nombre = self._actividad(self.ana, contacto='')
        completa = self._actividad(self.ana)
        self.assertEqual([sin_telefono.puntuable, sin_nombre.puntuable, completa.puntuable], [False, False, True])
        self.assertIn('teléfono', sin_telefono.motivo_sin_puntaje)

    def test_cp_v2_003_gestion_previa_no_suma_aunque_este_validada(self):
        """CP-V2-003: RF-044. Una gestión previa validada no suma al avance; la realización sí."""
        MetaProyecto.objects.create(cargo=self.ana.cargo, funcionario=self.ana, periodo=self.periodo,
                                    categoria=self.categoria, item_medible='Meta', valor_objetivo='2', ponderador=100)
        self._actividad(self.ana, tipo_gestion=Actividad.TipoGestion.PREVIA).marcar_validado(self.delegado_rural)
        self._actividad(self.ana).marcar_validado(self.delegado_rural)
        resultado = cumplimiento_funcionario(self.ana, self.periodo)
        self.assertEqual((resultado.filas[0].avance, resultado.cumplimiento), (1, 50.0))

    def test_cp_v2_004_maximo_siete_ingresos_diarios(self):
        """CP-V2-004: RF-042. Con 7 actividades ingresadas hoy, el formulario rechaza la octava."""
        for _ in range(7):
            self._actividad(self.ana)
        form = ActividadForm(data={'fecha': HOY.isoformat(), 'categoria': self.categoria.pk,
                                   'descripcion': 'Octava del día'}, funcionario=self.ana)
        self.assertFalse(form.is_valid())
        self.assertIn('máximo diario', str(form.non_field_errors()))

    def test_cp_v2_005_cierre_semanal(self):
        """CP-V2-005: RF-043. El lunes aún se ingresa la semana anterior; desde el martes, solo la semana en curso."""
        lunes = datetime.date(2026, 11, 9)
        martes = datetime.date(2026, 11, 10)
        domingo = datetime.date(2026, 11, 15)
        self.assertEqual(inicio_ventana_registro(lunes), datetime.date(2026, 11, 2))
        self.assertEqual(inicio_ventana_registro(martes), datetime.date(2026, 11, 9))
        self.assertEqual(inicio_ventana_registro(domingo), datetime.date(2026, 11, 9))

    def test_cp_v2_006_organizacion_obligatoria_si_la_solicita_una_organizacion(self):
        """CP-V2-006: RF-039. Si el solicitante es una organización, hay que indicar cuál."""
        datos = {'fecha': HOY.isoformat(), 'categoria': self.categoria.pk, 'descripcion': 'Taller',
                 'tipo_solicitante': Actividad.TipoSolicitante.ORGANIZACION}
        form = ActividadForm(data=datos, funcionario=self.ana)
        self.assertFalse(form.is_valid())
        self.assertIn('organizacion', form.errors)
        organizacion = OrganizacionComunitaria.objects.create(
            nombre='Club de Adulto Mayor Las Rosas', tipo=OrganizacionComunitaria.Tipo.ADULTO_MAYOR,
            delegacion=self.rural)
        form = ActividadForm(data={**datos, 'organizacion': organizacion.pk}, funcionario=self.ana)
        self.assertTrue(form.is_valid(), form.errors)

    def test_cp_v2_007_actividades_v1_conservan_su_puntaje(self):
        """CP-V2-007: RF-048. Las actividades registradas con reglas 1.0 no pierden puntaje por las reglas 2.0."""
        antigua = self._actividad(self.ana, contacto='', telefono_contacto='', version_reglas='1.0')
        nueva = self._actividad(self.ana, contacto='', telefono_contacto='')
        self.assertTrue(antigua.puntuable)
        self.assertEqual(nueva.version_reglas, '2.0')
        self.assertFalse(nueva.puntuable)


class CumplimientoV2Tests(EscenarioBase):
    """Unidades: gestion/indicadores.py con las reglas 2.0 (RF-045 a RF-047)."""

    def _meta(self, objetivo, ponderador=100):
        return MetaProyecto.objects.create(
            cargo=self.ana.cargo, funcionario=self.ana, periodo=self.periodo, categoria=self.categoria,
            item_medible='Meta', valor_objetivo=str(objetivo), ponderador=ponderador)

    def _validadas(self, cantidad):
        for _ in range(cantidad):
            self._actividad(self.ana).marcar_validado(self.delegado_rural)

    def _reconocimiento(self, tipo):
        return Reconocimiento.objects.create(
            funcionario=self.ana, periodo=self.periodo, tipo=tipo, fecha=HOY,
            respaldo=Reconocimiento.Respaldo.CORREO, detalle='Respaldo formal recibido por el Delegado.',
            registrado_por=self.delegado_rural)

    def test_cp_v2_008_tope_120_por_item(self):
        """CP-V2-008: RF-045. Pasado el 120 % de un ítem, más actividades no suben el puntaje."""
        self._meta(2)
        self._validadas(4)   # 200 %
        self.assertEqual(cumplimiento_funcionario(self.ana, self.periodo).filas[0].cumplimiento, 120.0)

    def test_cp_v2_009_felicitaciones_y_reclamos(self):
        """CP-V2-009: RF-046. Cada felicitación suma 10 y cada reclamo resta 20 al cumplimiento ponderado."""
        self._meta(4)
        self._validadas(2)   # 50 %
        self._reconocimiento(Reconocimiento.Tipo.FELICITACION)
        self._reconocimiento(Reconocimiento.Tipo.FELICITACION)
        self._reconocimiento(Reconocimiento.Tipo.RECLAMO)
        resultado = cumplimiento_funcionario(self.ana, self.periodo)
        self.assertEqual((resultado.base, resultado.ajuste, resultado.cumplimiento), (50.0, 0, 50.0))

    def test_cp_v2_010_total_entre_0_y_150(self):
        """CP-V2-010: RF-046. Con felicitaciones el total no supera 150 %, y con reclamos no baja de 0 %."""
        self._meta(2)
        self._validadas(3)   # 120 % (tope por ítem)
        for _ in range(3):
            self._reconocimiento(Reconocimiento.Tipo.FELICITACION)
        self.assertEqual(cumplimiento_funcionario(self.ana, self.periodo).cumplimiento, 150.0)
        Reconocimiento.objects.all().delete()
        Actividad.objects.all().delete()
        self._reconocimiento(Reconocimiento.Tipo.RECLAMO)
        self.assertEqual(cumplimiento_funcionario(self.ana, self.periodo).cumplimiento, 0.0)

    def test_cp_v2_011_ausencias_ajustan_la_meta_esperada(self):
        """CP-V2-011: RF-047. Los días de ausencia se descuentan del período al calcular la meta esperada."""
        # Período de prueba: HOY-30 a HOY+30 (61 días), van 31 días transcurridos.
        sin_ausencia = porcentaje_esperado_funcionario(self.ana, self.periodo, HOY)
        Ausencia.objects.create(funcionario=self.ana, tipo=Ausencia.Tipo.LICENCIA,
                                desde=HOY - datetime.timedelta(days=20), hasta=HOY - datetime.timedelta(days=11))
        con_ausencia = porcentaje_esperado_funcionario(self.ana, self.periodo, HOY)
        self.assertEqual(sin_ausencia, round(31 / 61 * 100, 1))
        self.assertEqual(con_ausencia, round((31 - 10) / (61 - 10) * 100, 1))
        self.assertEqual(cumplimiento_funcionario(self.ana, self.periodo, HOY).dias_ausencia, 10)


class FormulariosV2Tests(EscenarioBase):
    """Unidades e integración: felicitaciones, ausencias y organizaciones (RF-039, RF-046, RF-047)."""

    def test_cp_v2_012_maximo_tres_felicitaciones(self):
        """CP-V2-012: RF-046. No se registran más de 3 felicitaciones por funcionario en el período."""
        for _ in range(3):
            Reconocimiento.objects.create(funcionario=self.ana, periodo=self.periodo, tipo='Felicitacion', fecha=HOY,
                                          respaldo='Correo', detalle='Felicitación con respaldo formal.')
        form = ReconocimientoForm(data={'funcionario': self.ana.pk, 'periodo': self.periodo.pk, 'tipo': 'Felicitacion',
                                        'fecha': HOY.isoformat(), 'respaldo': 'Libro',
                                        'detalle': 'Cuarta felicitación del período.'})
        self.assertFalse(form.is_valid())

    def test_cp_v2_013_solo_el_delegado_registra_felicitaciones(self):
        """CP-V2-013: RF-046. El Delegado registra la felicitación (queda como autor); el Funcionario no puede (403)."""
        self.entrar(self.ana)
        self.assertEqual(self.client.get(reverse('organizacion:reconocimiento_crear')).status_code, 403)
        self.entrar(self.delegado_rural)
        respuesta = self.client.post(reverse('organizacion:reconocimiento_crear'), {
            'funcionario': self.ana.pk, 'periodo': self.periodo.pk, 'tipo': 'Felicitacion',
            'fecha': HOY.isoformat(), 'respaldo': 'Correo', 'detalle': 'Vecina felicita por correo al Delegado.'})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Reconocimiento.objects.get().registrado_por, self.delegado_rural)

    def test_cp_v2_014_delegado_solo_elige_a_su_equipo(self):
        """CP-V2-014: RF-046/RF-047. El Delegado de Rural no puede registrar ausencias de un funcionario de Centro."""
        self.entrar(self.delegado_rural)
        respuesta = self.client.get(reverse('organizacion:ausencia_crear'))
        opciones = respuesta.context['form'].fields['funcionario'].queryset
        self.assertIn(self.ana, opciones)
        self.assertNotIn(self.pedro, opciones)

    def test_cp_v2_015_ausencias_no_se_cruzan(self):
        """CP-V2-015: RF-047. Una ausencia no puede terminar antes de empezar ni cruzarse con otra del mismo funcionario."""
        Ausencia.objects.create(funcionario=self.ana, tipo='Vacaciones', desde=HOY, hasta=HOY + datetime.timedelta(days=4))
        al_reves = AusenciaForm(data={'funcionario': self.ana.pk, 'tipo': 'Libre', 'desde': HOY.isoformat(),
                                      'hasta': (HOY - datetime.timedelta(days=1)).isoformat()})
        cruzada = AusenciaForm(data={'funcionario': self.ana.pk, 'tipo': 'Libre',
                                     'desde': (HOY + datetime.timedelta(days=2)).isoformat(),
                                     'hasta': (HOY + datetime.timedelta(days=6)).isoformat()})
        self.assertFalse(al_reves.is_valid())
        self.assertFalse(cruzada.is_valid())

    def test_cp_v2_016_organizaciones_por_delegacion(self):
        """CP-V2-016: RF-039. El Delegado crea organizaciones solo en su delegación y distingue territoriales de funcionales."""
        form = OrganizacionForm(data={'nombre': 'Centro de Madres Las Violetas', 'tipo': 'CENTRO_MADRES',
                                      'activa': 'on'}, delegacion=self.rural)
        self.assertTrue(form.is_valid(), form.errors)
        organizacion = form.save()
        self.assertEqual((organizacion.delegacion, organizacion.clase), (self.rural, 'Funcional'))
        jjvv = OrganizacionComunitaria.objects.create(nombre='JJVV Villa Alegre', delegacion=self.centro)
        self.assertEqual(jjvv.clase, 'Territorial')
        self.entrar(self.delegado_rural)
        listado = self.client.get(reverse('delegaciones:organizaciones'))
        self.assertContains(listado, 'Centro de Madres Las Violetas')
        self.assertNotContains(listado, 'JJVV Villa Alegre')
