# Alineación del estado de Django con los documentos de MongoDB.

import citas.models
from django.db import migrations, models
import djongo.models.fields


def convertir_activo(apps, schema_editor):
    Horario = apps.get_model('citas', 'HorarioMedico')
    horarios = Horario.objects.using(schema_editor.connection.alias)
    for horario in horarios.values('id', 'activo'):
        if horario['activo'] in ('SI', 'NO'):
            horarios.filter(pk=horario['id']).update(activo=horario['activo'] == 'SI')


class Migration(migrations.Migration):

    dependencies = [
        ('citas', '0001_initial'),
    ]

    # MongoDB no necesita ALTER COLUMN TYPE, que Djongo no implementa.
    # Los cambios de validación y defaults se aplican en el ORM.
    operations = [migrations.SeparateDatabaseAndState(state_operations=[
        migrations.AlterField(
            model_name='cita',
            name='doctor',
            field=djongo.models.fields.EmbeddedField(model_container=citas.models.DoctorSnapshot),
        ),
        migrations.AlterField(
            model_name='cita',
            name='duracion_minutos',
            field=models.IntegerField(default=30),
        ),
        migrations.AlterField(
            model_name='cita',
            name='paciente',
            field=djongo.models.fields.EmbeddedField(model_container=citas.models.PacienteSnapshot),
        ),
        migrations.AlterField(
            model_name='horariomedico',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='horariomedico',
            name='doctor',
            field=djongo.models.fields.EmbeddedField(model_container=citas.models.DoctorSnapshot),
        ),
        migrations.AlterField(
            model_name='horariomedico',
            name='duracion_consulta_minutos',
            field=models.IntegerField(default=30),
        ),
        migrations.AlterField(
            model_name='horariomedico',
            name='zona_horaria',
            field=models.CharField(default='America/Bogota', max_length=50),
        ),
    ]), migrations.RunPython(convertir_activo)]
