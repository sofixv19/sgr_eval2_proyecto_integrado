"""
Crea los grupos de usuarios del SGR con sus permisos (principio de mínimo
privilegio) y, opcionalmente, usuarios de prueba para la demostración.

Uso:
    python manage.py configurar_roles
    python manage.py configurar_roles --usuarios-demo --clave "UnaClaveSegura2026"

Es idempotente: se puede ejecutar varias veces.
"""
from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

TABLAS_MAESTRAS = [
    ('delegaciones', 'delegacion'),
    ('gestion', 'categoria'),
    ('organizacion', 'cargofuncion'),
    ('organizacion', 'funcionario'),
    ('organizacion', 'metaproyecto'),
    ('organizacion', 'periodo'),
]
TRANSACCIONALES = [('gestion', 'actividad')]

# Acciones permitidas por grupo y tabla (view/add/change/delete).
GRUPOS = {
    'Administrador': {
        **{t: ['view', 'add', 'change', 'delete'] for t in TABLAS_MAESTRAS},
        **{t: ['view', 'add', 'change', 'delete'] for t in TRANSACCIONALES},
    },
    'Coordinador': {
        **{t: ['view'] for t in TABLAS_MAESTRAS},
        ('organizacion', 'cargofuncion'): ['view', 'add', 'change'],
        ('organizacion', 'metaproyecto'): ['view', 'add', 'change', 'delete'],
        ('organizacion', 'periodo'): ['view', 'add', 'change'],
        ('gestion', 'actividad'): ['view'],
    },
    'Delegado': {
        **{t: ['view'] for t in TABLAS_MAESTRAS},
        ('gestion', 'actividad'): ['view', 'change'],
    },
    'Funcionario': {
        **{t: ['view'] for t in TABLAS_MAESTRAS},
        ('gestion', 'actividad'): ['view', 'add', 'change'],
    },
    'Verificador': {
        **{t: ['view'] for t in TABLAS_MAESTRAS},
        ('gestion', 'actividad'): ['view'],
    },
}

USUARIOS_DEMO = [
    ('admin.sgr', 'Administrador', 'Administrador', 'SGR'),
    ('coordinador.sgr', 'Coordinador', 'Coordinador', 'SGR'),
    ('delegado.rural', 'Delegado', 'Delegado', 'Rural'),
    ('funcionario.rural', 'Funcionario', 'Funcionario', 'Rural'),
    ('verificador.sgr', 'Verificador', 'Verificador', 'SGR'),
]


class Command(BaseCommand):
    help = 'Crea los grupos de roles del SGR con sus permisos y, si se pide, usuarios de prueba.'

    def add_arguments(self, parser):
        parser.add_argument('--usuarios-demo', action='store_true', help='Crea un usuario de prueba por rol.')
        parser.add_argument('--clave', default='', help='Contraseña para los usuarios de prueba.')

    def handle(self, *args, **opciones):
        hablar = opciones.get('verbosity', 1) > 0
        for nombre, tablas in GRUPOS.items():
            grupo, _ = Group.objects.get_or_create(name=nombre)
            permisos = []
            for (app, modelo), acciones in tablas.items():
                for accion in acciones:
                    permisos.append(Permission.objects.get(
                        content_type__app_label=app, codename=f'{accion}_{modelo}',
                    ))
            grupo.permissions.set(permisos)
            if hablar:
                self.stdout.write(f'  Grupo {nombre}: {len(permisos)} permisos')

        if opciones['usuarios_demo']:
            clave = opciones['clave']
            try:
                validate_password(clave)
            except ValidationError as error:
                raise CommandError('Contraseña no válida: ' + ' '.join(error.messages))
            for username, grupo, nombre, apellido in USUARIOS_DEMO:
                usuario, creado = User.objects.get_or_create(username=username, defaults={
                    'first_name': nombre, 'last_name': apellido, 'is_active': True,
                })
                usuario.set_password(clave)
                usuario.save()
                usuario.groups.set([Group.objects.get(name=grupo)])
                if hablar:
                    self.stdout.write(f'  Usuario {username} ({grupo}) {"creado" if creado else "actualizado"}')

        if hablar:
            self.stdout.write(self.style.SUCCESS('Roles configurados correctamente.'))
