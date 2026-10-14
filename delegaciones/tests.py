"""
Pruebas unitarias e integrales de la app 'delegaciones'.

Cubren el criterio 2.1.6.13 de la rúbrica de Evaluación 2 (Unidad 2):
pruebas unitarias (modelo) e integrales (vistas end-to-end contra la base
de datos configurada en settings, vía el test runner de Django).
"""
from django.test import TestCase
from django.urls import reverse

from comun.pruebas import iniciar_sesion_admin

from .forms import DelegacionForm
from .models import Delegacion


class DelegacionModeloTests(TestCase):
    """Pruebas unitarias sobre el modelo Delegacion."""

    def test_slug_se_genera_automaticamente(self):
        """CP-DEL-007: Si no se indica slug, se genera automáticamente a partir del nombre."""
        delegacion = Delegacion.objects.create(
            nombre='La Antena - La Florida',
            encargado='Encargado de prueba',
            direccion='Dirección de prueba',
            telefono='+56900000000',
            email='prueba@laserena.cl',
            territorio='Territorio de prueba',
            enfoque='Enfoque de prueba',
        )
        self.assertEqual(delegacion.slug, 'la-antena-la-florida')

    def test_slug_explicito_no_se_sobreescribe(self):
        """CP-DEL-008: Un slug indicado manualmente se respeta."""
        delegacion = Delegacion.objects.create(
            nombre='Centro',
            slug='centro-personalizado',
            encargado='Encargado de prueba',
            direccion='Dirección de prueba',
            telefono='+56900000000',
            email='centro@laserena.cl',
            territorio='Territorio de prueba',
            enfoque='Enfoque de prueba',
        )
        self.assertEqual(delegacion.slug, 'centro-personalizado')

    def test_nombre_unico(self):
        """CP-DEL-009: La base de datos no acepta dos delegaciones con el mismo nombre."""
        Delegacion.objects.create(
            nombre='Rural', encargado='A', direccion='A', telefono='1',
            email='a@laserena.cl', territorio='A', enfoque='A',
        )
        with self.assertRaises(Exception):
            Delegacion.objects.create(
                nombre='Rural', encargado='B', direccion='B', telefono='2',
                email='b@laserena.cl', territorio='B', enfoque='B',
            )

    def test_str_representation(self):
        """CP-DEL-010: La delegación se muestra por su nombre."""
        delegacion = Delegacion.objects.create(
            nombre='Las Compañías', encargado='A', direccion='A', telefono='1',
            email='a@laserena.cl', territorio='A', enfoque='A',
        )
        self.assertEqual(str(delegacion), 'Las Compañías')


class DelegacionVistasTests(TestCase):
    """Pruebas integrales: HTTP end-to-end contra las vistas, usando la
    base de datos real configurada en settings (MySQL o SQLite según el
    .env), tal como la vería un usuario del sistema."""

    def setUp(self):
        iniciar_sesion_admin(self.client)
        self.d1 = Delegacion.objects.create(
            nombre='Avenida del Mar', encargado='Rodrigo', direccion='A',
            telefono='1', email='a@laserena.cl', territorio='Costa', enfoque='A',
        )
        self.d2 = Delegacion.objects.create(
            nombre='La Pampa', encargado='María', direccion='B',
            telefono='2', email='b@laserena.cl', territorio='Pampa', enfoque='B',
        )

    def test_listado_responde_200(self):
        """CP-DEL-011: El listado de delegaciones responde correctamente (200)."""
        response = self.client.get(reverse('delegaciones:listado'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Avenida del Mar')
        self.assertContains(response, 'La Pampa')

    def test_busqueda_filtra_resultados(self):
        """CP-DEL-012: La búsqueda del listado filtra por texto."""
        response = self.client.get(reverse('delegaciones:listado'), {'q': 'Pampa'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'La Pampa')
        self.assertNotContains(response, 'Avenida del Mar')

    def test_detalle_existente_responde_200(self):
        """CP-DEL-013: La ficha de una delegación existente responde 200."""
        response = self.client.get(
            reverse('delegaciones:detalle', args=[self.d1.slug])
        )
        self.assertEqual(response.status_code, 200)

    def test_detalle_inexistente_responde_404(self):
        """CP-DEL-014: Una delegación inexistente responde 404."""
        response = self.client.get(
            reverse('delegaciones:detalle', args=['no-existe'])
        )
        self.assertEqual(response.status_code, 404)


class DelegacionCrudTests(TestCase):
    """Pruebas integrales del CRUD real de Delegación (Evaluación Sumativa
    N.º 3): antes estas tres rutas solo mostraban 'en_construccion.html'."""

    def setUp(self):
        iniciar_sesion_admin(self.client)
        self.delegacion = Delegacion.objects.create(
            nombre='Delegación CRUD', encargado='Encargado original', direccion='A',
            telefono='1', email='crud-deleg@laserena.cl', territorio='A', enfoque='A',
        )

    def test_crear_delegacion_mediante_formulario(self):
        """CP-DEL-015: Se crea una delegación desde el formulario y se genera su slug."""
        datos = {
            'nombre': 'Delegación Nueva (prueba)', 'encargado': 'Encargado de prueba',
            'direccion': 'Dirección de prueba', 'telefono': '+56911111111',
            'email': 'nueva@laserena.cl', 'territorio': 'Territorio de prueba',
            'enfoque': 'Enfoque de prueba',
        }
        response = self.client.post(reverse('delegaciones:crear'), datos)
        delegacion = Delegacion.objects.get(nombre='Delegación Nueva (prueba)')
        self.assertRedirects(response, reverse('delegaciones:detalle', args=[delegacion.slug]))
        self.assertEqual(delegacion.slug, 'delegacion-nueva-prueba')

    def test_editar_delegacion_mediante_formulario(self):
        """CP-DEL-016: Se modifica una delegación desde el formulario."""
        datos = {
            'nombre': self.delegacion.nombre, 'encargado': 'Encargado modificado',
            'direccion': 'Calle Prat 123', 'telefono': '512 206518', 'email': 'crud-deleg@laserena.cl',
            'territorio': 'A', 'enfoque': 'A',
        }
        self.client.post(reverse('delegaciones:editar', args=[self.delegacion.slug]), datos)
        self.delegacion.refresh_from_db()
        self.assertEqual(self.delegacion.encargado, 'Encargado modificado')

    def test_eliminar_delegacion_mediante_formulario(self):
        """CP-DEL-017: Se elimina una delegación sin funcionarios."""
        response = self.client.post(reverse('delegaciones:eliminar', args=[self.delegacion.slug]))
        self.assertRedirects(response, reverse('delegaciones:listado'))
        self.assertFalse(Delegacion.objects.filter(id=self.delegacion.id).exists())

    def test_eliminar_muestra_confirmacion_antes_de_borrar(self):
        """CP-DEL-018: La petición GET de eliminar solo muestra la confirmación y no borra."""
        response = self.client.get(reverse('delegaciones:eliminar', args=[self.delegacion.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Delegacion.objects.filter(id=self.delegacion.id).exists())


class DelegacionValidacionesTests(TestCase):
    """Unidades: DelegacionForm (validaciones nuevas) y eliminación protegida. Casos CP-DEL."""

    def setUp(self):
        self.admin = iniciar_sesion_admin(self.client)
        self.datos = {
            'nombre': 'Delegación Norte', 'encargado': 'María Soto', 'direccion': 'Calle Prat 123',
            'telefono': '512 206518', 'email': 'Norte@LaSerena.cl', 'territorio': 'Sector norte', 'enfoque': 'Atención vecinal',
        }

    def test_cp_del_001_formulario_valido(self):
        """CP-DEL-001: con datos válidos el formulario es válido y el correo queda en minúsculas."""
        form = DelegacionForm(data=self.datos)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['email'], 'norte@laserena.cl')

    def test_cp_del_002_telefono_invalido(self):
        """CP-DEL-002: un teléfono que no tiene 9 dígitos se rechaza."""
        form = DelegacionForm(data={**self.datos, 'telefono': '1234'})
        self.assertFalse(form.is_valid())
        self.assertIn('telefono', form.errors)

    def test_cp_del_003_nombre_duplicado(self):
        """CP-DEL-003: no se acepta una delegación con un nombre ya registrado (sin distinguir mayúsculas)."""
        Delegacion.objects.create(**{**self.datos, 'email': 'otra@laserena.cl'})
        form = DelegacionForm(data={**self.datos, 'nombre': 'DELEGACIÓN NORTE'})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_cp_del_004_campos_obligatorios(self):
        """CP-DEL-004: todos los campos de la delegación son obligatorios."""
        form = DelegacionForm(data={})
        self.assertFalse(form.is_valid())
        for campo in ['nombre', 'encargado', 'direccion', 'telefono', 'email', 'territorio', 'enfoque']:
            self.assertIn(campo, form.errors)

    def test_cp_del_005_eliminar_con_funcionarios(self):
        """CP-DEL-005: no se elimina una delegación con funcionarios (RESTRICT); se muestra un mensaje."""
        from organizacion.models import CargoFuncion, Funcionario
        delegacion = Delegacion.objects.create(**self.datos)
        Funcionario.objects.create(
            nombre='Ana Rojas', rut='12.345.678-5', email='ana@laserena.cl', delegacion=delegacion,
            cargo=CargoFuncion.objects.create(nombre_cargo='Gestor Social'),
        )
        respuesta = self.client.post(reverse('delegaciones:eliminar', args=[delegacion.slug]), follow=True)
        self.assertTrue(Delegacion.objects.filter(pk=delegacion.pk).exists())
        self.assertContains(respuesta, 'No se puede eliminar la delegación')

    def test_cp_del_006_sin_permiso_no_crea(self):
        """CP-DEL-006: un usuario sin permiso de agregar recibe 403 y no se crea la delegación."""
        from comun.pruebas import crear_usuario
        self.client.force_login(crear_usuario('sin.permisos'))
        respuesta = self.client.post(reverse('delegaciones:crear'), self.datos)
        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(Delegacion.objects.filter(nombre='Delegación Norte').exists())
