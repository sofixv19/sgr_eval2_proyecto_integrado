"""
Crea los grupos de usuarios del SGR con sus permisos (principio de mínimo
privilegio) y, opcionalmente, usuarios de prueba para la demostración.

Uso:
    python manage.py configurar_roles
    python manage.py configurar_roles --usuarios-demo --clave "UnaClaveSegura2026"
    python manage.py configurar_roles --cuentas-funcionarios --clave "UnaClaveSegura2026"

Es idempotente: se puede ejecutar varias veces.
"""
from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from cuentas.perfiles import sincronizar_cuenta
from organizacion.models import Funcionario

TABLAS_MAESTRAS = [
    ('delegaciones', 'delegacion'),
    ('gestion', 'categoria'),
    ('organizacion', 'cargofuncion'),
    ('organizacion', 'funcionario'),
    ('organizacion', 'metaproyecto'),
    ('organizacion', 'periodo'),
    ('delegaciones', 'organizacioncomunitaria'),   # v2.0
]
TRANSACCIONALES = [
    ('gestion', 'actividad'), ('gestion', 'evidencia'),
    ('organizacion', 'reconocimiento'), ('organizacion', 'ausencia'),   # v2.0
    ('gestion', 'compromiso'), ('gestion', 'cambiocompromiso'),        # v2.1 agenda colectiva
    ('comun', 'registroauditoria'),                                    # v2.1 auditoría
]
TODAS = TABLAS_MAESTRAS + TRANSACCIONALES

# Acciones permitidas por grupo y tabla (view/add/change/delete, más el
# permiso propio 'validar' de Actividad). Reparto de funciones según la
# retroalimentación del profesor Caiceo (revisión de la Evaluación 2):
# - Coordinador: gestiona delegaciones (crear, activar/desactivar) y crea
#   y asigna a los Delegados; ve el cumplimiento de todas.
# - Delegado: gestiona a los funcionarios de su delegación, les asigna
#   metas y valida la evidencia de sus actividades. No modifica actividades.
# - Funcionario: registra sus actividades y sube su evidencia.
# El ámbito (qué delegación ve cada uno) se controla en cuentas/perfiles.py.
GRUPOS = {
    'Administrador': {
        **{t: ['view', 'add', 'change', 'delete'] for t in TODAS},
        ('gestion', 'actividad'): ['view', 'add', 'change', 'delete', 'validar'],
        # La auditoría es de solo lectura incluso para el Administrador (HU-30).
        ('comun', 'registroauditoria'): ['view'],
        ('gestion', 'cambiocompromiso'): ['view'],
    },
    'Coordinador': {
        ('delegaciones', 'delegacion'): ['view', 'add', 'change'],
        ('organizacion', 'funcionario'): ['view', 'add', 'change'],
        ('organizacion', 'cargofuncion'): ['view'],
        ('organizacion', 'metaproyecto'): ['view'],
        ('organizacion', 'periodo'): ['view', 'add', 'change'],
        ('gestion', 'categoria'): ['view'],
        ('gestion', 'actividad'): ['view'],
        ('gestion', 'evidencia'): ['view'],
        ('delegaciones', 'organizacioncomunitaria'): ['view', 'add', 'change'],
        ('organizacion', 'reconocimiento'): ['view'],
        ('organizacion', 'ausencia'): ['view'],
        ('gestion', 'compromiso'): ['view'],
        ('gestion', 'cambiocompromiso'): ['view'],
        ('comun', 'registroauditoria'): ['view'],
    },
    'Delegado': {
        ('delegaciones', 'delegacion'): ['view'],
        ('organizacion', 'funcionario'): ['view', 'add', 'change'],
        ('organizacion', 'cargofuncion'): ['view', 'add', 'change'],
        ('organizacion', 'metaproyecto'): ['view', 'add', 'change', 'delete'],
        ('organizacion', 'periodo'): ['view'],
        ('gestion', 'categoria'): ['view'],
        ('gestion', 'actividad'): ['view', 'validar'],
        ('gestion', 'evidencia'): ['view'],
        # v2.0: organizaciones de su territorio, felicitaciones/reclamos y ausencias de su equipo
        ('delegaciones', 'organizacioncomunitaria'): ['view', 'add', 'change'],
        ('organizacion', 'reconocimiento'): ['view', 'add', 'change', 'delete'],
        ('organizacion', 'ausencia'): ['view', 'add', 'change', 'delete'],
        # v2.1: agenda colectiva de su delegación (crear, actualizar, reasignar, eliminar)
        ('gestion', 'compromiso'): ['view', 'add', 'change', 'delete'],
        ('gestion', 'cambiocompromiso'): ['view'],
    },
    'Funcionario': {
        ('gestion', 'categoria'): ['view'],
        ('gestion', 'actividad'): ['view', 'add', 'change', 'delete'],
        ('gestion', 'evidencia'): ['view', 'add'],
        ('delegaciones', 'organizacioncomunitaria'): ['view'],
        ('organizacion', 'reconocimiento'): ['view'],
        ('organizacion', 'ausencia'): ['view'],
        ('gestion', 'compromiso'): ['view', 'add', 'change'],
        ('gestion', 'cambiocompromiso'): ['view'],
    },
    'Verificador': {t: ['view'] for t in TODAS},
}

# Usuarios de prueba. Los de Delegado y Funcionario se enlazan a un registro
# de la tabla de funcionarios, que es lo que define su delegación.
USUARIOS_DEMO = [
    ('admin.sgr', 'Administrador', 'Administrador', 'SGR', None),
    ('coordinador.sgr', 'Coordinador', 'Coordinador', 'SGR', None),
    ('delegado.rural', 'Delegado', 'Delegado', 'Rural', 'c.araya.delegado@laserena.cl'),
    ('funcionario.rural', 'Funcionario', 'Funcionario', 'Rural', 'f.contreras.ejemplo@laserena.cl'),
    ('verificador.sgr', 'Verificador', 'Verificador', 'SGR', None),
]


class Command(BaseCommand):
    help = 'Crea los grupos de roles del SGR con sus permisos y, si se pide, usuarios de prueba.'

    def add_arguments(self, parser):
        parser.add_argument('--usuarios-demo', action='store_true', help='Crea un usuario de prueba por rol.')
        parser.add_argument('--clave', default='', help='Contraseña para los usuarios de prueba.')
        parser.add_argument('--cuentas-funcionarios', action='store_true',
                            help='Crea una cuenta de acceso para cada funcionario que aún no tenga (con la clave indicada).')

    def handle(self, *args, **opciones):
        hablar = opciones.get('verbosity', 1) > 0
        for nombre, tablas in GRUPOS.items():
            grupo, _ = Group.objects.get_or_create(name=nombre)
            permisos = []
            for (app, modelo), acciones in tablas.items():
                for accion in acciones:
                    codigo = 'validar_actividad' if accion == 'validar' else f'{accion}_{modelo}'
                    permisos.append(Permission.objects.get(content_type__app_label=app, codename=codigo))
            grupo.permissions.set(permisos)
            if hablar:
                self.stdout.write(f'  Grupo {nombre}: {len(permisos)} permisos')

        if opciones['usuarios_demo'] or opciones['cuentas_funcionarios']:
            clave = opciones['clave']
            try:
                validate_password(clave)
            except ValidationError as error:
                raise CommandError('Contraseña no válida: ' + ' '.join(error.messages))

        if opciones['usuarios_demo']:
            for username, grupo, nombre, apellido, email in USUARIOS_DEMO:
                usuario, creado = User.objects.get_or_create(username=username, defaults={
                    'first_name': nombre, 'last_name': apellido, 'is_active': True,
                })
                usuario.set_password(clave)
                usuario.save()
                usuario.groups.set([Group.objects.get(name=grupo)])
                enlace = ''
                if email:
                    funcionario = Funcionario.objects.filter(email=email).first()
                    if funcionario:
                        Funcionario.objects.filter(usuario=usuario).exclude(pk=funcionario.pk).update(usuario=None)
                        funcionario.usuario = usuario
                        funcionario.rol = grupo
                        funcionario.save(update_fields=['usuario', 'rol'])
                        enlace = f' -> {funcionario.nombre} ({funcionario.delegacion})'
                if hablar:
                    self.stdout.write(f'  Usuario {username} ({grupo}) {"creado" if creado else "actualizado"}{enlace}')

        if opciones['cuentas_funcionarios']:
            for funcionario in Funcionario.objects.filter(usuario__isnull=True).select_related('delegacion'):
                usuario, _ = sincronizar_cuenta(funcionario, clave=clave)
                if hablar:
                    self.stdout.write(f'  Cuenta {usuario.username} ({funcionario.rol}, {funcionario.delegacion})')

        if hablar:
            self.stdout.write(self.style.SUCCESS('Roles configurados correctamente.'))
