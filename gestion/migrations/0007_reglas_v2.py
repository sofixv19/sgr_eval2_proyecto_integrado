"""
Versión 2.0 — Nuevos requerimientos (octubre 2026).

Agrega a Actividad los campos de las nuevas reglas de puntaje. Las
actividades que ya existían quedan marcadas con version_reglas = "1.0":
las reglas 2.0 no se aplican hacia atrás, así su puntaje no cambia.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("delegaciones", "0003_organizaciones_comunitarias"),
        ("gestion", "0006_estado_validacion_inicial"),
    ]

    operations = [
        migrations.AddField(
            model_name="actividad",
            name="motivo_sin_puntaje",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=200,
                verbose_name="Motivo por el que no suma",
            ),
        ),
        migrations.AddField(
            model_name="actividad",
            name="organizacion",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="actividades",
                to="delegaciones.organizacioncomunitaria",
                verbose_name="Organización solicitante",
            ),
        ),
        migrations.AddField(
            model_name="actividad",
            name="puntuable",
            field=models.BooleanField(
                default=True,
                editable=False,
                help_text="Se calcula al guardar según las reglas de la versión 2.0.",
                verbose_name="Suma puntaje",
            ),
        ),
        migrations.AddField(
            model_name="actividad",
            name="tipo_gestion",
            field=models.CharField(
                choices=[
                    (
                        "Realizacion",
                        "Realización de la acción (taller, visita, atención, operativo…)",
                    ),
                    (
                        "Previa",
                        "Gestión previa (coordinación, correo, invitación, coordinación interna)",
                    ),
                ],
                default="Realizacion",
                help_text="Solo la realización de la acción da punto; las gestiones previas no.",
                max_length=20,
                verbose_name="Tipo de gestión",
            ),
        ),
        migrations.AddField(
            model_name="actividad",
            name="tipo_solicitante",
            field=models.CharField(
                choices=[
                    ("Vecino", "Vecino/a (usuario)"),
                    ("Organizacion", "Organización comunitaria"),
                    ("Delegado", "El propio Delegado (gestión interna)"),
                ],
                default="Vecino",
                help_text="Si el solicitante es el propio Delegado, la actividad no se contabiliza (otra gestión).",
                max_length=20,
                verbose_name="Quién solicita",
            ),
        ),
        # Primero con "1.0" para las actividades existentes...
        migrations.AddField(
            model_name="actividad",
            name="version_reglas",
            field=models.CharField(default="1.0", editable=False, max_length=5,
                                   verbose_name="Versión de reglas"),
        ),
        # ...y luego "2.0" como valor por defecto para las nuevas.
        migrations.AlterField(
            model_name="actividad",
            name="version_reglas",
            field=models.CharField(
                default="2.0",
                editable=False,
                help_text="Versión de los requerimientos vigente al registrar la actividad. Las reglas de puntaje de la 2.0 no se aplican hacia atrás a las actividades 1.x.",
                max_length=5,
                verbose_name="Versión de reglas",
            ),
        ),
    ]
