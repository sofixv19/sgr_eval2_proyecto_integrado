"""Pruebas de la versión 3.0 (Guía PI Evaluación 3, Actividad 1 y 2):
contraseña temporal con cambio obligatorio y recuperación por correo."""
import re

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from cuentas.models import EstadoCuenta, debe_cambiar_clave, marcar_clave_temporal

CLAVE = 'Clave.Segura.2026'
NUEVA = 'Otra.Clave.Segura.77'


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ClavesTests(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user('ana.rojas', 'ana@laserena.cl', CLAVE)

    def test_cp_cla_001_clave_temporal_obliga_a_cambiarla(self):
        """CP-CLA-001: Con contraseña temporal, cualquier página redirige al cambio de contraseña."""
        marcar_clave_temporal(self.usuario)
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('gestion:listado'))
        self.assertRedirects(respuesta, reverse('cuentas:cambiar_clave'))

    def test_cp_cla_002_al_cambiarla_se_libera_el_acceso(self):
        """CP-CLA-002: Tras cambiar la contraseña temporal, el usuario sigue con sesión y ya no se le exige el cambio."""
        marcar_clave_temporal(self.usuario)
        self.client.force_login(self.usuario)
        respuesta = self.client.post(reverse('cuentas:cambiar_clave'), {
            'old_password': CLAVE, 'new_password1': NUEVA, 'new_password2': NUEVA})
        self.assertRedirects(respuesta, '/', fetch_redirect_response=False)
        self.assertFalse(debe_cambiar_clave(self.usuario))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(NUEVA))

    def test_cp_cla_003_clave_debil_o_actual_incorrecta_se_rechaza(self):
        """CP-CLA-003: Se rechaza una clave actual incorrecta y una nueva clave débil (validación en el servidor)."""
        marcar_clave_temporal(self.usuario)
        self.client.force_login(self.usuario)
        respuesta = self.client.post(reverse('cuentas:cambiar_clave'), {
            'old_password': 'incorrecta', 'new_password1': '123', 'new_password2': '123'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context['form'].errors)
        self.assertTrue(debe_cambiar_clave(self.usuario))

    def test_cp_cla_004_recuperar_envia_enlace_y_no_revela_correos(self):
        """CP-CLA-004: Recuperar contraseña envía un enlace al correo registrado y responde igual si el correo no existe."""
        r1 = self.client.post(reverse('cuentas:recuperar'), {'email': 'ana@laserena.cl'})
        r2 = self.client.post(reverse('cuentas:recuperar'), {'email': 'nadie@laserena.cl'})
        self.assertRedirects(r1, reverse('cuentas:recuperar_enviado'))
        self.assertRedirects(r2, reverse('cuentas:recuperar_enviado'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/cuentas/restablecer/', mail.outbox[0].body)
        # v3.0.1: si el servidor de correo falla, la página no se cae (Django registra el error)
        import smtplib
        from unittest import mock
        with mock.patch('django.core.mail.EmailMultiAlternatives.send', side_effect=smtplib.SMTPException('caído')):
            r3 = self.client.post(reverse('cuentas:recuperar'), {'email': 'ana@laserena.cl'})
        self.assertRedirects(r3, reverse('cuentas:recuperar_enviado'))

    def test_cp_cla_005_enlace_sirve_una_vez(self):
        """CP-CLA-005: El enlace de recuperación permite crear una clave nueva y deja de servir después de usarlo."""
        self.client.post(reverse('cuentas:recuperar'), {'email': 'ana@laserena.cl'})
        enlace = re.search(r'(/cuentas/restablecer/\S+/)', mail.outbox[0].body).group(1)
        respuesta = self.client.get(enlace, follow=True)
        url_form = respuesta.redirect_chain[-1][0]
        self.client.post(url_form, {'new_password1': NUEVA, 'new_password2': NUEVA})
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(NUEVA))
        segunda = self.client.get(enlace, follow=True)
        self.assertFalse(segunda.context['validlink'])

    @override_settings(PASSWORD_RESET_TIMEOUT=-1)
    def test_cp_cla_006_enlace_vencido_no_sirve(self):
        """CP-CLA-006: Un enlace de recuperación vencido se rechaza (token con expiración)."""
        uid = urlsafe_base64_encode(force_bytes(self.usuario.pk))
        token = default_token_generator.make_token(self.usuario)
        respuesta = self.client.get(reverse('cuentas:restablecer', args=[uid, token]), follow=True)
        self.assertFalse(respuesta.context['validlink'])

    def test_cp_cla_007_paginas_de_recuperacion_son_publicas(self):
        """CP-CLA-007: Las páginas de recuperación se abren sin sesión y el inicio de sesión muestra el enlace."""
        self.assertEqual(self.client.get(reverse('cuentas:recuperar')).status_code, 200)
        self.assertContains(self.client.get(reverse('cuentas:login')), reverse('cuentas:recuperar'))

    def test_cp_cla_008_nueva_clave_del_delegado_es_temporal(self):
        """CP-CLA-008: La contraseña que genera el sistema para una cuenta nueva queda marcada como temporal."""
        from cuentas.perfiles import sincronizar_cuenta
        from delegaciones.models import Delegacion
        from organizacion.models import CargoFuncion, Funcionario
        d = Delegacion.objects.create(nombre='Rural', encargado='E', direccion='D', telefono='1',
                                      email='r@laserena.cl', territorio='Rural', enfoque='E')
        f = Funcionario.objects.create(nombre='Luis Pérez', rut='12.222.222-5', email='luis@laserena.cl',
                                       delegacion=d, cargo=CargoFuncion.objects.create(nombre_cargo='Gestor'))
        usuario, clave = sincronizar_cuenta(f)
        self.assertTrue(clave)
        self.assertTrue(EstadoCuenta.objects.get(usuario=usuario).debe_cambiar_clave)
