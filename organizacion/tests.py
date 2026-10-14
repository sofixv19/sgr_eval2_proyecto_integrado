"""
Pruebas unitarias de la app 'organizacion' (CargoFuncion, Funcionario,
MetaProyecto), incorporada al proyecto al fusionar el trabajo del
compañero de equipo con el de Sofía.
"""
import datetime

from django.test import TestCase
from django.urls import reverse

from comun.pruebas import iniciar_sesion_admin
from delegaciones.models import Delegacion
from gestion.models import Actividad, Categoria

from .forms import CargoFuncionForm, FuncionarioForm, MetaProyectoForm
from .models import CargoFuncion, Funcionario, MetaProyecto


class CargoFuncionTests(TestCase):
    def test_nombre_cargo_unico(self):
        """CP-ORG-001: La base de datos no acepta dos cargos con el mismo nombre."""
        CargoFuncion.objects.create(nombre_cargo='Gestor Social')
        with self.assertRaises(Exception):
            CargoFuncion.objects.create(nombre_cargo='Gestor Social')

    def test_str_representation(self):
        """CP-ORG-002: El cargo se muestra por su nombre."""
        cargo = CargoFuncion.objects.create(nombre_cargo='Inspector Territorial')
        self.assertEqual(str(cargo), 'Inspector Territorial')


class FuncionarioTests(TestCase):
    def setUp(self):
        self.delegacion = Delegacion.objects.create(
            nombre='Centro', encargado='A', direccion='A', telefono='1',
            email='centro@laserena.cl', territorio='A', enfoque='A',
        )
        self.cargo = CargoFuncion.objects.create(nombre_cargo='Gestor Social')

    def test_funcionario_queda_asociado_a_delegacion_y_cargo(self):
        """CP-ORG-003: El funcionario queda asociado a su delegación y su cargo."""
        funcionario = Funcionario.objects.create(
            nombre='Ana Pérez', rut='19.000.000-1', email='ana@laserena.cl',
            delegacion=self.delegacion, cargo=self.cargo,
        )
        self.assertEqual(funcionario.delegacion, self.delegacion)
        self.assertEqual(funcionario.cargo, self.cargo)
        self.assertEqual(funcionario.rol, 'Funcionario')  # valor por defecto

    def test_rut_unico(self):
        """CP-ORG-004: La base de datos no acepta dos funcionarios con el mismo RUT."""
        Funcionario.objects.create(
            nombre='Ana Pérez', rut='19.000.000-2', email='ana2@laserena.cl',
            delegacion=self.delegacion, cargo=self.cargo,
        )
        with self.assertRaises(Exception):
            Funcionario.objects.create(
                nombre='Otra Persona', rut='19.000.000-2', email='otra@laserena.cl',
                delegacion=self.delegacion, cargo=self.cargo,
            )

    def test_no_se_puede_borrar_cargo_con_funcionarios(self):
        """CP-ORG-005: No se puede borrar un cargo con funcionarios (RESTRICT)."""
        Funcionario.objects.create(
            nombre='Ana Pérez', rut='19.000.000-3', email='ana3@laserena.cl',
            delegacion=self.delegacion, cargo=self.cargo,
        )
        with self.assertRaises(Exception):
            self.cargo.delete()


class MetaProyectoTests(TestCase):
    def test_meta_asociada_a_cargo_con_ponderador(self):
        """CP-ORG-006: La meta queda asociada a su cargo con su ponderador."""
        cargo = CargoFuncion.objects.create(nombre_cargo='Encargado de Delegación')
        meta = MetaProyecto.objects.create(
            cargo=cargo, item_medible='Actividades registradas por mes',
            valor_objetivo='20', unidad='Cantidad', ponderador=40,
        )
        self.assertEqual(meta.cargo, cargo)
        self.assertEqual(meta.ponderador, 40)
        self.assertIn('Encargado de Delegación', str(meta))

    def test_borrar_cargo_borra_sus_metas_en_cascada(self):
        """CP-ORG-007: Al borrar un cargo se borran sus metas (CASCADE)."""
        cargo = CargoFuncion.objects.create(nombre_cargo='Cargo temporal')
        MetaProyecto.objects.create(
            cargo=cargo, item_medible='Meta de prueba',
            valor_objetivo='10', ponderador=10,
        )
        cargo.delete()
        self.assertEqual(MetaProyecto.objects.count(), 0)


# ---------------------------------------------------------------------------
# Mantenedores (CRUD) de las tablas maestras de 'organizacion'.
# Casos CP-CAR, CP-FUN y CP-MET del Plan de Pruebas Unitarias.
# ---------------------------------------------------------------------------

def _delegacion(nombre='Rural'):
    return Delegacion.objects.create(
        nombre=nombre, encargado='Encargada de prueba', direccion='Calle Prat 123',
        telefono='512 206518', email=f'{nombre.lower()}@laserena.cl', territorio='Sector', enfoque='Enfoque',
    )


class CargoMantenedorTests(TestCase):
    """Unidades: CargoFuncionForm y vistas CargoCrear / CargoEditar / CargoEliminar."""

    def setUp(self):
        iniciar_sesion_admin(self.client)
        self.cargo = CargoFuncion.objects.create(nombre_cargo='Gestor Social')

    def test_cp_car_001_crear_cargo_valido(self):
        """CP-CAR-001: se crea un cargo con datos válidos y se redirige al listado."""
        respuesta = self.client.post(reverse('organizacion:cargo_crear'), {
            'nombre_cargo': 'Inspector Territorial', 'descripcion': 'Fiscaliza en terreno', 'active': 'on',
        })
        self.assertRedirects(respuesta, reverse('organizacion:cargos'))
        self.assertTrue(CargoFuncion.objects.filter(nombre_cargo='Inspector Territorial', active=True).exists())

    def test_cp_car_002_nombre_duplicado(self):
        """CP-CAR-002: no se acepta un cargo con el mismo nombre, aunque cambien mayúsculas."""
        form = CargoFuncionForm(data={'nombre_cargo': 'GESTOR SOCIAL', 'active': True})
        self.assertFalse(form.is_valid())
        self.assertIn('Ya existe un cargo con ese nombre.', form.errors['nombre_cargo'])

    def test_cp_car_003_nombre_obligatorio_e_invalido(self):
        """CP-CAR-003: el nombre del cargo es obligatorio y no admite números ni símbolos."""
        self.assertFalse(CargoFuncionForm(data={'nombre_cargo': ''}).is_valid())
        self.assertFalse(CargoFuncionForm(data={'nombre_cargo': 'Cargo#1'}).is_valid())

    def test_cp_car_004_editar_vigencia(self):
        """CP-CAR-004: se puede modificar un cargo y dejarlo como no vigente."""
        self.client.post(reverse('organizacion:cargo_editar', args=[self.cargo.pk]), {
            'nombre_cargo': 'Gestor Social', 'descripcion': 'Atiende casos sociales',
        })
        self.cargo.refresh_from_db()
        self.assertFalse(self.cargo.active)
        self.assertEqual(self.cargo.descripcion, 'Atiende casos sociales')

    def test_cp_car_005_eliminar_cargo_con_funcionarios(self):
        """CP-CAR-005: no se elimina un cargo con funcionarios; se muestra un mensaje de error."""
        Funcionario.objects.create(
            nombre='Ana Rojas', rut='12.345.678-5', email='ana@laserena.cl',
            delegacion=_delegacion(), cargo=self.cargo,
        )
        respuesta = self.client.post(reverse('organizacion:cargo_eliminar', args=[self.cargo.pk]), follow=True)
        self.assertTrue(CargoFuncion.objects.filter(pk=self.cargo.pk).exists())
        self.assertContains(respuesta, 'No se puede eliminar')

    def test_cp_car_006_eliminar_cargo_sin_funcionarios(self):
        """CP-CAR-006: un cargo sin funcionarios se elimina correctamente."""
        respuesta = self.client.post(reverse('organizacion:cargo_eliminar', args=[self.cargo.pk]))
        self.assertRedirects(respuesta, reverse('organizacion:cargos'))
        self.assertFalse(CargoFuncion.objects.filter(pk=self.cargo.pk).exists())


class FuncionarioMantenedorTests(TestCase):
    """Unidades: FuncionarioForm y vistas del mantenedor de Funcionarios."""

    def setUp(self):
        iniciar_sesion_admin(self.client)
        self.delegacion = _delegacion()
        self.cargo = CargoFuncion.objects.create(nombre_cargo='Gestor Social')
        self.datos = {
            'nombre': 'Ana María Rojas', 'rut': '12345678-5', 'email': 'Ana.Rojas@LaSerena.cl',
            'delegacion': self.delegacion.pk, 'cargo': self.cargo.pk, 'rol': 'Funcionario', 'activo': 'on',
        }

    def _existente(self, **extra):
        datos = dict(nombre='Pedro Soto', rut='7.654.321-6', email='pedro@laserena.cl',
                     delegacion=self.delegacion, cargo=self.cargo)
        datos.update(extra)
        return Funcionario.objects.create(**datos)

    def test_cp_fun_001_crear_funcionario_valido(self):
        """CP-FUN-001: se crea un funcionario; el RUT se normaliza y el correo se guarda en minúsculas."""
        respuesta = self.client.post(reverse('organizacion:funcionario_crear'), self.datos)
        self.assertRedirects(respuesta, reverse('organizacion:listado'))
        funcionario = Funcionario.objects.get(rut='12.345.678-5')
        self.assertEqual(funcionario.email, 'ana.rojas@laserena.cl')

    def test_cp_fun_002_rut_con_dv_incorrecto(self):
        """CP-FUN-002: el formulario rechaza un RUT con dígito verificador incorrecto."""
        form = FuncionarioForm(data={**self.datos, 'rut': '12.345.678-9'})
        self.assertFalse(form.is_valid())
        self.assertIn('rut', form.errors)

    def test_cp_fun_003_rut_duplicado(self):
        """CP-FUN-003: no se puede registrar dos veces el mismo RUT, aunque se escriba sin puntos."""
        self._existente(rut='12.345.678-5')
        form = FuncionarioForm(data=self.datos)
        self.assertFalse(form.is_valid())
        self.assertIn('Ya existe un funcionario con ese RUT.', form.errors['rut'])

    def test_cp_fun_004_correo_duplicado(self):
        """CP-FUN-004: no se acepta un correo ya registrado (sin distinguir mayúsculas)."""
        self._existente(email='ana.rojas@laserena.cl')
        form = FuncionarioForm(data=self.datos)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_cp_fun_005_un_solo_delegado_por_delegacion(self):
        """CP-FUN-005: una delegación no puede tener dos Delegados activos."""
        self._existente(rol='Delegado')
        form = FuncionarioForm(data={**self.datos, 'rol': 'Delegado'})
        self.assertFalse(form.is_valid())
        self.assertIn('ya tiene un Delegado activo', str(form.non_field_errors()))

    def test_cp_fun_006_solo_cargos_vigentes(self):
        """CP-FUN-006: el formulario solo ofrece cargos vigentes."""
        no_vigente = CargoFuncion.objects.create(nombre_cargo='Cargo antiguo', active=False)
        form = FuncionarioForm()
        self.assertIn(self.cargo, form.fields['cargo'].queryset)
        self.assertNotIn(no_vigente, form.fields['cargo'].queryset)

    def test_cp_fun_007_campos_obligatorios(self):
        """CP-FUN-007: nombre, RUT, correo, delegación y cargo son obligatorios."""
        form = FuncionarioForm(data={'rol': 'Funcionario'})
        self.assertFalse(form.is_valid())
        for campo in ['nombre', 'rut', 'email', 'delegacion', 'cargo']:
            self.assertIn(campo, form.errors)

    def test_cp_fun_008_editar_funcionario(self):
        """CP-FUN-008: se modifica un funcionario existente y se puede desactivar."""
        funcionario = self._existente()
        self.client.post(reverse('organizacion:funcionario_editar', args=[funcionario.pk]), {
            'nombre': 'Pedro Soto Díaz', 'rut': '7.654.321-6', 'email': 'pedro@laserena.cl',
            'delegacion': self.delegacion.pk, 'cargo': self.cargo.pk, 'rol': 'Funcionario',
        })
        funcionario.refresh_from_db()
        self.assertEqual(funcionario.nombre, 'Pedro Soto Díaz')
        self.assertFalse(funcionario.activo)

    def test_cp_fun_009_eliminar_funcionario_con_actividades(self):
        """CP-FUN-009: no se elimina un funcionario con actividades registradas (PROTECT)."""
        funcionario = self._existente()
        Actividad.objects.create(
            codigo='RUR-900', fecha=datetime.date(2026, 10, 1), delegacion=self.delegacion,
            categoria=Categoria.objects.create(nombre='Social'), descripcion='Visita', funcionario=funcionario,
        )
        respuesta = self.client.post(reverse('organizacion:funcionario_eliminar', args=[funcionario.pk]), follow=True)
        self.assertTrue(Funcionario.objects.filter(pk=funcionario.pk).exists())
        self.assertContains(respuesta, 'No se puede eliminar')

    def test_cp_fun_010_eliminar_y_ver_detalle(self):
        """CP-FUN-010: el detalle responde 200 y un funcionario sin actividades se elimina."""
        funcionario = self._existente()
        self.assertEqual(self.client.get(reverse('organizacion:funcionario_detalle', args=[funcionario.pk])).status_code, 200)
        self.client.post(reverse('organizacion:funcionario_eliminar', args=[funcionario.pk]))
        self.assertFalse(Funcionario.objects.filter(pk=funcionario.pk).exists())

    def test_cp_fun_011_busqueda_en_listado(self):
        """CP-FUN-011: el listado filtra por nombre, RUT, cargo o delegación."""
        self._existente()
        respuesta = self.client.get(reverse('organizacion:listado'), {'q': '7.654.321'})
        self.assertContains(respuesta, 'Pedro Soto')
        respuesta = self.client.get(reverse('organizacion:listado'), {'q': 'no-existe'})
        self.assertNotContains(respuesta, 'Pedro Soto')


class MetaMantenedorTests(TestCase):
    """Unidades: MetaProyectoForm (reglas RN-001 y RN-002) y vistas del mantenedor de Metas."""

    def setUp(self):
        iniciar_sesion_admin(self.client)
        self.cargo = CargoFuncion.objects.create(nombre_cargo='Encargado de Delegación')
        self.datos = {
            'cargo': self.cargo.pk, 'item_medible': 'Actividades registradas por mes',
            'valor_objetivo': '20', 'unidad': 'Cantidad', 'ponderador': 40,
        }

    def test_cp_met_001_crear_meta_valida(self):
        """CP-MET-001: se crea una meta válida y se redirige al listado."""
        respuesta = self.client.post(reverse('organizacion:meta_crear'), self.datos)
        self.assertRedirects(respuesta, reverse('organizacion:metas'))
        self.assertEqual(MetaProyecto.objects.get().ponderador, 40)

    def test_cp_met_002_valor_objetivo_cero_o_texto(self):
        """CP-MET-002: el valor objetivo debe ser un número mayor que cero (RN-002)."""
        for valor in ['0', '-5', 'veinte', '']:
            with self.subTest(valor=valor):
                form = MetaProyectoForm(data={**self.datos, 'valor_objetivo': valor})
                self.assertFalse(form.is_valid())
                self.assertIn('valor_objetivo', form.errors)

    def test_cp_met_003_porcentaje_mayor_a_100(self):
        """CP-MET-003: si la unidad es Porcentaje, el valor objetivo no puede superar 100."""
        form = MetaProyectoForm(data={**self.datos, 'unidad': 'Porcentaje', 'valor_objetivo': '120'})
        self.assertFalse(form.is_valid())
        self.assertIn('valor_objetivo', form.errors)

    def test_cp_met_004_ponderador_fuera_de_rango(self):
        """CP-MET-004: el ponderador debe estar entre 1 y 100."""
        for ponderador in [0, 101, -10]:
            with self.subTest(ponderador=ponderador):
                form = MetaProyectoForm(data={**self.datos, 'ponderador': ponderador})
                self.assertFalse(form.is_valid())
                self.assertIn('ponderador', form.errors)

    def test_cp_met_005_suma_de_ponderadores_supera_100(self):
        """CP-MET-005: la suma de ponderadores de un cargo no puede superar 100 % (RN-001)."""
        MetaProyecto.objects.create(cargo=self.cargo, item_medible='Meta A', valor_objetivo='10', ponderador=70)
        form = MetaProyectoForm(data={**self.datos, 'ponderador': 40})
        self.assertFalse(form.is_valid())
        self.assertIn('110 %', str(form.errors['ponderador']))

    def test_cp_met_006_editar_no_cuenta_su_propio_ponderador(self):
        """CP-MET-006: al editar una meta, su propio ponderador anterior no se suma dos veces."""
        meta = MetaProyecto.objects.create(cargo=self.cargo, item_medible='Meta A', valor_objetivo='10', ponderador=90)
        form = MetaProyectoForm(data={**self.datos, 'item_medible': 'Meta A', 'ponderador': 100}, instance=meta)
        self.assertTrue(form.is_valid(), form.errors)

    def test_cp_met_007_editar_y_eliminar_meta(self):
        """CP-MET-007: una meta se modifica y luego se elimina desde el mantenedor."""
        meta = MetaProyecto.objects.create(cargo=self.cargo, item_medible='Meta A', valor_objetivo='10', ponderador=10)
        self.client.post(reverse('organizacion:meta_editar', args=[meta.pk]), {**self.datos, 'ponderador': 30})
        meta.refresh_from_db()
        self.assertEqual(meta.ponderador, 30)
        self.client.post(reverse('organizacion:meta_eliminar', args=[meta.pk]))
        self.assertFalse(MetaProyecto.objects.filter(pk=meta.pk).exists())
