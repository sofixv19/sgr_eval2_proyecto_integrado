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

from .forms import CargoFuncionForm, FuncionarioForm, MetaFuncionarioForm, PeriodoForm
from .models import CargoFuncion, Funcionario, MetaProyecto, Periodo


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
        """CP-CAR-001: Se crea un cargo con datos válidos y se redirige al listado."""
        respuesta = self.client.post(reverse('organizacion:cargo_crear'), {
            'nombre_cargo': 'Inspector Territorial', 'area': 'TR', 'descripcion': 'Fiscaliza en terreno', 'active': 'on',
        })
        self.assertRedirects(respuesta, reverse('organizacion:cargos'))
        self.assertTrue(CargoFuncion.objects.filter(nombre_cargo='Inspector Territorial', active=True).exists())

    def test_cp_car_002_nombre_duplicado(self):
        """CP-CAR-002: No se acepta un cargo con el mismo nombre, aunque cambien mayúsculas."""
        form = CargoFuncionForm(data={'nombre_cargo': 'GESTOR SOCIAL', 'active': True})
        self.assertFalse(form.is_valid())
        self.assertIn('Ya existe un cargo con ese nombre.', form.errors['nombre_cargo'])

    def test_cp_car_003_nombre_obligatorio_e_invalido(self):
        """CP-CAR-003: El nombre del cargo es obligatorio y no admite números ni símbolos."""
        self.assertFalse(CargoFuncionForm(data={'nombre_cargo': ''}).is_valid())
        self.assertFalse(CargoFuncionForm(data={'nombre_cargo': 'Cargo#1'}).is_valid())

    def test_cp_car_004_editar_vigencia(self):
        """CP-CAR-004: Se puede modificar un cargo y dejarlo como no vigente."""
        self.client.post(reverse('organizacion:cargo_editar', args=[self.cargo.pk]), {
            'nombre_cargo': 'Gestor Social', 'area': 'SO', 'descripcion': 'Atiende casos sociales',
        })
        self.cargo.refresh_from_db()
        self.assertFalse(self.cargo.active)
        self.assertEqual(self.cargo.descripcion, 'Atiende casos sociales')

    def test_cp_car_005_eliminar_cargo_con_funcionarios(self):
        """CP-CAR-005: No se elimina un cargo con funcionarios; se muestra un mensaje de error."""
        Funcionario.objects.create(
            nombre='Ana Rojas', rut='12.345.678-5', email='ana@laserena.cl',
            delegacion=_delegacion(), cargo=self.cargo,
        )
        respuesta = self.client.post(reverse('organizacion:cargo_eliminar', args=[self.cargo.pk]), follow=True)
        self.assertTrue(CargoFuncion.objects.filter(pk=self.cargo.pk).exists())
        self.assertContains(respuesta, 'No se puede eliminar')

    def test_cp_car_006_eliminar_cargo_sin_funcionarios(self):
        """CP-CAR-006: Un cargo sin funcionarios se elimina correctamente."""
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
        """CP-FUN-001: Se crea un funcionario con su cuenta de acceso; el RUT se normaliza y el correo queda en minúsculas."""
        respuesta = self.client.post(reverse('organizacion:funcionario_crear'), self.datos, follow=True)
        funcionario = Funcionario.objects.get(rut='12.345.678-5')
        self.assertRedirects(respuesta, reverse('organizacion:funcionario_detalle', args=[funcionario.pk]))
        self.assertEqual(funcionario.email, 'ana.rojas@laserena.cl')
        self.assertIsNotNone(funcionario.usuario)
        self.assertContains(respuesta, 'Credenciales para entregar')

    def test_cp_fun_002_rut_con_dv_incorrecto(self):
        """CP-FUN-002: El formulario rechaza un RUT con dígito verificador incorrecto."""
        form = FuncionarioForm(data={**self.datos, 'rut': '12.345.678-9'})
        self.assertFalse(form.is_valid())
        self.assertIn('rut', form.errors)

    def test_cp_fun_003_rut_duplicado(self):
        """CP-FUN-003: No se puede registrar dos veces el mismo RUT, aunque se escriba sin puntos."""
        self._existente(rut='12.345.678-5')
        form = FuncionarioForm(data=self.datos)
        self.assertFalse(form.is_valid())
        self.assertIn('Ya existe un funcionario con ese RUT.', form.errors['rut'])

    def test_cp_fun_004_correo_duplicado(self):
        """CP-FUN-004: No se acepta un correo ya registrado (sin distinguir mayúsculas)."""
        self._existente(email='ana.rojas@laserena.cl')
        form = FuncionarioForm(data=self.datos)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_cp_fun_005_un_solo_delegado_por_delegacion(self):
        """CP-FUN-005: Una delegación no puede tener dos Delegados activos."""
        self._existente(rol='Delegado')
        form = FuncionarioForm(data={**self.datos, 'rol': 'Delegado'})
        self.assertFalse(form.is_valid())
        self.assertIn('ya tiene un Delegado activo', str(form.non_field_errors()))

    def test_cp_fun_006_solo_cargos_vigentes(self):
        """CP-FUN-006: El formulario solo ofrece cargos vigentes."""
        no_vigente = CargoFuncion.objects.create(nombre_cargo='Cargo antiguo', active=False)
        form = FuncionarioForm()
        self.assertIn(self.cargo, form.fields['cargo'].queryset)
        self.assertNotIn(no_vigente, form.fields['cargo'].queryset)

    def test_cp_fun_007_campos_obligatorios(self):
        """CP-FUN-007: Nombre, RUT, correo, delegación y cargo son obligatorios."""
        form = FuncionarioForm(data={'rol': 'Funcionario'})
        self.assertFalse(form.is_valid())
        for campo in ['nombre', 'rut', 'email', 'delegacion', 'cargo']:
            self.assertIn(campo, form.errors)

    def test_cp_fun_008_editar_funcionario(self):
        """CP-FUN-008: Se modifica un funcionario existente y se puede desactivar."""
        funcionario = self._existente()
        self.client.post(reverse('organizacion:funcionario_editar', args=[funcionario.pk]), {
            'nombre': 'Pedro Soto Díaz', 'rut': '7.654.321-6', 'email': 'pedro@laserena.cl',
            'delegacion': self.delegacion.pk, 'cargo': self.cargo.pk, 'rol': 'Funcionario',
        })
        funcionario.refresh_from_db()
        self.assertEqual(funcionario.nombre, 'Pedro Soto Díaz')
        self.assertFalse(funcionario.activo)

    def test_cp_fun_009_eliminar_funcionario_con_actividades(self):
        """CP-FUN-009: No se elimina un funcionario con actividades registradas (PROTECT)."""
        funcionario = self._existente()
        Actividad.objects.create(
            codigo='RUR-900', fecha=datetime.date(2026, 10, 1), delegacion=self.delegacion,
            categoria=Categoria.objects.create(nombre='Social'), descripcion='Visita', funcionario=funcionario,
        )
        respuesta = self.client.post(reverse('organizacion:funcionario_eliminar', args=[funcionario.pk]), follow=True)
        self.assertTrue(Funcionario.objects.filter(pk=funcionario.pk).exists())
        self.assertContains(respuesta, 'No se puede eliminar')

    def test_cp_fun_010_eliminar_y_ver_detalle(self):
        """CP-FUN-010: El detalle responde 200 y un funcionario sin actividades se elimina."""
        funcionario = self._existente()
        self.assertEqual(self.client.get(reverse('organizacion:funcionario_detalle', args=[funcionario.pk])).status_code, 200)
        self.client.post(reverse('organizacion:funcionario_eliminar', args=[funcionario.pk]))
        self.assertFalse(Funcionario.objects.filter(pk=funcionario.pk).exists())

    def test_cp_fun_011_busqueda_en_listado(self):
        """CP-FUN-011: El listado filtra por nombre, RUT, cargo o delegación."""
        self._existente()
        respuesta = self.client.get(reverse('organizacion:listado'), {'q': '7.654.321'})
        self.assertContains(respuesta, 'Pedro Soto')
        respuesta = self.client.get(reverse('organizacion:listado'), {'q': 'no-existe'})
        self.assertNotContains(respuesta, 'Pedro Soto')


class MetaMantenedorTests(TestCase):
    """Unidades: MetaFuncionarioForm (reglas RN-001 y RN-002) y vistas del mantenedor de Metas.
    Desde la revisión de la Evaluación 2 la meta se asigna a un funcionario y mide una categoría."""

    def setUp(self):
        iniciar_sesion_admin(self.client)
        self.cargo = CargoFuncion.objects.create(nombre_cargo='Encargado de Delegación')
        self.funcionario = Funcionario.objects.create(
            nombre='Ana Rojas', rut='12.345.678-5', email='ana.meta@laserena.cl',
            delegacion=_delegacion(), cargo=self.cargo)
        self.categoria = Categoria.objects.create(nombre='Social')
        self.otra_categoria = Categoria.objects.create(nombre='Seguridad')
        Periodo.objects.all().delete()  # la migración 0005 crea un período inicial
        self.periodo = Periodo.objects.create(
            nombre='Segundo semestre 2026', fecha_inicio=datetime.date(2026, 7, 1),
            fecha_fin=datetime.date(2026, 12, 31), estado='Abierto',
        )
        self.datos = {
            'funcionario': self.funcionario.pk, 'periodo': self.periodo.pk, 'categoria': self.categoria.pk,
            'valor_objetivo': '20', 'ponderador': 40,
        }

    def _meta(self, ponderador, categoria=None, periodo=None):
        return MetaProyecto.objects.create(
            cargo=self.cargo, funcionario=self.funcionario, periodo=periodo or self.periodo,
            categoria=categoria or self.otra_categoria, item_medible='Meta A', valor_objetivo='10', ponderador=ponderador)

    def test_cp_met_001_crear_meta_valida(self):
        """CP-MET-001: Se asigna una meta válida a un funcionario; el cargo y el ítem se completan solos."""
        respuesta = self.client.post(reverse('organizacion:meta_crear'), self.datos)
        self.assertRedirects(respuesta, reverse('organizacion:metas'))
        meta = MetaProyecto.objects.get()
        self.assertEqual((meta.ponderador, meta.cargo, meta.item_medible), (40, self.cargo, 'Social'))

    def test_cp_met_002_valor_objetivo_cero_o_texto(self):
        """CP-MET-002: La meta debe ser un número mayor que cero (RN-002)."""
        for valor in ['0', '-5', 'veinte', '']:
            with self.subTest(valor=valor):
                form = MetaFuncionarioForm(data={**self.datos, 'valor_objetivo': valor})
                self.assertFalse(form.is_valid())
                self.assertIn('valor_objetivo', form.errors)

    def test_cp_met_003_porcentaje_mayor_a_100(self):
        """CP-MET-003: Un funcionario no puede tener dos metas de la misma categoría en el mismo período."""
        self._meta(30, categoria=self.categoria)
        form = MetaFuncionarioForm(data=self.datos)
        self.assertFalse(form.is_valid())
        self.assertIn('categoria', form.errors)

    def test_cp_met_004_ponderador_fuera_de_rango(self):
        """CP-MET-004: El ponderador debe estar entre 1 y 100."""
        for ponderador in [0, 101, -10]:
            with self.subTest(ponderador=ponderador):
                form = MetaFuncionarioForm(data={**self.datos, 'ponderador': ponderador})
                self.assertFalse(form.is_valid())
                self.assertIn('ponderador', form.errors)

    def test_cp_met_005_suma_de_ponderadores_supera_100(self):
        """CP-MET-005: La suma de ponderadores de un funcionario en un período no puede superar 100 % (RN-001)."""
        self._meta(70)
        form = MetaFuncionarioForm(data={**self.datos, 'ponderador': 40})
        self.assertFalse(form.is_valid())
        self.assertIn('110 %', str(form.errors['ponderador']))

    def test_cp_met_006_editar_no_cuenta_su_propio_ponderador(self):
        """CP-MET-006: Al editar una meta, su propio ponderador anterior no se suma dos veces."""
        meta = self._meta(90, categoria=self.categoria)
        form = MetaFuncionarioForm(data={**self.datos, 'ponderador': 100}, instance=meta)
        self.assertTrue(form.is_valid(), form.errors)

    def test_cp_met_007_editar_y_eliminar_meta(self):
        """CP-MET-007: Una meta se modifica y luego se elimina desde el mantenedor."""
        meta = self._meta(10, categoria=self.categoria)
        self.client.post(reverse('organizacion:meta_editar', args=[meta.pk]), {**self.datos, 'ponderador': 30})
        meta.refresh_from_db()
        self.assertEqual(meta.ponderador, 30)
        self.client.post(reverse('organizacion:meta_eliminar', args=[meta.pk]))
        self.assertFalse(MetaProyecto.objects.filter(pk=meta.pk).exists())

    def test_cp_met_008_mismo_cargo_otro_periodo(self):
        """CP-MET-008: Los ponderadores se suman por período: en otro período el funcionario parte desde cero."""
        self._meta(90)
        otro = Periodo.objects.create(nombre='Primer semestre 2027', fecha_inicio=datetime.date(2027, 1, 1),
                                      fecha_fin=datetime.date(2027, 6, 30))
        form = MetaFuncionarioForm(data={**self.datos, 'periodo': otro.pk, 'ponderador': 60})
        self.assertTrue(form.is_valid(), form.errors)

    def test_cp_met_009_periodo_obligatorio_y_no_cerrado(self):
        """CP-MET-009: El período es obligatorio y no se pueden crear metas en un período Cerrado."""
        self.assertIn('periodo', MetaFuncionarioForm(data={**self.datos, 'periodo': ''}).errors)
        cerrado = Periodo.objects.create(nombre='Primer semestre 2026', fecha_inicio=datetime.date(2026, 1, 1),
                                         fecha_fin=datetime.date(2026, 6, 30), estado='Cerrado')
        self.assertNotIn(cerrado, MetaFuncionarioForm().fields['periodo'].queryset)


class PeriodoMantenedorTests(TestCase):
    """Unidades: PeriodoForm (fechas, solapamiento, estados, RN-013) y vistas del mantenedor de Períodos."""

    def setUp(self):
        iniciar_sesion_admin(self.client)
        Periodo.objects.all().delete()  # la migración 0005 crea un período inicial
        self.periodo = Periodo.objects.create(
            nombre='Segundo semestre 2026', fecha_inicio=datetime.date(2026, 7, 1),
            fecha_fin=datetime.date(2026, 12, 31), estado='Abierto',
        )
        self.datos = {'nombre': 'Primer semestre 2027', 'fecha_inicio': '2027-01-01', 'fecha_fin': '2027-06-30',
                      'estado': 'Planificado'}

    def test_cp_per_001_crear_periodo_valido(self):
        """CP-PER-001: Se crea un período válido y se redirige al listado."""
        respuesta = self.client.post(reverse('organizacion:periodo_crear'), self.datos)
        self.assertRedirects(respuesta, reverse('organizacion:periodos'))
        self.assertTrue(Periodo.objects.filter(nombre='Primer semestre 2027').exists())

    def test_cp_per_002_campos_obligatorios(self):
        """CP-PER-002: Nombre, fechas y estado son obligatorios."""
        form = PeriodoForm(data={})
        self.assertFalse(form.is_valid())
        for campo in ['nombre', 'fecha_inicio', 'fecha_fin', 'estado']:
            self.assertIn(campo, form.errors)

    def test_cp_per_003_fecha_fin_anterior(self):
        """CP-PER-003: La fecha de término debe ser posterior a la de inicio."""
        form = PeriodoForm(data={**self.datos, 'fecha_fin': '2026-12-31'})
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_fin', form.errors)

    def test_cp_per_004_periodos_solapados(self):
        """CP-PER-004: No se acepta un período cuyas fechas se cruzan con otro."""
        form = PeriodoForm(data={**self.datos, 'fecha_inicio': '2026-12-01', 'fecha_fin': '2027-03-31'})
        self.assertFalse(form.is_valid())
        self.assertIn('se cruzan', str(form.non_field_errors()))

    def test_cp_per_005_un_solo_periodo_abierto(self):
        """CP-PER-005: Solo puede haber un período Abierto a la vez."""
        form = PeriodoForm(data={**self.datos, 'estado': 'Abierto'})
        self.assertFalse(form.is_valid())
        self.assertIn('estado', form.errors)

    def test_cp_per_006_periodo_cerrado_no_se_modifica(self):
        """CP-PER-006: Un período Cerrado no se puede modificar sin reabrirlo (RN-013)."""
        cerrado = Periodo.objects.create(nombre='Primer semestre 2026', fecha_inicio=datetime.date(2026, 1, 1),
                                         fecha_fin=datetime.date(2026, 6, 30), estado='Cerrado')
        form = PeriodoForm(data={'nombre': 'Primer semestre 2026 corregido', 'fecha_inicio': '2026-01-01',
                                 'fecha_fin': '2026-06-30', 'estado': 'Cerrado'}, instance=cerrado)
        self.assertFalse(form.is_valid())
        self.assertIn('Cerrado', str(form.non_field_errors()))

    def test_cp_per_007_editar_periodo(self):
        """CP-PER-007: Se modifica el estado de un período desde el mantenedor."""
        self.client.post(reverse('organizacion:periodo_editar', args=[self.periodo.pk]), {
            'nombre': 'Segundo semestre 2026', 'fecha_inicio': '2026-07-01', 'fecha_fin': '2026-12-31', 'estado': 'Cerrado',
        })
        self.periodo.refresh_from_db()
        self.assertEqual(self.periodo.estado, 'Cerrado')

    def test_cp_per_008_eliminar_periodo_con_metas(self):
        """CP-PER-008: Un período con metas no se elimina (PROTECT) y uno sin metas sí."""
        cargo = CargoFuncion.objects.create(nombre_cargo='Gestor Social')
        MetaProyecto.objects.create(
            cargo=cargo, periodo=self.periodo, item_medible='Meta A', valor_objetivo='10', ponderador=10)
        respuesta = self.client.post(reverse('organizacion:periodo_eliminar', args=[self.periodo.pk]), follow=True)
        self.assertTrue(Periodo.objects.filter(pk=self.periodo.pk).exists())
        self.assertContains(respuesta, 'No se puede eliminar')
        libre = Periodo.objects.create(nombre='Primer semestre 2027', fecha_inicio=datetime.date(2027, 1, 1),
                                       fecha_fin=datetime.date(2027, 6, 30))
        self.client.post(reverse('organizacion:periodo_eliminar', args=[libre.pk]))
        self.assertFalse(Periodo.objects.filter(pk=libre.pk).exists())
