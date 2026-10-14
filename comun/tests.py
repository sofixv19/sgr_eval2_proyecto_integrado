"""
Pruebas unitarias de los validadores reutilizables (comun/validadores.py)
y del filtro de plantilla 'atributo'. Casos CP-VAL del Plan de Pruebas.
"""
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .templatetags.comun_tags import atributo
from .validadores import calcular_dv, normalizar_rut, validar_nombre, validar_telefono, validar_texto_minimo


class ValidadorRutTests(SimpleTestCase):
    """Unidades: calcular_dv() y normalizar_rut()."""

    def test_cp_val_001_rut_valido_se_normaliza(self):
        """CP-VAL-001: Un RUT válido escrito sin puntos se acepta y se normaliza a 12.345.678-5."""
        self.assertEqual(normalizar_rut('12345678-5'), '12.345.678-5')
        self.assertEqual(normalizar_rut(' 7.654.321-6 '), '7.654.321-6')

    def test_cp_val_002_rut_con_dv_incorrecto(self):
        """CP-VAL-002: Un RUT con dígito verificador incorrecto se rechaza."""
        with self.assertRaisesMessage(ValidationError, 'dígito verificador'):
            normalizar_rut('12.345.678-9')

    def test_cp_val_003_rut_con_formato_invalido(self):
        """CP-VAL-003: Textos que no tienen forma de RUT se rechazan."""
        for valor in ['', 'abc', '123-4', '12.345.678-55', '12345678K9']:
            with self.subTest(valor=valor):
                with self.assertRaisesMessage(ValidationError, 'Formato de RUT inválido'):
                    normalizar_rut(valor)

    def test_cp_val_004_rut_con_dv_k(self):
        """CP-VAL-004: Se aceptan RUT cuyo dígito verificador es K (en minúscula o mayúscula)."""
        self.assertEqual(calcular_dv(16666666), 'K')
        self.assertEqual(normalizar_rut('16666666-k'), '16.666.666-K')


class ValidadoresTextoTests(SimpleTestCase):
    """Unidades: validar_telefono(), validar_nombre() y validar_texto_minimo()."""

    def test_cp_val_005_telefono_valido(self):
        """CP-VAL-005: Teléfonos chilenos de 9 dígitos, con o sin +56 y separadores, se aceptan."""
        for valor in ['512 206518', '+56 9 1234 5678', '(51) 220-6518', '56912345678']:
            with self.subTest(valor=valor):
                validar_telefono(valor)

    def test_cp_val_006_telefono_invalido(self):
        """CP-VAL-006: Teléfonos con letras o con una cantidad incorrecta de dígitos se rechazan."""
        for valor in ['', '1234', '51220651', '5122065189', 'fono 512206518']:
            with self.subTest(valor=valor):
                with self.assertRaises(ValidationError):
                    validar_telefono(valor)

    def test_cp_val_007_nombre_con_numeros_o_simbolos(self):
        """CP-VAL-007: Un nombre con números o símbolos se rechaza."""
        for valor in ['Ana 123', 'Juan<script>', 'Pedro@Soto']:
            with self.subTest(valor=valor):
                with self.assertRaisesMessage(ValidationError, 'solo puede contener letras'):
                    validar_nombre(valor)

    def test_cp_val_008_nombre_corto_y_espacios(self):
        """CP-VAL-008: Un nombre de menos de 3 letras se rechaza y los espacios repetidos se limpian."""
        with self.assertRaisesMessage(ValidationError, 'al menos 3'):
            validar_nombre('  A ')
        self.assertEqual(validar_nombre('  María   José  Pérez '), 'María José Pérez')

    def test_cp_val_009_texto_minimo(self):
        """CP-VAL-009: Un texto obligatorio formado solo por espacios se rechaza."""
        with self.assertRaises(ValidationError):
            validar_texto_minimo('     ', minimo=3)
        self.assertEqual(validar_texto_minimo(' Calle  Prat 123 '), 'Calle Prat 123')


class FiltroAtributoTests(SimpleTestCase):
    """Unidad: filtro de plantilla 'atributo' usado por los listados genéricos."""

    def test_cp_val_010_filtro_atributo(self):
        """CP-VAL-010: El filtro lee rutas con punto y muestra Sí/No y '—' para valores vacíos."""
        class Cargo:
            nombre_cargo = 'Gestor Social'

        class Obj:
            cargo = Cargo()
            activo = True
            descripcion = ''

        self.assertEqual(atributo(Obj(), 'cargo.nombre_cargo'), 'Gestor Social')
        self.assertEqual(atributo(Obj(), 'activo'), 'Sí')
        self.assertEqual(atributo(Obj(), 'descripcion'), '—')
