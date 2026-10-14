"""
Pruebas unitarias del módulo de autenticación (app 'cuentas').

Siguen los casos CP-LOGIN del Plan de Pruebas Unitarias: la unidad probada
es la función validar_credenciales() de cuentas/servicios.py, aislada de la
vista. Las pruebas CP-ACC verifican el control de acceso del sitio.
"""
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from comun.pruebas import CLAVE_PRUEBA, crear_usuario

from . import servicios
from .servicios import validar_credenciales


class ValidarCredencialesTests(TestCase):
    """Unidad: cuentas.servicios.validar_credenciales()."""

    def setUp(self):
        cache.clear()
        self.usuario = crear_usuario('usuario.prueba')

    def test_cp_login_001_credenciales_validas(self):
        """CP-LOGIN-001: usuario y contraseña válidos -> autenticación exitosa."""
        resultado = validar_credenciales('usuario.prueba', CLAVE_PRUEBA)
        self.assertTrue(resultado.ok)
        self.assertEqual(resultado.codigo, servicios.OK)
        self.assertEqual(resultado.usuario, self.usuario)

    def test_cp_login_002_contrasena_incorrecta(self):
        """CP-LOGIN-002: usuario válido y contraseña incorrecta -> autenticación rechazada."""
        resultado = validar_credenciales('usuario.prueba', 'otraClave.123')
        self.assertFalse(resultado.ok)
        self.assertEqual(resultado.codigo, servicios.CREDENCIALES_INVALIDAS)
        self.assertIsNone(resultado.usuario)

    def test_cp_login_003_usuario_inexistente(self):
        """CP-LOGIN-003: usuario inexistente -> autenticación rechazada."""
        resultado = validar_credenciales('no.existe', CLAVE_PRUEBA)
        self.assertFalse(resultado.ok)
        self.assertEqual(resultado.codigo, servicios.CREDENCIALES_INVALIDAS)

    def test_cp_login_004_usuario_vacio(self):
        """CP-LOGIN-004: usuario vacío -> validación de campo obligatorio."""
        resultado = validar_credenciales('   ', CLAVE_PRUEBA)
        self.assertFalse(resultado.ok)
        self.assertEqual(resultado.codigo, servicios.USUARIO_VACIO)
        self.assertEqual(resultado.mensaje, 'El usuario es obligatorio.')

    def test_cp_login_005_contrasena_vacia(self):
        """CP-LOGIN-005: contraseña vacía -> validación de campo obligatorio."""
        resultado = validar_credenciales('usuario.prueba', '')
        self.assertFalse(resultado.ok)
        self.assertEqual(resultado.codigo, servicios.CONTRASENA_VACIA)
        self.assertEqual(resultado.mensaje, 'La contraseña es obligatoria.')

    def test_cp_login_006_ambos_campos_vacios(self):
        """CP-LOGIN-006: usuario y contraseña vacíos -> se informa que ambos campos son obligatorios."""
        resultado = validar_credenciales('', '')
        self.assertFalse(resultado.ok)
        self.assertEqual(resultado.codigo, servicios.AMBOS_VACIOS)
        self.assertIn('usuario y su contraseña', resultado.mensaje)

    def test_cp_login_007_usuario_inactivo(self):
        """CP-LOGIN-007: usuario bloqueado/inactivo -> acceso rechazado."""
        crear_usuario('usuario.inactivo', activo=False)
        resultado = validar_credenciales('usuario.inactivo', CLAVE_PRUEBA)
        self.assertFalse(resultado.ok)
        self.assertEqual(resultado.codigo, servicios.USUARIO_INACTIVO)

    def test_cp_login_008_formato_invalido(self):
        """CP-LOGIN-008: datos con formato inválido -> validación y rechazo de los datos."""
        for usuario in ['ab', 'usuario con espacios', "admin' OR '1'='1", 'x' * 151]:
            with self.subTest(usuario=usuario):
                resultado = validar_credenciales(usuario, CLAVE_PRUEBA)
                self.assertFalse(resultado.ok)
                self.assertEqual(resultado.codigo, servicios.FORMATO_INVALIDO)

    @override_settings(SGR_LOGIN_MAX_INTENTOS=5)
    def test_cp_login_009_bloqueo_por_intentos_fallidos(self):
        """CP-LOGIN-009: tras 5 intentos fallidos la cuenta se bloquea temporalmente, incluso con la clave correcta."""
        for _ in range(5):
            validar_credenciales('usuario.prueba', 'claveMala.1')
        resultado = validar_credenciales('usuario.prueba', CLAVE_PRUEBA)
        self.assertFalse(resultado.ok)
        self.assertEqual(resultado.codigo, servicios.BLOQUEADO)

    def test_cp_login_010_mensaje_no_revela_usuarios(self):
        """CP-LOGIN-010: usuario inexistente y contraseña incorrecta muestran el mismo mensaje."""
        inexistente = validar_credenciales('no.existe', 'claveMala.1')
        incorrecta = validar_credenciales('usuario.prueba', 'claveMala.1')
        self.assertEqual(inexistente.mensaje, incorrecta.mensaje)
        self.assertEqual(inexistente.mensaje, servicios.MENSAJE_INVALIDAS)


class ControlAccesoTests(TestCase):
    """Unidades: LoginObligatorioMiddleware, vistas iniciar_sesion / cerrar_sesion y permisos."""

    def setUp(self):
        cache.clear()
        self.usuario = crear_usuario('usuario.prueba')

    def test_cp_acc_001_anonimo_redirigido_al_login(self):
        """CP-ACC-001: un usuario sin sesión que entra a una página interna es enviado al login."""
        respuesta = self.client.get(reverse('organizacion:cargos'))
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(respuesta['Location'].startswith(reverse('cuentas:login')))
        self.assertIn('next=', respuesta['Location'])

    def test_cp_acc_002_login_correcto_redirige_a_next(self):
        """CP-ACC-002: el login correcto crea la sesión y redirige a la página pedida."""
        respuesta = self.client.post(reverse('cuentas:login'), {
            'usuario': 'usuario.prueba', 'contrasena': CLAVE_PRUEBA, 'next': '/gestion/',
        })
        self.assertRedirects(respuesta, '/gestion/', fetch_redirect_response=False)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.usuario.pk)

    def test_cp_acc_003_next_externo_se_ignora(self):
        """CP-ACC-003: un parámetro next hacia otro sitio se ignora (redirección abierta)."""
        respuesta = self.client.post(reverse('cuentas:login'), {
            'usuario': 'usuario.prueba', 'contrasena': CLAVE_PRUEBA, 'next': 'http://sitio-malicioso.com/',
        })
        self.assertRedirects(respuesta, '/', fetch_redirect_response=False)

    def test_cp_acc_004_login_incorrecto_muestra_error(self):
        """CP-ACC-004: el formulario de login muestra el error y no crea sesión."""
        respuesta = self.client.post(reverse('cuentas:login'), {'usuario': 'usuario.prueba', 'contrasena': 'mala'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, servicios.MENSAJE_INVALIDAS)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_cp_acc_005_cerrar_sesion_solo_por_post(self):
        """CP-ACC-005: cerrar sesión exige POST (con CSRF) y elimina la sesión."""
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse('cuentas:logout')).status_code, 405)
        respuesta = self.client.post(reverse('cuentas:logout'))
        self.assertRedirects(respuesta, reverse('cuentas:login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_cp_acc_006_sin_permiso_recibe_403(self):
        """CP-ACC-006: un usuario sin el permiso 'add' recibe 403 al intentar crear un cargo."""
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('organizacion:cargo_crear'))
        self.assertEqual(respuesta.status_code, 403)

    def test_cp_acc_007_contrasena_guardada_con_hash(self):
        """CP-ACC-007: la contraseña se guarda con hash PBKDF2 y nunca en texto plano."""
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.password.startswith('pbkdf2_sha256$'))
        self.assertNotIn(CLAVE_PRUEBA, self.usuario.password)


class ConfigurarRolesTests(TestCase):
    """Unidad: comando de gestión configurar_roles (permisos por grupo)."""

    def setUp(self):
        call_command('configurar_roles', verbosity=0)

    def test_cp_rol_001_crea_los_cinco_grupos(self):
        """CP-ROL-001: se crean los grupos Administrador, Coordinador, Delegado, Funcionario y Verificador."""
        nombres = set(Group.objects.values_list('name', flat=True))
        self.assertEqual(nombres, {'Administrador', 'Coordinador', 'Delegado', 'Funcionario', 'Verificador'})

    def test_cp_rol_002_verificador_solo_lectura(self):
        """CP-ROL-002: el Verificador solo tiene permisos de lectura (view)."""
        permisos = Group.objects.get(name='Verificador').permissions.values_list('codename', flat=True)
        self.assertTrue(permisos)
        self.assertTrue(all(p.startswith('view_') for p in permisos))

    def test_cp_rol_003_coordinador_gestiona_metas_pero_no_funcionarios(self):
        """CP-ROL-003: el Coordinador puede crear metas, pero no funcionarios."""
        coordinador = crear_usuario('coordinador.prueba', grupos=['Coordinador'])
        coordinador = User.objects.get(pk=coordinador.pk)  # recarga la caché de permisos
        self.assertTrue(coordinador.has_perm('organizacion.add_metaproyecto'))
        self.assertFalse(coordinador.has_perm('organizacion.add_funcionario'))
        self.client.force_login(coordinador)
        self.assertEqual(self.client.get(reverse('organizacion:meta_crear')).status_code, 200)
        self.assertEqual(self.client.get(reverse('organizacion:funcionario_crear')).status_code, 403)
