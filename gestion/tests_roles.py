"""
Pruebas de los cambios pedidos por el profesor Caiceo en la revisión de la
Evaluación 2 (audio del 04-11-2026): perfiles por rol y delegación, código
automático por área, evidencias, validación por el Delegado y cálculo de
cumplimiento.

Casos del plan: CP-PERF (perfiles y ámbito), CP-COD (registro y código),
CP-EVI (evidencias y validación) y CP-CUM (cumplimiento y semáforo).
"""
import datetime

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from comun.pruebas import CLAVE_PRUEBA, MEDIA_PRUEBAS, crear_usuario
from cuentas.perfiles import sincronizar_cuenta
from delegaciones.models import Delegacion
from organizacion.models import CargoFuncion, Funcionario, MetaProyecto, Periodo

from .forms import ActividadForm
from .indicadores import cumplimiento_delegacion, cumplimiento_funcionario, semaforo
from .models import Actividad, Categoria, Evidencia

HOY = timezone.localdate()


def _foto(nombre='foto.jpg', contenido=b'\xff\xd8\xff\xe0imagen'):
    return SimpleUploadedFile(nombre, contenido, content_type='image/jpeg')


@override_settings(MEDIA_ROOT=MEDIA_PRUEBAS)
class EscenarioBase(TestCase):
    """Dos delegaciones, cada una con su Delegado y funcionarios con cuenta."""

    def setUp(self):
        call_command('configurar_roles', verbosity=0)
        Periodo.objects.all().delete()
        self.periodo = Periodo.objects.create(
            nombre='Período de prueba', fecha_inicio=HOY - datetime.timedelta(days=30),
            fecha_fin=HOY + datetime.timedelta(days=30), estado='Abierto')
        self.rural = self._delegacion('Rural')
        self.centro = self._delegacion('Centro')
        self.territorial = CargoFuncion.objects.create(nombre_cargo='Inspector Territorial', area='TR')
        self.social = CargoFuncion.objects.create(nombre_cargo='Gestor Social', area='SO')
        self.categoria = Categoria.objects.create(nombre='Organizaciones Comunitarias')
        self.ana = self._funcionario('Ana Rojas', '11.111.111-1', self.rural, self.territorial)
        self.luis = self._funcionario('Luis Pérez', '12.222.222-5', self.rural, self.social)
        self.pedro = self._funcionario('Pedro Soto', '13.333.333-9', self.centro, self.territorial)
        self.delegado_rural = self._funcionario('Carla Araya', '14.444.444-2', self.rural, self.territorial, 'Delegado')
        self.delegado_centro = self._funcionario('Sergio Pizarro', '15.555.555-6', self.centro, self.territorial,
                                                 'Delegado')
        self.coordinador = crear_usuario('coordinador.prueba', grupos=['Coordinador'])

    def _delegacion(self, nombre):
        return Delegacion.objects.create(nombre=nombre, encargado='Encargada', direccion='Calle 123',
                                         telefono='+56 51 220 0000', email=f'{nombre.lower()}@laserena.cl',
                                         territorio=nombre, enfoque='Gestión territorial')

    def _funcionario(self, nombre, rut, delegacion, cargo, rol='Funcionario'):
        funcionario = Funcionario.objects.create(
            nombre=nombre, rut=rut, email=f'{rut[:2]}{nombre.split()[0].lower()}@laserena.cl',
            delegacion=delegacion, cargo=cargo, rol=rol)
        sincronizar_cuenta(funcionario, clave=CLAVE_PRUEBA)
        return funcionario

    def _actividad(self, funcionario, **extra):
        datos = dict(fecha=HOY, categoria=self.categoria, descripcion='Reunión con junta de vecinos',
                     funcionario=funcionario, delegacion=funcionario.delegacion)
        datos.update(extra)
        return Actividad.objects.create(**datos)

    def entrar(self, funcionario_o_usuario):
        usuario = getattr(funcionario_o_usuario, 'usuario', funcionario_o_usuario)
        self.client.force_login(User.objects.get(pk=usuario.pk))


class PerfilesTests(EscenarioBase):
    """Unidades: cuentas/perfiles.py (ámbito por rol) y vistas que lo aplican."""

    def test_cp_perf_001_funcionario_ve_solo_sus_actividades(self):
        """CP-PERF-001: El Funcionario ve solo sus actividades, no las de otros funcionarios de su delegación."""
        propia = self._actividad(self.ana)
        ajena = self._actividad(self.luis)
        self.entrar(self.ana)
        respuesta = self.client.get(reverse('gestion:listado'))
        self.assertContains(respuesta, propia.codigo)
        self.assertNotContains(respuesta, ajena.codigo)
        self.assertEqual(self.client.get(reverse('gestion:detalle', args=[ajena.pk])).status_code, 404)

    def test_cp_perf_002_delegado_ve_solo_su_delegacion(self):
        """CP-PERF-002: El Delegado ve las actividades de todos los funcionarios de su delegación y no las de otra."""
        de_ana, de_luis, de_pedro = self._actividad(self.ana), self._actividad(self.luis), self._actividad(self.pedro)
        self.entrar(self.delegado_rural)
        respuesta = self.client.get(reverse('gestion:listado'))
        self.assertContains(respuesta, de_ana.codigo)
        self.assertContains(respuesta, de_luis.codigo)
        self.assertNotContains(respuesta, de_pedro.codigo)

    def test_cp_perf_003_delegado_no_registra_ni_modifica(self):
        """CP-PERF-003: El Delegado no registra ni modifica actividades de sus funcionarios (403)."""
        actividad = self._actividad(self.ana)
        self.entrar(self.delegado_rural)
        self.assertEqual(self.client.get(reverse('gestion:crear')).status_code, 403)
        self.assertEqual(self.client.get(reverse('gestion:editar', args=[actividad.pk])).status_code, 403)

    def test_cp_perf_004_delegado_crea_funcionario_de_su_delegacion(self):
        """CP-PERF-004: El Delegado crea un funcionario: queda en su delegación, con rol Funcionario y cuenta de acceso."""
        self.entrar(self.delegado_rural)
        respuesta = self.client.post(reverse('organizacion:funcionario_crear'), {
            'nombre': 'Marta Díaz', 'rut': '16.666.666-K', 'email': 'marta@laserena.cl',
            'cargo': self.social.pk, 'activo': 'on', 'delegacion': self.centro.pk, 'rol': 'Coordinador',
        }, follow=True)
        nueva = Funcionario.objects.get(rut='16.666.666-K')
        self.assertEqual((nueva.delegacion, nueva.rol), (self.rural, 'Funcionario'))
        self.assertTrue(nueva.usuario.groups.filter(name='Funcionario').exists())
        self.assertContains(respuesta, 'Credenciales para entregar')

    def test_cp_perf_005_delegado_no_modifica_otra_delegacion(self):
        """CP-PERF-005: El Delegado no puede modificar funcionarios de otra delegación ni a otro Delegado (404)."""
        self.entrar(self.delegado_rural)
        self.assertEqual(self.client.get(reverse('organizacion:funcionario_editar', args=[self.pedro.pk])).status_code,
                         404)
        self.assertEqual(
            self.client.get(reverse('organizacion:funcionario_editar', args=[self.delegado_centro.pk])).status_code, 404)

    def test_cp_perf_006_coordinador_crea_y_asigna_delegado(self):
        """CP-PERF-006: El Coordinador crea un Delegado y lo asigna a una delegación; no puede haber dos por delegación."""
        nueva = self._delegacion('La Pampa')
        self.entrar(self.coordinador)
        self.client.post(reverse('organizacion:funcionario_crear'), {
            'nombre': 'Nora Ortiz', 'rut': '17.777.777-3', 'email': 'nora@laserena.cl',
            'delegacion': nueva.pk, 'cargo': self.territorial.pk, 'activo': 'on',
        })
        delegado = Funcionario.objects.get(rut='17.777.777-3')
        self.assertEqual((delegado.rol, delegado.delegacion), ('Delegado', nueva))
        self.assertTrue(delegado.usuario.groups.filter(name='Delegado').exists())
        self.client.post(reverse('organizacion:funcionario_crear'), {
            'nombre': 'Otro Delegado', 'rut': '18.888.888-7', 'email': 'otro@laserena.cl',
            'delegacion': nueva.pk, 'cargo': self.territorial.pk, 'activo': 'on',
        })
        self.assertFalse(Funcionario.objects.filter(rut='18.888.888-7').exists())

    def test_cp_perf_007_coordinador_desactiva_delegacion(self):
        """CP-PERF-007: El Coordinador desactiva una delegación y esta deja de ofrecerse para asignar funcionarios."""
        self.entrar(self.coordinador)
        self.client.post(reverse('delegaciones:cambiar_estado', args=[self.centro.slug]))
        self.centro.refresh_from_db()
        self.assertFalse(self.centro.activa)
        respuesta = self.client.get(reverse('organizacion:funcionario_crear'))
        self.assertNotIn(self.centro, respuesta.context['form'].fields['delegacion'].queryset)

    def test_cp_perf_008_panel_distinto_por_rol(self):
        """CP-PERF-008: Cada rol ve una portada distinta (Funcionario, Delegado y Coordinador)."""
        casos = [(self.ana, 'Mis metas del período'), (self.delegado_rural, 'Evidencias pendientes'),
                 (self.coordinador, 'Coordinación de delegaciones')]
        for quien, texto in casos:
            with self.subTest(texto=texto):
                self.entrar(quien)
                self.assertContains(self.client.get(reverse('delegaciones:inicio')), texto)

    def test_cp_perf_009_cuenta_del_funcionario(self):
        """CP-PERF-009: Las credenciales generadas permiten entrar y, al desactivar al funcionario, su cuenta se bloquea."""
        self.assertTrue(self.client.login(username=self.ana.usuario.username, password=CLAVE_PRUEBA))
        self.ana.activo = False
        self.ana.save()
        sincronizar_cuenta(self.ana)
        self.client.logout()
        self.assertFalse(self.client.login(username=self.ana.usuario.username, password=CLAVE_PRUEBA))


class RegistroActividadTests(EscenarioBase):
    """Unidades: Actividad.save() (código por área) y ActividadForm (registro del Funcionario)."""

    def test_cp_cod_001_codigo_por_area(self):
        """CP-COD-001: El código se genera solo con la sigla del área del cargo: TR-0001, TR-0002 y SO-0001."""
        a1, a2, a3 = self._actividad(self.ana), self._actividad(self.pedro), self._actividad(self.luis)
        self.assertEqual((a1.codigo, a2.codigo, a3.codigo), ('TR-0001', 'TR-0002', 'SO-0001'))
        a1.descripcion = 'Cambio'
        a1.save()
        a1.refresh_from_db()
        self.assertEqual(a1.codigo, 'TR-0001')  # el código no cambia al editar

    def test_cp_cod_002_delegacion_y_funcionario_automaticos(self):
        """CP-COD-002: Al registrar, la delegación y el funcionario salen de la cuenta y el estado parte en Pendiente."""
        self.entrar(self.ana)
        self.client.post(reverse('gestion:crear'), {
            'fecha': HOY.isoformat(), 'categoria': self.categoria.pk, 'descripcion': 'Visita a sede social',
            'delegacion': self.centro.pk, 'funcionario': self.pedro.pk, 'estado': 'Realizado', 'codigo': 'X-1',
        })
        actividad = Actividad.objects.get(descripcion='Visita a sede social')
        self.assertEqual((actividad.funcionario, actividad.delegacion), (self.ana, self.rural))
        self.assertEqual((actividad.estado, actividad.codigo), (Actividad.Estado.PENDIENTE, 'TR-0001'))
        self.assertIsNotNone(actividad.fecha_registro)

    def test_cp_cod_003_fecha_con_plazo(self):
        """CP-COD-003: No se aceptan fechas futuras ni más antiguas que el plazo (7 días); dentro del plazo sí."""
        base = {'categoria': self.categoria.pk, 'descripcion': 'Prueba de fecha'}
        casos = [(HOY + datetime.timedelta(days=1), False), (HOY - datetime.timedelta(days=8), False),
                 (HOY - datetime.timedelta(days=7), True), (HOY, True)]
        for fecha, valida in casos:
            with self.subTest(fecha=fecha):
                form = ActividadForm(data={**base, 'fecha': fecha.isoformat()}, funcionario=self.ana)
                self.assertEqual(form.is_valid(), valida, form.errors)


class EvidenciaValidacionTests(EscenarioBase):
    """Unidades: Evidencia, RevisionForm, Actividad.marcar_validado() / rechazar() y vista de evidencia."""

    def test_cp_evi_001_funcionario_sube_evidencia(self):
        """CP-EVI-001: El Funcionario sube una fotografía y queda guardada con el código de la actividad como nombre."""
        actividad = self._actividad(self.ana)
        self.entrar(self.ana)
        self.client.post(reverse('gestion:detalle', args=[actividad.pk]),
                         {'subir_evidencia': '1', 'archivo': _foto(), 'descripcion': 'Reunión'})
        evidencia = actividad.evidencias.get()
        self.assertTrue(str(evidencia).startswith(f'{actividad.codigo}_1'))
        self.assertEqual(evidencia.subida_por, self.ana.usuario)

    def test_cp_evi_002_formato_y_tamano(self):
        """CP-EVI-002: Se rechazan archivos con formato no permitido o de más de 5 MB."""
        actividad = self._actividad(self.ana)
        self.entrar(self.ana)
        self.client.post(reverse('gestion:detalle', args=[actividad.pk]),
                         {'subir_evidencia': '1', 'archivo': SimpleUploadedFile('virus.exe', b'MZ')})
        grande = SimpleUploadedFile('grande.jpg', b'0' * (5 * 1024 * 1024 + 1), content_type='image/jpeg')
        self.client.post(reverse('gestion:detalle', args=[actividad.pk]), {'subir_evidencia': '1', 'archivo': grande})
        self.assertFalse(actividad.evidencias.exists())

    def test_cp_evi_003_rechazo_y_correccion(self):
        """CP-EVI-003: El Delegado rechaza con observación; el funcionario la ve y al subir otra evidencia vuelve a Pendiente."""
        actividad = self._actividad(self.ana)
        Evidencia.objects.create(actividad=actividad, archivo=_foto())
        self.entrar(self.delegado_rural)
        url = reverse('gestion:detalle', args=[actividad.pk])
        respuesta = self.client.post(url, {'revisar': '1', 'decision': 'rechazar', 'observacion': ''})
        self.assertContains(respuesta, 'Indique el motivo del rechazo')
        self.client.post(url, {'revisar': '1', 'decision': 'rechazar', 'observacion': 'La foto no se ve'})
        actividad.refresh_from_db()
        self.assertEqual(actividad.estado_validacion, Actividad.EstadoValidacion.RECHAZADA)
        self.entrar(self.ana)
        self.assertContains(self.client.get(url), 'La foto no se ve')
        self.client.post(url, {'subir_evidencia': '1', 'archivo': _foto('nueva.png')})
        actividad.refresh_from_db()
        self.assertEqual(actividad.estado_validacion, Actividad.EstadoValidacion.PENDIENTE)

    def test_cp_evi_004_no_se_aprueba_sin_evidencia(self):
        """CP-EVI-004: El Delegado no puede aprobar una actividad que no tiene evidencia."""
        actividad = self._actividad(self.ana)
        self.entrar(self.delegado_rural)
        respuesta = self.client.post(reverse('gestion:detalle', args=[actividad.pk]),
                                     {'revisar': '1', 'decision': 'aprobar'})
        self.assertContains(respuesta, 'sin evidencia')
        actividad.refresh_from_db()
        self.assertFalse(actividad.validado)

    def test_cp_evi_005_archivo_protegido(self):
        """CP-EVI-005: El archivo de la evidencia solo lo ven quienes pueden ver la actividad."""
        actividad = self._actividad(self.ana)
        evidencia = Evidencia.objects.create(actividad=actividad, archivo=_foto())
        url = reverse('gestion:evidencia', args=[evidencia.pk])
        self.entrar(self.delegado_rural)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.entrar(self.pedro)
        self.assertEqual(self.client.get(url).status_code, 404)


class CumplimientoTests(EscenarioBase):
    """Unidades: gestion/indicadores.py (avance, cumplimiento, ponderación y semáforo)."""

    def _meta(self, funcionario, objetivo, ponderador, categoria=None):
        return MetaProyecto.objects.create(
            cargo=funcionario.cargo, funcionario=funcionario, periodo=self.periodo,
            categoria=categoria or self.categoria, item_medible='Meta', valor_objetivo=str(objetivo),
            ponderador=ponderador)

    def _validadas(self, funcionario, cantidad, categoria=None):
        for _ in range(cantidad):
            self._actividad(funcionario, categoria=categoria or self.categoria).marcar_validado(self.delegado_rural)

    def test_cp_cum_001_solo_cuentan_validadas(self):
        """CP-CUM-001: Solo las actividades validadas suman al avance: 2 validadas de una meta de 4 = 50 %."""
        self._meta(self.ana, 4, 100)
        self._validadas(self.ana, 2)
        self._actividad(self.ana)  # pendiente: no cuenta
        resultado = cumplimiento_funcionario(self.ana, self.periodo)
        self.assertEqual((resultado.filas[0].avance, resultado.cumplimiento), (2, 50.0))

    def test_cp_cum_002_ponderacion_y_tope(self):
        """CP-CUM-002: Se aplica el ponderador de cada meta y el tope de 150 % por meta."""
        otra = Categoria.objects.create(nombre='Seguridad')
        self._meta(self.ana, 2, 60)
        self._meta(self.ana, 4, 40, categoria=otra)
        self._validadas(self.ana, 5)            # 250 % -> tope 150 %
        self._validadas(self.ana, 1, categoria=otra)  # 25 %
        resultado = cumplimiento_funcionario(self.ana, self.periodo)
        self.assertEqual([f.cumplimiento for f in resultado.filas], [150.0, 25.0])
        self.assertEqual(resultado.cumplimiento, 100.0)  # 60*150/100 + 40*25/100

    def test_cp_cum_003_semaforo(self):
        """CP-CUM-003: Semáforo: verde si alcanza lo esperado, ámbar desde 60 % de lo esperado y rojo bajo eso."""
        self.assertEqual(semaforo(50, 50), 'verde')
        self.assertEqual(semaforo(30, 50), 'ambar')
        self.assertEqual(semaforo(29, 50), 'rojo')

    def test_cp_cum_004_cumplimiento_de_la_delegacion(self):
        """CP-CUM-004: El cumplimiento de la delegación es el promedio de sus funcionarios con metas."""
        self._meta(self.ana, 2, 100)
        self._meta(self.luis, 4, 100)
        self._validadas(self.ana, 2)
        self._validadas(self.luis, 1)
        porcentaje, _, detalle = cumplimiento_delegacion(self.rural, self.periodo)
        self.assertEqual(porcentaje, 62.5)  # (100 + 25) / 2
        self.assertEqual(len(detalle), 2)


class EquipoDelegadoTests(EscenarioBase):
    def test_cp_perf_010_delegado_ve_solo_su_equipo(self):
        """CP-PERF-010: el Delegado ve en "Mis funcionarios" solo a su equipo
        (él y sus funcionarios), no a un Coordinador asignado a la delegación."""
        coordinadora = self._funcionario('Marta Barraza', '16.666.666-K', self.rural, self.territorial, 'Coordinador')
        self.entrar(self.delegado_rural)
        respuesta = self.client.get(reverse('organizacion:listado'))
        self.assertContains(respuesta, 'Ana Rojas')
        self.assertContains(respuesta, 'Carla Araya')
        self.assertNotContains(respuesta, coordinadora.nombre)
