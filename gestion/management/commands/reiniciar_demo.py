"""
Deja la base de datos de DEMOSTRACIÓN como recién instalada (versión 2.1.2).

Borra todo lo que se creó probando el sistema y vuelve a cargar el equipo de
ejemplo de `cargar_datos_iniciales`:

- Borra actividades, evidencias (también los archivos), compromisos, metas,
  felicitaciones, ausencias y organizaciones comunitarias.
- Borra los funcionarios que no son del equipo de ejemplo y sus cuentas.
- Borra las delegaciones que no están en data/delegaciones.json y los
  períodos de prueba (deja abierto "Segundo semestre 2026").
- Conserva las 5 cuentas de demostración CON su contraseña actual, los
  superusuarios, los cargos y las categorías.
- Conserva los nombres que el equipo le haya puesto a los funcionarios y
  delegaciones de ejemplo (versión 2.1.3).
- La auditoría queda con un solo registro que deja constancia del reinicio.

Es solo para el ambiente de demostración: pide --confirmar.

Uso:  python manage.py reiniciar_demo --confirmar
"""
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from comun.auditoria import registrar
from comun.models import RegistroAuditoria
from cuentas.management.commands.configurar_roles import USUARIOS_DEMO
from delegaciones.models import Delegacion, OrganizacionComunitaria
from gestion.management.commands.cargar_datos_iniciales import (
    FUNCIONARIOS_SEED, _delegaciones_json, delegacion_semilla, funcionario_semilla,
)
from gestion.models import Actividad, CambioCompromiso, Compromiso, Evidencia
from organizacion.models import Ausencia, Funcionario, MetaProyecto, Periodo, Reconocimiento

PERIODO_DEMO = 'Segundo semestre 2026'


class Command(BaseCommand):
    help = 'Borra los datos de prueba y deja solo el equipo de ejemplo (ambiente de demostración).'

    def add_arguments(self, parser):
        parser.add_argument('--confirmar', action='store_true', help='Confirma que se quiere borrar todo.')

    def handle(self, *args, **opciones):
        if not opciones['confirmar']:
            raise CommandError('Esto borra los datos de prueba. Para hacerlo, agregue --confirmar.')

        with transaction.atomic():
            borrados = self._limpiar()
            self._enlazar_cuentas_demo()
        call_command('cargar_datos_iniciales', stdout=self.stdout)
        self._enlazar_cuentas_demo()

        # La auditoría parte de cero, con constancia del reinicio.
        RegistroAuditoria.objects.all().delete()
        registrar('Reinicio de demostración', usuario=None,
                  detalle='Datos de prueba borrados y equipo de ejemplo cargado de nuevo. ' + borrados)

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {Funcionario.objects.count()} funcionarios, {Actividad.objects.count()} actividades, '
            f'{Compromiso.objects.count()} compromisos y {Delegacion.objects.count()} delegaciones.'))

    def _limpiar(self):
        for evidencia in Evidencia.objects.all():
            try:
                evidencia.archivo.delete(save=False)
            except OSError:  # si el archivo ya no está, se sigue igual
                pass
        equipo = [f.pk for f in (funcionario_semilla(item['nombre']) for item in FUNCIONARIOS_SEED) if f]
        conteo = {
            'actividades': Actividad.objects.count(),
            'funcionarios': Funcionario.objects.exclude(pk__in=equipo).count(),
        }
        CambioCompromiso.objects.all().delete()
        Compromiso.objects.all().delete()
        Evidencia.objects.all().delete()
        Actividad.objects.all().delete()
        # v3.0: Tubo de cartas y comunidad (se vuelven a cargar como ejemplo)
        from gestion.models import Carta
        from territorio.models import Hito, MembresiaOrganizacion, SubtipoAtencion, Territorio, TipoAtencion, Vecino
        Carta.objects.all().delete()
        Hito.objects.all().delete()
        MembresiaOrganizacion.objects.all().delete()
        Vecino.objects.all().delete()
        Territorio.objects.all().delete()
        SubtipoAtencion.objects.all().delete()
        TipoAtencion.objects.all().delete()
        MetaProyecto.objects.all().delete()
        Reconocimiento.objects.all().delete()
        Ausencia.objects.all().delete()
        OrganizacionComunitaria.objects.all().delete()

        # Funcionarios que no son del equipo de ejemplo, y las cuentas que
        # quedan sin uso (nunca las 5 de demostración ni los superusuarios).
        # Los del equipo de ejemplo se conservan con el nombre que les haya
        # puesto el equipo; solo se borran los demás.
        Funcionario.objects.exclude(pk__in=equipo).delete()
        demo = [u[0] for u in USUARIOS_DEMO]
        cuentas = (User.objects.filter(is_superuser=False, funcionario__isnull=True)
                   .exclude(username__in=demo))
        conteo['cuentas'] = cuentas.count()
        cuentas.delete()

        oficiales = [d.pk for d in (delegacion_semilla(nombre) for nombre in _delegaciones_json()) if d]
        # Si en las pruebas se movió a alguien del equipo de ejemplo, vuelve a su delegación.
        for item in FUNCIONARIOS_SEED:
            funcionario, delegacion = funcionario_semilla(item['nombre']), delegacion_semilla(item['delegacion'])
            if funcionario and delegacion:
                Funcionario.objects.filter(pk=funcionario.pk).update(
                    delegacion=delegacion, rol=item.get('rol', 'Funcionario'), activo=True)
        Delegacion.objects.exclude(pk__in=oficiales).delete()
        Delegacion.objects.update(activa=True)

        Periodo.objects.exclude(nombre=PERIODO_DEMO).delete()
        Periodo.objects.filter(nombre=PERIODO_DEMO).update(estado=Periodo.Estado.ABIERTO)

        return (f"Se borraron {conteo['actividades']} actividades, {conteo['funcionarios']} funcionarios "
                f"de prueba y {conteo['cuentas']} cuentas sin uso.")

    def _enlazar_cuentas_demo(self):
        """Vuelve a unir delegado.rural y funcionario.rural con su registro de
        funcionario, sin tocar su contraseña."""
        for username, grupo, _nombre, _apellido, email in USUARIOS_DEMO:
            usuario = User.objects.filter(username=username).first()
            datos = next((f for f in FUNCIONARIOS_SEED if f['email'] == email), None)
            funcionario = funcionario_semilla(datos['nombre']) if datos else None
            if usuario is None or funcionario is None:
                continue
            Funcionario.objects.filter(usuario=usuario).exclude(pk=funcionario.pk).update(usuario=None)
            Funcionario.objects.filter(pk=funcionario.pk).update(usuario=usuario, rol=grupo, activo=True)
            usuario.is_active = True
            usuario.save(update_fields=['is_active'])
