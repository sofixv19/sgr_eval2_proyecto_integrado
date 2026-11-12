"""
Pruebas de la versión 2.1 — alcance mínimo de la Guía SGR (sección 13.2):
agenda colectiva (CP-AGE), auditoría (CP-AUD), exportación (CP-EXP),
períodos cerrados (CP-PCE), filtros (CP-FIL) y alertas/actividad reciente
(CP-ALE).
"""
import datetime

from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse

from comun.models import RegistroAuditoria
from organizacion.models import Periodo

from .alertas import actividad_reciente, alertas_delegacion
from .forms import ActividadForm, CompromisoForm
from .indicadores import cumplimiento_delegacion
from .models import Actividad, Compromiso
from .tests_roles import HOY, EscenarioBase


class AgendaColectivaTests(EscenarioBase):
    """RF-016 a RF-021, HU-12 a HU-15."""

    def _compromiso(self, responsable=None, dias=5, **extra):
        responsable = responsable or self.ana
        datos = dict(delegacion=responsable.delegacion, solicitante='JJVV Villa Alegre', territorio='Sector alto',
                     descripcion='Poda de árboles en la plaza', responsable=responsable,
                     fecha_compromiso=HOY + datetime.timedelta(days=dias))
        datos.update(extra)
        return Compromiso.objects.create(**datos)

    def test_cp_age_001_codigo_y_visibilidad_por_delegacion(self):
        """CP-AGE-001: RF-016. El compromiso recibe código AC-0001 y lo ve todo el equipo de su delegación, no otra."""
        compromiso = self._compromiso()
        self.assertEqual(compromiso.codigo, 'AC-0001')
        self.entrar(self.luis)   # compañero de Rural
        self.assertContains(self.client.get(reverse('gestion:agenda')), 'AC-0001')
        self.entrar(self.pedro)  # funcionario de Centro
        self.assertNotContains(self.client.get(reverse('gestion:agenda')), 'AC-0001')
        self.assertEqual(self.client.get(reverse('gestion:compromiso_detalle', args=[compromiso.pk])).status_code, 404)

    def test_cp_age_002_responsable_y_fecha_obligatorios(self):
        """CP-AGE-002: RF-017. No se guarda sin responsable ni fecha comprometida, ni con fecha anterior a la solicitud."""
        base = {'origen': 'EXT', 'solicitante': 'Vecina Rosa', 'territorio': 'Centro', 'descripcion': 'Luminaria',
                'fecha_solicitud': HOY.isoformat()}
        form = CompromisoForm(data=base, delegacion=self.rural)
        self.assertFalse(form.is_valid())
        self.assertIn('responsable', form.errors)
        self.assertIn('fecha_compromiso', form.errors)
        form = CompromisoForm(data={**base, 'responsable': self.ana.pk,
                                    'fecha_compromiso': (HOY - datetime.timedelta(days=1)).isoformat()},
                              delegacion=self.rural)
        self.assertFalse(form.is_valid())
        form = CompromisoForm(data={**base, 'responsable': self.ana.pk, 'fecha_compromiso': HOY.isoformat()},
                              delegacion=self.rural)
        self.assertTrue(form.is_valid(), form.errors)

    def test_cp_age_003_transiciones_e_historial(self):
        """CP-AGE-003: RF-018. Cada cambio de estado guarda estado anterior, nuevo, autor, fecha y observación."""
        compromiso = self._compromiso()
        compromiso.cambiar_estado('En proceso', self.ana.usuario, 'Se coordinó con Aseo y Ornato')
        cambio = compromiso.cambios.get()
        esperado = ('Ingresado', 'En proceso', self.ana.usuario)
        self.assertEqual((cambio.valor_anterior, cambio.valor_nuevo, cambio.autor), esperado)
        with self.assertRaises(ValidationError):
            compromiso.cambiar_estado('Ingresado', self.ana.usuario, 'volver atrás')   # transición no permitida
        with self.assertRaises(ValidationError):
            compromiso.cambiar_estado('Realizado', self.ana.usuario, '')               # sin observación
        compromiso.cambiar_estado('Realizado', self.ana.usuario, 'Poda realizada')
        self.assertEqual(compromiso.fecha_cierre, HOY)
        self.assertEqual(compromiso.estados_siguientes(puede_reabrir=False), [])      # solo el Delegado reabre

    def test_cp_age_004_vencidos_y_proximos(self):
        """CP-AGE-004: RF-019. Se distinguen vencidos, próximos a vencer y realizados fuera de plazo."""
        vencido = self._compromiso(dias=-2)
        proximo = self._compromiso(dias=1)
        lejano = self._compromiso(dias=20)
        self.assertTrue(vencido.vencido and not vencido.proximo_a_vencer)
        self.assertTrue(proximo.proximo_a_vencer and not proximo.vencido)
        self.assertFalse(lejano.vencido or lejano.proximo_a_vencer)
        vencido.cambiar_estado('Realizado', self.ana.usuario, 'Se hizo tarde')
        self.assertTrue(vencido.fuera_de_plazo)
        self.entrar(self.ana)
        respuesta = self.client.get(reverse('gestion:agenda') + '?situacion=vencidos')
        self.assertEqual([c.pk for c in respuesta.context['compromisos']], [])
        self._compromiso(dias=-1)
        respuesta = self.client.get(reverse('gestion:agenda') + '?situacion=vencidos')
        self.assertEqual(len(respuesta.context['compromisos']), 1)

    def test_cp_age_005_resumen_colectivo_coincide_con_detalle(self):
        """CP-AGE-005: RF-021. El resumen por responsable totaliza por estado y su total coincide con la lista filtrada."""
        self._compromiso()
        hecho = self._compromiso()
        hecho.cambiar_estado('Realizado', self.ana.usuario, 'Listo')
        self._compromiso(responsable=self.luis)
        self.entrar(self.delegado_rural)
        respuesta = self.client.get(reverse('gestion:agenda'))
        resumen = {f['responsable'].pk: f for f in respuesta.context['resumen']}
        self.assertEqual((resumen[self.ana.pk]['total'], resumen[self.ana.pk]['pct_realizado']), (2, 50.0))
        self.assertEqual(sum(f['total'] for f in respuesta.context['resumen']), respuesta.context['total'])

    def test_cp_age_006_reasignacion_solo_delegado(self):
        """CP-AGE-006: HU-15. El Delegado reasigna con motivo y queda en el historial; un funcionario no puede."""
        compromiso = self._compromiso()
        self.entrar(self.luis)
        respuesta = self.client.post(reverse('gestion:compromiso_detalle', args=[compromiso.pk]),
                                     {'accion': 'reasignar', 'responsable': self.luis.pk, 'motivo': 'x'})
        self.assertEqual(respuesta.status_code, 403)
        self.entrar(self.delegado_rural)
        self.client.post(reverse('gestion:compromiso_detalle', args=[compromiso.pk]),
                         {'accion': 'reasignar', 'responsable': self.luis.pk, 'motivo': 'Licencia médica'})
        compromiso.refresh_from_db()
        self.assertEqual(compromiso.responsable, self.luis)
        self.assertEqual(compromiso.cambios.get().observacion, 'Licencia médica')

    def test_cp_age_007_actividad_cumple_compromiso_una_vez(self):
        """CP-AGE-007: RF-020. La actividad que cumple un compromiso lo cierra, y el compromiso no admite una segunda."""
        compromiso = self._compromiso()
        self.entrar(self.ana)
        self.client.post(reverse('gestion:crear'), {
            'compromiso': compromiso.pk, 'fecha': HOY.isoformat(), 'categoria': self.categoria.pk,
            'descripcion': 'Poda realizada', 'contacto': 'JJVV Villa Alegre', 'telefono_contacto': '+56 9 1234 5678'})
        compromiso.refresh_from_db()
        self.assertEqual(compromiso.estado, 'Realizado')
        self.assertEqual(compromiso.actividades.count(), 1)
        respuesta = self.client.get(reverse('gestion:crear') + f'?compromiso={compromiso.pk}')
        self.assertIsNone(respuesta.context['compromiso'])


class AuditoriaTests(EscenarioBase):
    """RF-036, HU-30, CA-09."""

    def test_cp_aud_001_registra_valor_anterior_y_nuevo(self):
        """CP-AUD-001: Al modificar un registro queda usuario, acción, entidad, valor anterior y valor nuevo."""
        self.entrar(self.delegado_rural)
        self.client.post(reverse('organizacion:ausencia_crear'), {
            'funcionario': self.ana.pk, 'tipo': 'Vacaciones', 'desde': HOY.isoformat(), 'hasta': HOY.isoformat()})
        alta = RegistroAuditoria.objects.filter(accion='Alta', entidad='Ausencia').get()
        self.assertEqual(alta.usuario, self.delegado_rural.usuario)
        actividad = self._actividad(self.ana, descripcion='Texto original')
        actividad.descripcion = 'Texto corregido'
        actividad.save()
        cambio = RegistroAuditoria.objects.filter(accion='Modificación', objeto_id=str(actividad.pk),
                                                  entidad='Actividad').get()
        self.assertEqual(cambio.cambios['Descripción'], ['Texto original', 'Texto corregido'])

    def test_cp_aud_002_validacion_y_rechazo_quedan_registrados(self):
        """CP-AUD-002: La validación y el rechazo de una actividad se registran como tales."""
        actividad = self._actividad(self.ana)
        actividad.rechazar(self.delegado_rural, 'Foto borrosa')
        actividad.marcar_validado(self.delegado_rural)
        acciones = list(RegistroAuditoria.objects.filter(objeto_id=str(actividad.pk), entidad='Actividad')
                        .values_list('accion', flat=True))
        self.assertIn('Rechazo', acciones)
        self.assertIn('Validación', acciones)

    def test_cp_aud_003_historial_inalterable_y_acceso_restringido(self):
        """CP-AUD-003: El historial no se puede modificar ni eliminar, y un Funcionario no puede consultarlo (403)."""
        self._actividad(self.ana)
        registro = RegistroAuditoria.objects.first()
        registro.detalle = 'manipulado'
        with self.assertRaises(PermissionDenied):
            registro.save()
        with self.assertRaises(PermissionDenied):
            registro.delete()
        self.entrar(self.ana)
        self.assertEqual(self.client.get(reverse('comun:auditoria')).status_code, 403)
        self.client.force_login(self.coordinador)
        self.assertEqual(self.client.get(reverse('comun:auditoria')).status_code, 200)

    def test_cp_aud_004_acceso_denegado_se_registra(self):
        """CP-AUD-004: HU-26. Un intento de acceso fuera de su ámbito se deniega y queda registrado."""
        self.entrar(self.ana)
        self.client.get(reverse('comun:auditoria'))
        evento = RegistroAuditoria.objects.filter(accion='Acceso denegado').get()
        self.assertIn('/auditoria/', evento.detalle)
        self.assertEqual(evento.usuario, self.ana.usuario)


class ExportacionTests(EscenarioBase):
    """RF-033, HU-20."""

    def test_cp_exp_001_actividades_respeta_ambito_y_filtros(self):
        """CP-EXP-001: El CSV de actividades trae encabezados, fecha y filtros, y solo las actividades del ámbito."""
        propia = self._actividad(self.ana)
        ajena = self._actividad(self.pedro)
        self.entrar(self.delegado_rural)
        respuesta = self.client.get(reverse('gestion:exportar_actividades') + '?estado=Pendiente')
        contenido = respuesta.content.decode('utf-8-sig')
        self.assertEqual(respuesta['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('Generado el', contenido)
        self.assertIn('estado=Pendiente', contenido)
        self.assertIn(propia.codigo, contenido)
        self.assertNotIn(ajena.codigo, contenido)

    def test_cp_exp_002_cumplimiento_y_agenda(self):
        """CP-EXP-002: Se exportan el cumplimiento por funcionario (con fórmula) y la agenda colectiva."""
        Compromiso.objects.create(delegacion=self.rural, solicitante='Vecino', territorio='Alto', descripcion='Bache',
                                  responsable=self.ana, fecha_compromiso=HOY)
        self.client.force_login(self.coordinador)
        cumplimiento = self.client.get(reverse('gestion:exportar_cumplimiento')).content.decode('utf-8-sig')
        self.assertIn('avance/meta x 100', cumplimiento)
        self.assertIn('Ana Rojas', cumplimiento)
        agenda = self.client.get(reverse('gestion:agenda_exportar')).content.decode('utf-8-sig')
        self.assertIn('AC-0001', agenda)


class PeriodoCerradoTests(EscenarioBase):
    """RN-013, CA-10."""

    def test_cp_pce_001_actividad_de_periodo_cerrado_no_se_altera(self):
        """CP-PCE-001: En un período cerrado no se registran actividades ni se editan, eliminan o validan las existentes."""
        actividad = self._actividad(self.ana)
        self.periodo.estado = Periodo.Estado.CERRADO
        self.periodo.save()
        form = ActividadForm(data={'fecha': HOY.isoformat(), 'categoria': self.categoria.pk,
                                   'descripcion': 'Nueva'}, funcionario=self.ana)
        self.assertFalse(form.is_valid())
        self.assertIn('cerrado', str(form.errors['fecha']))
        self.entrar(self.ana)
        self.assertEqual(self.client.get(reverse('gestion:editar', args=[actividad.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse('gestion:eliminar', args=[actividad.pk])).status_code, 403)
        self.entrar(self.delegado_rural)
        respuesta = self.client.get(reverse('gestion:detalle', args=[actividad.pk]))
        self.assertIsNone(respuesta.context['revision_form'])


class FiltrosYAlertasTests(EscenarioBase):
    """RF-032, RF-030, RF-037, RF-008."""

    def test_cp_fil_001_filtros_por_funcionario_item_y_fechas(self):
        """CP-FIL-001: RF-032. El listado filtra por funcionario, ítem y rango de fechas, y conserva los filtros."""
        de_ana = self._actividad(self.ana)
        de_luis = self._actividad(self.luis, fecha=HOY - datetime.timedelta(days=3))
        self.entrar(self.delegado_rural)
        respuesta = self.client.get(reverse('gestion:listado') + f'?funcionario={self.ana.pk}')
        self.assertEqual(list(respuesta.context['actividades']), [de_ana])
        respuesta = self.client.get(reverse('gestion:listado') + f'?hasta={(HOY - datetime.timedelta(days=1)).isoformat()}')
        self.assertEqual(list(respuesta.context['actividades']), [de_luis])
        self.assertEqual(respuesta.context['filtros']['hasta'], (HOY - datetime.timedelta(days=1)).isoformat())

    def test_cp_ale_001_actividad_reciente(self):
        """CP-ALE-001: RF-030. Se calcula el último ingreso, los días sin ingreso, los registros y el promedio diario."""
        self._actividad(self.ana)
        self._actividad(self.ana)
        reciente = actividad_reciente(self.ana, self.periodo, HOY)
        self.assertEqual((reciente.ultimo_ingreso, reciente.dias_sin_ingreso, reciente.registros), (HOY, 0, 2))
        self.assertEqual(reciente.promedio_diario, round(2 / 31, 2))
        self.assertFalse(reciente.inactivo)
        self.assertTrue(actividad_reciente(self.luis, self.periodo, HOY).inactivo)

    def test_cp_ale_002_alertas_del_delegado(self):
        """CP-ALE-002: RF-037. El Delegado recibe alertas de compromisos vencidos y funcionarios sin registros."""
        Compromiso.objects.create(delegacion=self.rural, solicitante='Vecino', territorio='Alto', descripcion='Bache',
                                  responsable=self.ana, fecha_compromiso=HOY - datetime.timedelta(days=2))
        _, _, detalle = cumplimiento_delegacion(self.rural, self.periodo)
        motivos = ' | '.join(a.motivo for a in alertas_delegacion(self.rural, detalle))
        self.assertIn('vencido', motivos)
        self.assertIn('nunca ha registrado', motivos)

    def test_cp_ale_003_panel_de_periodo_anterior(self):
        """CP-ALE-003: RF-008. El panel permite consultar un período anterior y muestra sus actividades, no las del vigente."""
        anterior = Periodo.objects.create(nombre='Primer semestre (prueba)', fecha_inicio=HOY - datetime.timedelta(days=200),
                                          fecha_fin=HOY - datetime.timedelta(days=31), estado='Cerrado')
        Actividad.objects.create(fecha=HOY - datetime.timedelta(days=100), categoria=self.categoria, descripcion='Antigua',
                                 funcionario=self.ana, delegacion=self.rural)
        self.entrar(self.ana)
        respuesta = self.client.get(reverse('delegaciones:inicio') + f'?periodo={anterior.pk}')
        self.assertEqual(respuesta.context['periodo'], anterior)
        self.assertEqual(respuesta.context['total'], 1)
