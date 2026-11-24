"""Pruebas de la versión 3.0 (Guía PI Evaluación 3)."""
from django.urls import reverse

from gestion.models import Actividad, Evidencia

from .tests_roles import EscenarioBase
from .tests_roles import _foto as pdf_simple


class VerificacionV3Tests(EscenarioBase):
    """Flujo de verificación: pendiente, aprobada, rechazada o más antecedentes."""

    def _con_evidencia(self, funcionario):
        actividad = self._actividad(funcionario)
        Evidencia.objects.create(actividad=actividad, archivo=pdf_simple(), subida_por=funcionario.usuario)
        return actividad

    def test_cp_ver_001_delegado_pide_mas_antecedentes(self):
        """CP-VER-001: El Delegado puede pedir más antecedentes con una observación; el estado queda 'Antecedentes'."""
        actividad = self._con_evidencia(self.ana)
        self.entrar(self.delegado_rural)
        self.client.post(reverse('gestion:detalle', args=[actividad.pk]), {
            'revisar': '1', 'decision': 'antecedentes', 'observacion': 'Falta la lista de asistencia'})
        actividad.refresh_from_db()
        self.assertEqual(actividad.estado_validacion, Actividad.EstadoValidacion.ANTECEDENTES)
        self.assertEqual(actividad.observacion_validacion, 'Falta la lista de asistencia')

    def test_cp_ver_002_antecedentes_sin_observacion_se_rechaza(self):
        """CP-VER-002: Pedir antecedentes sin decir cuáles no se acepta (validación en el servidor)."""
        actividad = self._con_evidencia(self.ana)
        self.entrar(self.delegado_rural)
        respuesta = self.client.post(reverse('gestion:detalle', args=[actividad.pk]), {
            'revisar': '1', 'decision': 'antecedentes', 'observacion': ''})
        self.assertEqual(respuesta.status_code, 200)
        actividad.refresh_from_db()
        self.assertEqual(actividad.estado_validacion, Actividad.EstadoValidacion.PENDIENTE)

    def test_cp_ver_003_al_completar_vuelve_a_pendiente(self):
        """CP-VER-003: Cuando el funcionario sube los antecedentes, la actividad vuelve a 'Pendiente'."""
        actividad = self._con_evidencia(self.ana)
        actividad.solicitar_antecedentes(self.delegado_rural, 'Falta foto')
        self.entrar(self.ana)
        self.client.post(reverse('gestion:detalle', args=[actividad.pk]), {
            'subir_evidencia': '1', 'archivo': pdf_simple('otra.jpg'), 'descripcion': 'Foto'})
        actividad.refresh_from_db()
        self.assertEqual(actividad.estado_validacion, Actividad.EstadoValidacion.PENDIENTE)

    def test_cp_ver_004_aprobada_no_se_modifica_ni_por_admin(self):
        """CP-VER-004: Una actividad aprobada no se puede modificar ni eliminar, ni siquiera el Administrador (403)."""
        from comun.pruebas import crear_usuario
        actividad = self._con_evidencia(self.ana)
        actividad.marcar_validado(self.delegado_rural)
        self.entrar(self.ana)
        self.assertEqual(self.client.get(reverse('gestion:editar', args=[actividad.pk])).status_code, 403)
        admin = crear_usuario('admin.prueba', grupos=['Administrador'])
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse('gestion:editar', args=[actividad.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('gestion:eliminar', args=[actividad.pk])).status_code, 403)
        self.assertTrue(Actividad.objects.filter(pk=actividad.pk).exists())


class GestionSocialYTuboTests(EscenarioBase):
    """Gestiones sociales, ingreso opcional al Tubo, Tubo de cartas y búsqueda."""

    def setUp(self):
        super().setUp()
        from territorio.models import SubtipoAtencion, TipoAtencion, Vecino
        self.vecina = Vecino.objects.create(rut='11.111.111-1', nombre='Rosa Pérez Díaz', telefono='+56 9 1234 5678',
                                            delegacion=self.rural)
        tipo = TipoAtencion.objects.create(nombre='Gestión de subsidios')
        self.subtipo = SubtipoAtencion.objects.create(tipo=tipo, nombre='PGU')

    def _datos_social(self, **extra):
        from django.utils import timezone
        datos = {'fecha': timezone.localdate().isoformat(), 'categoria': self.categoria.pk,
                 'subtipo_atencion': self.subtipo.pk, 'tipo_gestion': 'Realizacion', 'vecino': self.vecina.pk,
                 'descripcion': 'Postulación a PGU', 'solicitud_problema': 'Adulta mayor sin pensión'}
        datos.update(extra)
        return datos

    def test_cp_gso_001_gestion_social_toma_datos_del_vecino(self):
        """CP-GSO-001: La gestión social se registra con código GS, el nombre y teléfono del vecino, y suma puntaje."""
        self.entrar(self.luis)
        self.client.post(reverse('gestion:crear_gestion_social'), self._datos_social())
        gestion = Actividad.objects.get(clase=Actividad.Clase.SOCIAL)
        self.assertTrue(gestion.codigo.startswith('GS-'))
        self.assertEqual((gestion.contacto, gestion.telefono_contacto), ('Rosa Pérez Díaz', '+56 9 1234 5678'))
        self.assertTrue(gestion.puntuable)

    def test_cp_gso_002_gestion_social_exige_vecino_y_subtipo(self):
        """CP-GSO-002: Sin vecino o sin subtipo de atención la gestión social no se registra."""
        self.entrar(self.luis)
        respuesta = self.client.post(reverse('gestion:crear_gestion_social'),
                                     self._datos_social(vecino='', subtipo_atencion=''))
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Actividad.objects.filter(clase=Actividad.Clase.SOCIAL).exists())

    def test_cp_gso_003_ingresar_al_tubo_es_opcional(self):
        """CP-GSO-003: Si se marca 'Ingresar al Tubo', tras guardar se abre el alta del compromiso ligado al registro."""
        self.entrar(self.luis)
        sin = self.client.post(reverse('gestion:crear_gestion_social'), self._datos_social())
        self.assertIn('/gestion/', sin['Location'])
        con = self.client.post(reverse('gestion:crear_gestion_social'), self._datos_social(ingresar_al_tubo='on'))
        self.assertIn(reverse('gestion:compromiso_crear'), con['Location'])
        self.assertContains(self.client.get(con['Location']), '11.111.111-1')

    def test_cp_gso_005_tubo_hereda_territorio_del_vecino(self):
        """CP-GSO-005: Al pasar un registro al Tubo, el compromiso trae el territorio del vecino (DEF-V3-04)."""
        from territorio.models import Territorio
        self.vecina.territorio = Territorio.objects.create(nombre='Villa El Romeral', delegacion=self.rural)
        self.vecina.save()
        self.entrar(self.luis)
        con = self.client.post(reverse('gestion:crear_gestion_social'), self._datos_social(ingresar_al_tubo='on'))
        self.assertContains(self.client.get(con['Location']), 'Villa El Romeral')

    def test_cp_gso_004_filtro_y_busqueda_por_rut(self):
        """CP-GSO-004: El listado filtra gestiones sociales y encuentra registros por RUT o nombre del vecino."""
        self.entrar(self.luis)
        self.client.post(reverse('gestion:crear_gestion_social'), self._datos_social())
        social = Actividad.objects.get(clase=Actividad.Clase.SOCIAL)
        otra = self._actividad(self.luis, contacto='Juan Soto')
        respuesta = self.client.get(reverse('gestion:listado'), {'clase': 'Social'})
        self.assertContains(respuesta, social.codigo)
        self.assertNotContains(respuesta, otra.codigo)
        self.assertContains(self.client.get(reverse('gestion:listado'), {'q': '11.111.111'}), social.codigo)
        self.assertContains(self.client.get(reverse('gestion:listado'), {'q': 'Juan Soto'}), otra.codigo)


class TuboCartasTests(EscenarioBase):

    def _carta(self, **extra):
        from gestion.models import Carta
        datos = dict(delegacion=self.rural, para='Delegado', remite='Junta de Vecinos Algarrobito',
                     tema='Solicita luminarias', encargado=self.ana, registrada_por=self.ana)
        datos.update(extra)
        return Carta.objects.create(**datos)

    def test_cp_tub_001_toda_la_delegacion_ve_las_cartas(self):
        """CP-TUB-001: Todos los funcionarios de la delegación ven el Tubo de cartas; otra delegación no."""
        carta = self._carta()
        self.entrar(self.luis)
        self.assertContains(self.client.get(reverse('gestion:cartas')), carta.codigo)
        self.entrar(self.pedro)
        self.assertNotContains(self.client.get(reverse('gestion:cartas')), carta.codigo)

    def test_cp_tub_002_solo_modifica_lo_propio(self):
        """CP-TUB-002: Un funcionario solo modifica sus propias cartas (403 en las ajenas)."""
        carta = self._carta()
        self.entrar(self.luis)
        self.assertEqual(self.client.get(reverse('gestion:carta_editar', args=[carta.pk])).status_code, 403)
        self.entrar(self.ana)
        self.assertEqual(self.client.get(reverse('gestion:carta_editar', args=[carta.pk])).status_code, 200)

    def test_cp_tub_003_aprobada_no_se_modifica(self):
        """CP-TUB-003: Una carta aprobada ya no la modifica el funcionario; solo el Delegado puede aprobarla."""
        from gestion.models import Carta
        carta = self._carta()
        self.entrar(self.ana)
        self.client.post(reverse('gestion:carta_editar', args=[carta.pk]), {
            'fecha_ingreso': carta.fecha_ingreso.isoformat(), 'para': 'Delegado', 'remite': carta.remite,
            'tema': carta.tema, 'encargado': self.ana.pk, 'estado': 'Aprobada'})
        carta.refresh_from_db()
        self.assertEqual(carta.estado, Carta.Estado.EN_PROCESO)
        carta.estado = Carta.Estado.APROBADA
        carta.save()
        self.assertEqual(self.client.get(reverse('gestion:carta_editar', args=[carta.pk])).status_code, 403)

    def test_cp_tub_004_registrar_carta_genera_codigo(self):
        """CP-TUB-004: Al registrar una carta se genera el código TC y la delegación sale de la cuenta."""
        from django.utils import timezone

        from gestion.models import Carta
        self.entrar(self.luis)
        self.client.post(reverse('gestion:carta_crear'), {
            'fecha_ingreso': timezone.localdate().isoformat(), 'para': 'Delegado', 'remite': 'Club Adulto Mayor',
            'rut_remite': '12222222-5', 'tema': 'Solicita sede', 'encargado': self.luis.pk, 'estado': 'En proceso'})
        carta = Carta.objects.get()
        self.assertTrue(carta.codigo.startswith('TC-'))
        self.assertEqual((carta.delegacion, carta.rut_remite, carta.registrada_por), (self.rural, '12.222.222-5', self.luis))

    def test_cp_tub_005_busqueda_dinamica_en_el_tubo(self):
        """CP-TUB-005: El Tubo trae el buscador dinámico y cada fila incluye código, RUT y nombre del solicitante."""
        self._carta(rut_remite='12.222.222-5')
        self.entrar(self.luis)
        respuesta = self.client.get(reverse('gestion:cartas'))
        self.assertContains(respuesta, 'data-busqueda-dinamica')
        self.assertContains(respuesta, '12.222.222-5 Junta de Vecinos Algarrobito')
        self.assertContains(self.client.get(reverse('gestion:agenda')), 'data-busqueda-dinamica')


class DashboardTests(EscenarioBase):

    def test_cp_das_001_dashboard_por_rol(self):
        """CP-DAS-001: El dashboard abre para cada rol con sus gráficos, y el Delegado no ve funcionarios de otra delegación."""
        self._actividad(self.ana)
        self.entrar(self.delegado_rural)
        respuesta = self.client.get(reverse('gestion:dashboard'))
        self.assertEqual(respuesta.status_code, 200)
        nombres = respuesta.context['graficos']['por_funcionario']['etiquetas']
        self.assertIn(self.ana.nombre, nombres)
        self.assertNotIn(self.pedro.nombre, nombres)
        self.assertContains(respuesta, 'g-tendencia')

    def test_cp_das_002_funcionario_solo_se_ve_a_si_mismo(self):
        """CP-DAS-002: En el dashboard el Funcionario solo ve sus propios datos aunque pida otro funcionario en el filtro."""
        self.entrar(self.ana)
        respuesta = self.client.get(reverse('gestion:dashboard'), {'funcionario': self.luis.pk})
        self.assertEqual(respuesta.context['graficos']['por_funcionario']['etiquetas'], [self.ana.nombre])

    def test_cp_das_003_filtros_de_fecha_y_estado(self):
        """CP-DAS-003: Los filtros de rango de fechas y estado cambian los totales del dashboard."""
        import datetime
        self._actividad(self.ana)
        self._actividad(self.ana, fecha=HOY_MENOS(3))
        self.entrar(self.delegado_rural)
        todos = self.client.get(reverse('gestion:dashboard')).context['indicadores']['registros']
        hoy = self.client.get(reverse('gestion:dashboard'), {'desde': datetime.date.today().isoformat()})
        validadas = self.client.get(reverse('gestion:dashboard'), {'validacion': 'Validada'})
        self.assertEqual(todos, 2)
        self.assertEqual(hoy.context['indicadores']['registros'], 1)
        self.assertEqual(validadas.context['indicadores']['registros'], 0)


def HOY_MENOS(dias):
    import datetime

    from django.utils import timezone
    return timezone.localdate() - datetime.timedelta(days=dias)


class RespaldoTests(EscenarioBase):

    def test_cp_res_001_respaldar_y_recuperar(self):
        """CP-RES-001: El respaldo guarda los datos en un .zip y al recuperarlo vuelven los registros borrados."""
        import tempfile
        from io import StringIO
        from pathlib import Path

        from django.core.management import call_command
        actividad = self._actividad(self.ana)
        codigo = actividad.codigo
        with tempfile.TemporaryDirectory() as carpeta:
            call_command('respaldar', destino=carpeta, stdout=StringIO())
            archivo = next(Path(carpeta).glob('sgr_*.zip'))
            Actividad.objects.filter(pk=actividad.pk).delete()
            self.assertFalse(Actividad.objects.filter(codigo=codigo).exists())
            call_command('restaurar', str(archivo), confirmar=True, stdout=StringIO())
        self.assertTrue(Actividad.objects.filter(codigo=codigo).exists())

    def test_cp_res_002_restaurar_exige_confirmar(self):
        """CP-RES-002: Recuperar un respaldo sin --confirmar se rechaza."""
        from django.core.management import call_command
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command('restaurar', 'no_existe.zip')
