"""Pruebas de la versión 3.0: territorios, vecinos, socios y dirigentes,
hitos y tipos de atención (CRUD con validaciones y ámbito por delegación)."""
from django.urls import reverse

from delegaciones.models import OrganizacionComunitaria
from gestion.tests_roles import EscenarioBase

from .models import Hito, MembresiaOrganizacion, SubtipoAtencion, Territorio, TipoAtencion, Vecino


class ComunidadV3Tests(EscenarioBase):

    def setUp(self):
        super().setUp()
        self.sector = Territorio.objects.create(nombre='Sector Algarrobito', delegacion=self.rural)
        self.vecina = Vecino.objects.create(rut='11.111.111-1', nombre='Rosa Pérez Díaz',
                                            telefono='+56 9 1234 5678', delegacion=self.rural)
        self.jjvv = OrganizacionComunitaria.objects.create(nombre='JJVV Algarrobito', delegacion=self.rural)

    def test_cp_com_001_delegado_crea_territorio_en_su_delegacion(self):
        """CP-COM-001: El Delegado crea un territorio y queda asignado a su propia delegación."""
        self.entrar(self.delegado_rural)
        self.client.post(reverse('territorio:territorio_crear'), {'nombre': 'Sector El Romeral', 'activo': 'on'})
        territorio = Territorio.objects.get(nombre='Sector El Romeral')
        self.assertEqual(territorio.delegacion, self.rural)
        # El Delegado crea y edita territorios, pero no los elimina (solo el Administrador)
        url = reverse('territorio:territorio_eliminar', args=[territorio.pk])
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_cp_com_002_territorio_repetido_se_rechaza(self):
        """CP-COM-002: No se puede repetir el nombre de un territorio en la misma delegación."""
        self.entrar(self.delegado_rural)
        respuesta = self.client.post(reverse('territorio:territorio_crear'), {'nombre': 'sector algarrobito'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Territorio.objects.filter(delegacion=self.rural).count(), 1)

    def test_cp_com_003_vecino_rut_invalido_o_repetido(self):
        """CP-COM-003: El RUT del vecino se valida (dígito verificador) y no se puede repetir."""
        self.entrar(self.ana)
        datos = {'nombre': 'Juan Soto Rojas', 'telefono': '+56 9 8765 4321'}
        r1 = self.client.post(reverse('territorio:vecino_crear'), dict(datos, rut='11.111.111-2'))
        r2 = self.client.post(reverse('territorio:vecino_crear'), dict(datos, rut='11111111-1'))
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(Vecino.objects.count(), 1)

    def test_cp_com_004_vecino_valido_normaliza_rut(self):
        """CP-COM-004: Un vecino válido se guarda con el RUT normalizado y en la delegación del funcionario."""
        self.entrar(self.ana)
        self.client.post(reverse('territorio:vecino_crear'), {
            'rut': '12222222-5', 'nombre': 'Juan Soto Rojas', 'telefono': '987654321'})
        vecino = Vecino.objects.get(nombre='Juan Soto Rojas')
        self.assertEqual(vecino.rut, '12.222.222-5')
        self.assertEqual(vecino.delegacion, self.rural)
        # v3.0.1: el Delegado abre la página de eliminar (antes daba error 500) y elimina
        self.entrar(self.delegado_rural)
        url = reverse('territorio:vecino_eliminar', args=[vecino.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.post(url)
        self.assertFalse(Vecino.objects.filter(pk=vecino.pk).exists())

    def test_cp_com_005_otra_delegacion_no_ve_los_vecinos(self):
        """CP-COM-005: Un funcionario de otra delegación no ve ni puede editar los vecinos ajenos (404)."""
        self.entrar(self.pedro)
        self.assertNotContains(self.client.get(reverse('territorio:vecinos')), 'Rosa Pérez')
        self.assertEqual(self.client.get(reverse('territorio:vecino_editar', args=[self.vecina.pk])).status_code, 404)

    def test_cp_com_006_dirigente_necesita_cargo_y_cargo_unico(self):
        """CP-COM-006: Un dirigente debe tener cargo, y una organización no puede tener dos presidentes vigentes."""
        self.entrar(self.delegado_rural)
        r1 = self.client.post(reverse('territorio:membresia_crear'), {
            'organizacion': self.jjvv.pk, 'vecino': self.vecina.pk, 'rol': 'Dirigente', 'cargo': '', 'vigente': 'on'})
        self.assertEqual(r1.status_code, 200)
        self.client.post(reverse('territorio:membresia_crear'), {
            'organizacion': self.jjvv.pk, 'vecino': self.vecina.pk, 'rol': 'Dirigente', 'cargo': 'Presidente',
            'vigente': 'on'})
        otro = Vecino.objects.create(rut='12.222.222-5', nombre='Juan Soto Rojas', telefono='987654321',
                                     delegacion=self.rural)
        r3 = self.client.post(reverse('territorio:membresia_crear'), {
            'organizacion': self.jjvv.pk, 'vecino': otro.pk, 'rol': 'Dirigente', 'cargo': 'Presidente', 'vigente': 'on'})
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(MembresiaOrganizacion.objects.filter(cargo='Presidente').count(), 1)

    def test_cp_com_007_hito_responsable_de_la_misma_delegacion(self):
        """CP-COM-007: El responsable de un hito debe ser de la delegación del hito."""
        self.client.force_login(self.coordinador)
        from comun.pruebas import crear_usuario
        self.client.force_login(crear_usuario('admin.hitos', grupos=['Administrador']))
        respuesta = self.client.post(reverse('territorio:hito_crear'), {
            'nombre': 'Operativo de limpieza', 'fecha': '2026-12-01', 'delegacion': self.rural.pk,
            'responsable': self.pedro.pk, 'estado': 'Planificado'})
        self.assertEqual(respuesta.status_code, 200)
        self.client.post(reverse('territorio:hito_crear'), {
            'nombre': 'Operativo de limpieza', 'fecha': '2026-12-01', 'delegacion': self.rural.pk,
            'responsable': self.ana.pk, 'estado': 'Planificado'})
        self.assertEqual(Hito.objects.get().responsable, self.ana)

    def test_cp_com_008_tipos_y_subtipos_de_atencion(self):
        """CP-COM-008: El Coordinador crea tipos y subtipos de atención; un subtipo no se repite dentro del tipo."""
        self.client.force_login(self.coordinador)
        self.client.post(reverse('territorio:tipo_crear'), {'nombre': 'Gestión de subsidios', 'activo': 'on'})
        tipo = TipoAtencion.objects.get()
        self.client.post(reverse('territorio:subtipo_crear'), {'tipo': tipo.pk, 'nombre': 'PGU', 'activo': 'on'})
        r = self.client.post(reverse('territorio:subtipo_crear'), {'tipo': tipo.pk, 'nombre': 'pgu', 'activo': 'on'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(SubtipoAtencion.objects.count(), 1)

    def test_cp_com_009_funcionario_no_crea_tipos_de_atencion(self):
        """CP-COM-009: Un Funcionario no puede crear tipos de atención (403)."""
        self.entrar(self.ana)
        self.assertEqual(self.client.get(reverse('territorio:tipo_crear')).status_code, 403)

    def test_cp_com_010_autocompletar_vecino_por_rut(self):
        """CP-COM-010: Al escribir un RUT se obtienen los datos del vecino para autocompletar el formulario."""
        self.entrar(self.ana)
        datos = self.client.get(reverse('territorio:buscar_vecino'), {'q': '11111111-1'}).json()
        self.assertEqual(datos['resultados'][0]['telefono'], '+56 9 1234 5678')
        self.entrar(self.pedro)
        self.assertEqual(self.client.get(reverse('territorio:buscar_vecino'), {'q': 'Rosa'}).json()['resultados'], [])
