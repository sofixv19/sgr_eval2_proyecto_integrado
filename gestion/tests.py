"""
Pruebas unitarias e integrales de la app 'gestion'.

Cubren el criterio 2.1.6.13 de la rúbrica de Evaluación 2 (Unidad 2):
pruebas unitarias (modelo y relaciones) e integrales (vistas, filtros y
agregaciones ORM) sobre el módulo de actividades.

Tras fusionar el proyecto con el del compañero de equipo, 'funcionario'
es una relación real hacia 'organizacion.Funcionario' (antes era texto
libre), por lo que las pruebas crean también un Cargo y un Funcionario.

Se agregan además (retroalimentación del profesor Ciceo, Evaluación 1):
- ActividadValidacionTests: la regla de negocio "solo un Delegado valida,
  y no puede validar quien registró la actividad" (clean() / marcar_validado()).
- ActividadCrudTests: el CRUD real de Actividad (antes era un marcador de
  posición 'en_construccion.html').
- ActividadValidacionVistaTests: el formulario de validación expuesto en
  la vista de detalle.
"""
import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from comun.pruebas import iniciar_sesion_admin

from delegaciones.models import Delegacion
from organizacion.models import CargoFuncion, Funcionario
from .forms import CategoriaForm
from .models import Actividad, Categoria


def crear_funcionario(nombre, rut, delegacion, cargo=None, rol='Funcionario'):
    """Helper de prueba: crea un Funcionario con un cargo asociado."""
    if cargo is None:
        cargo, _ = CargoFuncion.objects.get_or_create(nombre_cargo='Funcionario de prueba')
    return Funcionario.objects.create(
        nombre=nombre, rut=rut, email=f'{rut}@laserena.cl',
        delegacion=delegacion, cargo=cargo, rol=rol,
    )


class ActividadModeloTests(TestCase):
    """Pruebas unitarias: relaciones e integridad del modelo Actividad."""

    def setUp(self):
        self.delegacion = Delegacion.objects.create(
            nombre='Centro', encargado='A', direccion='A', telefono='1',
            email='centro@laserena.cl', territorio='A', enfoque='A',
        )
        self.categoria = Categoria.objects.create(nombre='Social')
        self.funcionario = crear_funcionario('F. Prueba', '20.000.000-1', self.delegacion)

    def test_actividad_queda_asociada_a_delegacion_categoria_y_funcionario(self):
        """CP-ACT-001: La actividad queda asociada a su delegación, categoría y funcionario."""
        actividad = Actividad.objects.create(
            codigo='ACT-001',
            fecha=datetime.date(2026, 9, 1),
            delegacion=self.delegacion,
            categoria=self.categoria,
            descripcion='Solicitud de prueba',
            funcionario=self.funcionario,
        )
        self.assertEqual(actividad.delegacion, self.delegacion)
        self.assertEqual(actividad.categoria, self.categoria)
        self.assertEqual(actividad.funcionario, self.funcionario)
        self.assertEqual(actividad.estado, Actividad.Estado.PENDIENTE)

    def test_codigo_unico(self):
        """CP-ACT-002: El código de la actividad es único."""
        Actividad.objects.create(
            codigo='ACT-DUP', fecha=datetime.date(2026, 9, 1),
            delegacion=self.delegacion, categoria=self.categoria,
            descripcion='A', funcionario=self.funcionario,
        )
        with self.assertRaises(Exception):
            Actividad.objects.create(
                codigo='ACT-DUP', fecha=datetime.date(2026, 9, 2),
                delegacion=self.delegacion, categoria=self.categoria,
                descripcion='B', funcionario=self.funcionario,
            )

    def test_borrar_delegacion_borra_sus_actividades_en_cascada(self):
        """CP-ACT-003: Al borrar una delegación se borran sus actividades (CASCADE)."""
        delegacion_aislada = Delegacion.objects.create(
            nombre='Delegación aislada', encargado='A', direccion='A',
            telefono='1', email='aislada@laserena.cl', territorio='A', enfoque='A',
        )
        Actividad.objects.create(
            codigo='ACT-002', fecha=datetime.date(2026, 9, 1),
            delegacion=delegacion_aislada, categoria=self.categoria,
            descripcion='A', funcionario=self.funcionario,
        )
        delegacion_aislada.delete()
        self.assertEqual(Actividad.objects.filter(codigo='ACT-002').count(), 0)

    def test_no_se_puede_borrar_categoria_en_uso(self):
        """CP-ACT-004: No se puede borrar una categoría usada por actividades (PROTECT)."""
        Actividad.objects.create(
            codigo='ACT-003', fecha=datetime.date(2026, 9, 1),
            delegacion=self.delegacion, categoria=self.categoria,
            descripcion='A', funcionario=self.funcionario,
        )
        with self.assertRaises(Exception):
            self.categoria.delete()

    def test_no_se_puede_borrar_funcionario_en_uso(self):
        """CP-ACT-005: No se puede borrar un funcionario con actividades (PROTECT)."""
        Actividad.objects.create(
            codigo='ACT-004', fecha=datetime.date(2026, 9, 1),
            delegacion=self.delegacion, categoria=self.categoria,
            descripcion='A', funcionario=self.funcionario,
        )
        with self.assertRaises(Exception):
            self.funcionario.delete()


class ActividadVistasTests(TestCase):
    """Pruebas integrales sobre el listado y sus filtros (?estado=, ?q=)."""

    def setUp(self):
        iniciar_sesion_admin(self.client)
        delegacion = Delegacion.objects.create(
            nombre='Rural', encargado='A', direccion='A', telefono='1',
            email='rural@laserena.cl', territorio='A', enfoque='A',
        )
        categoria = Categoria.objects.create(nombre='Seguridad')
        funcionario_a = crear_funcionario('Funcionario A', '20.000.000-2', delegacion)
        funcionario_b = crear_funcionario('Funcionario B', '20.000.000-3', delegacion)
        Actividad.objects.create(
            codigo='ACT-100', fecha=datetime.date(2026, 9, 1),
            delegacion=delegacion, categoria=categoria,
            descripcion='Pendiente de revisión', funcionario=funcionario_a,
            estado=Actividad.Estado.PENDIENTE,
        )
        Actividad.objects.create(
            codigo='ACT-101', fecha=datetime.date(2026, 9, 2),
            delegacion=delegacion, categoria=categoria,
            descripcion='Ya resuelta', funcionario=funcionario_b,
            estado=Actividad.Estado.REALIZADO,
        )

    def test_listado_sin_filtro_muestra_todo(self):
        """CP-ACT-006: El listado de actividades sin filtro muestra todas."""
        response = self.client.get(reverse('gestion:listado'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 2)

    def test_filtro_por_estado(self):
        """CP-ACT-007: El filtro por estado muestra solo las actividades de ese estado."""
        response = self.client.get(
            reverse('gestion:listado'), {'estado': 'Realizado'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 1)
        self.assertContains(response, 'ACT-101')
        self.assertNotContains(response, 'ACT-100')

    def test_busqueda_por_codigo(self):
        """CP-ACT-008: La búsqueda por código encuentra la actividad."""
        response = self.client.get(reverse('gestion:listado'), {'q': 'ACT-100'})
        self.assertEqual(response.context['total'], 1)


class ActividadValidacionTests(TestCase):
    """Pruebas unitarias de la regla de negocio pedida por el profesor
    Ciceo (retroalimentación de la Evaluación 1): una actividad solo la
    puede validar un Funcionario con rol 'Delegado', y nunca el propio
    Funcionario que la registró (no se puede autovalidar ni validar un par
    del mismo nivel jerárquico)."""

    def setUp(self):
        self.delegacion = Delegacion.objects.create(
            nombre='Centro Validación', encargado='A', direccion='A', telefono='1',
            email='centrov@laserena.cl', territorio='A', enfoque='A',
        )
        self.categoria = Categoria.objects.create(nombre='Validación')
        self.funcionario = crear_funcionario(
            'Funcionario Operativo', '21.000.000-1', self.delegacion, rol='Funcionario',
        )
        self.delegado = crear_funcionario(
            'Delegado de Delegación', '21.000.000-2', self.delegacion, rol='Delegado',
        )
        self.otro_funcionario = crear_funcionario(
            'Otro Funcionario (par)', '21.000.000-3', self.delegacion, rol='Funcionario',
        )
        self.actividad = Actividad.objects.create(
            codigo='ACT-VAL-001', fecha=datetime.date(2026, 10, 1),
            delegacion=self.delegacion, categoria=self.categoria,
            descripcion='Actividad para pruebas de validación',
            funcionario=self.funcionario,
        )

    def test_un_delegado_puede_validar(self):
        """CP-VLD-001: Un Delegado puede validar la actividad de un funcionario."""
        self.actividad.marcar_validado(self.delegado)
        self.actividad.refresh_from_db()
        self.assertTrue(self.actividad.validado)
        self.assertEqual(self.actividad.validado_por, self.delegado)
        self.assertIsNotNone(self.actividad.fecha_validacion)

    def test_el_funcionario_no_puede_autovalidarse(self):
        """CP-VLD-002: El funcionario no puede validar su propia actividad."""
        with self.assertRaises(ValueError):
            self.actividad.marcar_validado(self.funcionario)

    def test_un_par_funcionario_no_puede_validar(self):
        """CP-VLD-003: Un funcionario del mismo nivel (no Delegado) no puede validar."""
        with self.assertRaises(ValueError):
            self.actividad.marcar_validado(self.otro_funcionario)

    def test_clean_rechaza_validado_por_sin_rol_delegado(self):
        """CP-VLD-004: El método clean() rechaza un validador sin rol Delegado."""
        self.actividad.validado_por = self.otro_funcionario
        with self.assertRaises(ValidationError):
            self.actividad.clean()

    def test_clean_rechaza_autovalidacion(self):
        """CP-VLD-005: El método clean() rechaza la autovalidación."""
        self.actividad.validado_por = self.funcionario
        with self.assertRaises(ValidationError):
            self.actividad.clean()

    def test_clean_acepta_delegado_valido(self):
        """CP-VLD-006: El método clean() acepta un Delegado válido."""
        self.actividad.validado_por = self.delegado
        self.actividad.clean()  # no debe lanzar excepción


class ActividadCrudTests(TestCase):
    """Pruebas integrales del CRUD real de Actividad (Evaluación Sumativa
    N.º 3): antes estas tres rutas solo mostraban 'en_construccion.html'."""

    def setUp(self):
        iniciar_sesion_admin(self.client)
        self.delegacion = Delegacion.objects.create(
            nombre='Delegación CRUD', encargado='A', direccion='A', telefono='1',
            email='crud@laserena.cl', territorio='A', enfoque='A',
        )
        self.categoria = Categoria.objects.create(nombre='Categoría CRUD')
        self.funcionario = crear_funcionario('Funcionario CRUD', '22.000.000-1', self.delegacion)
        self.actividad = Actividad.objects.create(
            codigo='ACT-CRUD-001', fecha=datetime.date(2026, 10, 1),
            delegacion=self.delegacion, categoria=self.categoria,
            descripcion='Actividad original', funcionario=self.funcionario,
        )

    def test_crear_actividad_mediante_formulario(self):
        """CP-ACT-009: Se registra una actividad desde el formulario."""
        datos = {
            'codigo': 'ACT-CRUD-NUEVA', 'fecha': '2026-10-05',
            'delegacion': self.delegacion.id, 'categoria': self.categoria.id,
            'funcionario': self.funcionario.id, 'estado': Actividad.Estado.PENDIENTE,
            'descripcion': 'Creada desde el formulario real',
            'solicitud_problema': '', 'contacto': '', 'telefono_contacto': '',
        }
        response = self.client.post(reverse('gestion:crear'), datos)
        actividad = Actividad.objects.get(codigo='ACT-CRUD-NUEVA')
        self.assertRedirects(response, reverse('gestion:detalle', args=[actividad.id]))
        self.assertEqual(actividad.descripcion, 'Creada desde el formulario real')

    def test_editar_actividad_mediante_formulario(self):
        """CP-ACT-010: Se modifica una actividad desde el formulario."""
        datos = {
            'codigo': self.actividad.codigo, 'fecha': '2026-10-01',
            'delegacion': self.delegacion.id, 'categoria': self.categoria.id,
            'funcionario': self.funcionario.id, 'estado': Actividad.Estado.EN_PROCESO,
            'descripcion': 'Descripción modificada', 'solicitud_problema': '',
            'contacto': '', 'telefono_contacto': '',
        }
        self.client.post(reverse('gestion:editar', args=[self.actividad.id]), datos)
        self.actividad.refresh_from_db()
        self.assertEqual(self.actividad.descripcion, 'Descripción modificada')
        self.assertEqual(self.actividad.estado, Actividad.Estado.EN_PROCESO)

    def test_eliminar_actividad_mediante_formulario(self):
        """CP-ACT-011: Se elimina una actividad desde el formulario."""
        response = self.client.post(reverse('gestion:eliminar', args=[self.actividad.id]))
        self.assertRedirects(response, reverse('gestion:listado'))
        self.assertFalse(Actividad.objects.filter(id=self.actividad.id).exists())

    def test_eliminar_muestra_confirmacion_antes_de_borrar(self):
        """CP-ACT-012: La petición GET de eliminar actividad solo muestra la confirmación."""
        response = self.client.get(reverse('gestion:eliminar', args=[self.actividad.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Actividad.objects.filter(id=self.actividad.id).exists())


class ActividadValidacionVistaTests(TestCase):
    """Pruebas integrales del formulario de validación en gestion/detalle.html."""

    def setUp(self):
        iniciar_sesion_admin(self.client)
        self.delegacion = Delegacion.objects.create(
            nombre='Delegación Vista Val.', encargado='A', direccion='A', telefono='1',
            email='vistaval@laserena.cl', territorio='A', enfoque='A',
        )
        self.categoria = Categoria.objects.create(nombre='Categoría Vista Val.')
        self.funcionario = crear_funcionario('Funcionario Vista', '23.000.000-1', self.delegacion)
        self.delegado = crear_funcionario(
            'Delegado Vista', '23.000.000-2', self.delegacion, rol='Delegado',
        )
        self.actividad = Actividad.objects.create(
            codigo='ACT-VISTA-001', fecha=datetime.date(2026, 10, 1),
            delegacion=self.delegacion, categoria=self.categoria,
            descripcion='Pendiente de validar', funcionario=self.funcionario,
        )

    def test_detalle_muestra_formulario_cuando_no_esta_validada(self):
        """CP-VLD-007: La ficha de una actividad pendiente muestra el formulario de validación."""
        response = self.client.get(reverse('gestion:detalle', args=[self.actividad.id]))
        self.assertContains(response, 'Validar esta actividad')

    def test_detalle_no_muestra_formulario_cuando_ya_esta_validada(self):
        """CP-VLD-008: La ficha de una actividad validada no muestra el formulario."""
        self.actividad.marcar_validado(self.delegado)
        response = self.client.get(reverse('gestion:detalle', args=[self.actividad.id]))
        self.assertNotContains(response, 'Validar esta actividad')
        self.assertContains(response, 'Validado')

    def test_validar_desde_la_vista_aplica_la_regla_de_negocio(self):
        """CP-VLD-009: Validar desde la pantalla registra Delegado y fecha."""
        response = self.client.post(
            reverse('gestion:detalle', args=[self.actividad.id]),
            {'validar': '1', 'validado_por': self.delegado.id},
        )
        self.assertRedirects(response, reverse('gestion:detalle', args=[self.actividad.id]))
        self.actividad.refresh_from_db()
        self.assertTrue(self.actividad.validado)
        self.assertEqual(self.actividad.validado_por, self.delegado)

    def test_validar_rechaza_autovalidacion_desde_la_vista(self):
        """CP-VLD-010: La pantalla rechaza que el funcionario se valide a sí mismo."""
        response = self.client.post(
            reverse('gestion:detalle', args=[self.actividad.id]),
            {'validar': '1', 'validado_por': self.funcionario.id},
        )
        self.assertEqual(response.status_code, 200)  # se queda en el formulario con el error
        self.actividad.refresh_from_db()
        self.assertFalse(self.actividad.validado)


# ---------------------------------------------------------------------------
# Mantenedor de la tabla maestra Categoría (casos CP-CAT del Plan de Pruebas)
# ---------------------------------------------------------------------------

class CategoriaMantenedorTests(TestCase):
    """Unidades: CategoriaForm y vistas CategoriaListado / Crear / Editar / Eliminar."""

    def setUp(self):
        iniciar_sesion_admin(self.client)
        self.categoria = Categoria.objects.create(nombre='Social', descripcion='Casos sociales')

    def test_cp_cat_001_crear_categoria_valida(self):
        """CP-CAT-001: se crea una categoría con datos válidos y aparece el mensaje de éxito."""
        respuesta = self.client.post(reverse('gestion:categoria_crear'), {
            'nombre': 'Medio Ambiente', 'descripcion': 'Limpieza de playas',
        }, follow=True)
        self.assertTrue(Categoria.objects.filter(nombre='Medio Ambiente').exists())
        self.assertContains(respuesta, 'creado/a correctamente')

    def test_cp_cat_002_nombre_duplicado(self):
        """CP-CAT-002: no se acepta una categoría repetida, aunque cambien mayúsculas."""
        form = CategoriaForm(data={'nombre': 'SOCIAL'})
        self.assertFalse(form.is_valid())
        self.assertIn('Ya existe una categoría con ese nombre.', form.errors['nombre'])

    def test_cp_cat_003_nombre_obligatorio_y_formato(self):
        """CP-CAT-003: el nombre es obligatorio, de al menos 3 letras y sin números."""
        for nombre in ['', 'Ab', 'Categoría 2']:
            with self.subTest(nombre=nombre):
                self.assertFalse(CategoriaForm(data={'nombre': nombre}).is_valid())

    def test_cp_cat_004_editar_categoria(self):
        """CP-CAT-004: se modifica el nombre y la descripción de una categoría."""
        self.client.post(reverse('gestion:categoria_editar', args=[self.categoria.pk]), {
            'nombre': 'Social y Comunitaria', 'descripcion': 'Actualizada',
        })
        self.categoria.refresh_from_db()
        self.assertEqual(self.categoria.nombre, 'Social y Comunitaria')

    def test_cp_cat_005_eliminar_categoria_sin_uso(self):
        """CP-CAT-005: una categoría sin actividades se elimina y se redirige al listado."""
        respuesta = self.client.post(reverse('gestion:categoria_eliminar', args=[self.categoria.pk]))
        self.assertRedirects(respuesta, reverse('gestion:categorias'))
        self.assertFalse(Categoria.objects.filter(pk=self.categoria.pk).exists())

    def test_cp_cat_006_eliminar_categoria_en_uso(self):
        """CP-CAT-006: una categoría usada por actividades no se elimina; se informa el error sin caer el sistema."""
        delegacion = Delegacion.objects.create(
            nombre='Rural', encargado='E', direccion='D', telefono='512206518',
            email='r@laserena.cl', territorio='T', enfoque='E',
        )
        Actividad.objects.create(
            codigo='RUR-901', fecha=datetime.date(2026, 10, 1), delegacion=delegacion, categoria=self.categoria,
            descripcion='Visita', funcionario=crear_funcionario('Ana Rojas', '12.345.678-5', delegacion),
        )
        respuesta = self.client.post(reverse('gestion:categoria_eliminar', args=[self.categoria.pk]), follow=True)
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())
        self.assertContains(respuesta, 'No se puede eliminar')

    def test_cp_cat_007_listado_con_busqueda(self):
        """CP-CAT-007: el listado muestra las categorías y filtra por texto."""
        Categoria.objects.create(nombre='Seguridad')
        respuesta = self.client.get(reverse('gestion:categorias'), {'q': 'segu'})
        self.assertContains(respuesta, 'Seguridad')
        self.assertNotContains(respuesta, 'Casos sociales')
