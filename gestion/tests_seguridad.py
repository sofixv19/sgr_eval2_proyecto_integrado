"""
Pruebas de seguridad (versión 2.2.3, OWASP Top 10:2025).

Demuestran con código controles que no se ven en la pantalla:
- CP-SEG-001: inyección SQL (A05): el buscador usa consultas parametrizadas.
- CP-SEG-002: XSS (A05): el texto que escribe un usuario se muestra escapado.
- CP-SEG-003: CSRF (A08): un formulario enviado sin token se rechaza.
- CP-SEG-004: control de acceso (A01): un Funcionario no ve lo de otra delegación.
"""
from django.test import Client
from django.urls import reverse

from cuentas.perfiles import filtrar_actividades
from gestion.models import Actividad

from .tests_roles import EscenarioBase

INYECCION = "' OR 1=1 --"


class SeguridadTests(EscenarioBase):

    def test_cp_seg_001_inyeccion_sql_en_el_buscador(self):
        """CP-SEG-001: Una búsqueda con "' OR 1=1 --" no altera la consulta: el ORM la envía como parámetro."""
        self._actividad(self.ana)
        self._actividad(self.pedro)
        self.client.force_login(self.coordinador)
        respuesta = self.client.get(reverse('gestion:listado'), {'q': INYECCION})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context['actividades'].count(), 0)
        # El texto del usuario viaja aparte, como parámetro, nunca pegado en el SQL.
        sql, parametros = Actividad.objects.filter(descripcion__icontains=INYECCION).query.sql_with_params()
        self.assertNotIn(INYECCION, sql)
        self.assertIn(f'%{INYECCION}%', parametros)

    def test_cp_seg_002_texto_del_usuario_se_muestra_escapado(self):
        """CP-SEG-002: Una descripción con <script> se muestra como texto y no se ejecuta en el navegador."""
        actividad = self._actividad(self.ana, descripcion='<script>alert("hola")</script>')
        self.entrar(self.ana)
        respuesta = self.client.get(reverse('gestion:detalle', args=[actividad.pk]))
        self.assertContains(respuesta, '&lt;script&gt;')
        self.assertNotContains(respuesta, '<script>alert')

    def test_cp_seg_003_formulario_sin_token_csrf_se_rechaza(self):
        """CP-SEG-003: Un formulario enviado desde otro sitio, sin el token CSRF, se rechaza con 403."""
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.ana.usuario)
        respuesta = cliente.post(reverse('gestion:crear'), {'descripcion': 'Enviada desde otro sitio'})
        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(Actividad.objects.filter(descripcion='Enviada desde otro sitio').exists())

    def test_cp_seg_004_funcionario_no_ve_otra_delegacion(self):
        """CP-SEG-004: El filtro por ámbito deja al Funcionario solo con lo suyo, y la ficha de otra delegación responde 404."""
        propia = self._actividad(self.ana)
        ajena = self._actividad(self.pedro)
        visibles = filtrar_actividades(self.ana.usuario, Actividad.objects.all())
        self.assertEqual(list(visibles), [propia])
        self.entrar(self.ana)
        self.assertEqual(self.client.get(reverse('gestion:detalle', args=[ajena.pk])).status_code, 404)
