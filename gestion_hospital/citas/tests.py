from importlib import import_module

from django.apps import apps
from django.contrib.staticfiles import finders
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.template.loader import get_template
from django.test import SimpleTestCase, TransactionTestCase
from django.urls import reverse

from registros_medicos.forms.registros_forms import RegistroMedicoForm
from .admin import CitaAdmin
from .models import Cita, HorarioMedico


class RecursosIntegradosTests(SimpleTestCase):
    def test_recursos_de_citas_no_ocultan_los_de_registros(self):
        self.assertIn('citas', get_template('citas/layout.html').origin.name)
        self.assertIn('registros_medicos', get_template('layout.html').origin.name)
        self.assertIn('citas', finders.find('citas/style.css'))
        self.assertIn('registros_medicos', finders.find('style.css'))


class IntegracionCitasTests(TransactionTestCase):
    def setUp(self):
        self.datos = {
            'paciente_id': 'paciente-prueba',
            'paciente_documento': '10000001',
            'paciente_nombre': 'Paciente de prueba',
            'paciente_telefono': '3000000000',
            'doctor_id': 'doctor-prueba',
            'doctor_nombre': 'Medico de prueba',
            'doctor_especialidad': 'Medicina general',
            'fecha_inicio': '2026-11-10T09:00',
            'duracion_minutos': '30',
            'motivo_consulta': 'Control',
        }

    def test_ciclo_crud_con_subdocumentos_y_registro_medico(self):
        respuesta = self.client.post(reverse('citas:crear_cita'), self.datos)
        self.assertRedirects(respuesta, reverse('citas:listar_citas'))
        cita = Cita.objects.get()
        self.assertIsInstance(cita.pk, int)
        self.assertEqual(cita.doctor['nombre_completo'], self.datos['doctor_nombre'])
        self.assertEqual(cita.paciente['id_user'], self.datos['paciente_documento'])
        self.assertEqual((cita.fecha_fin - cita.fecha_inicio).total_seconds(), 1800)
        self.assertIn(self.datos['paciente_nombre'], str(cita))
        self.assertEqual(CitaAdmin.paciente_nombre(None, cita), self.datos['paciente_nombre'])
        self.assertEqual(CitaAdmin.doctor_nombre(None, cita), self.datos['doctor_nombre'])

        detalle = reverse('citas:detalle_cita', args=[cita.pk])
        for url in [detalle, reverse('citas:filtrar_citas', args=['PROGRAMADA']),
                    reverse('citas:actualizar_cita', args=[cita.pk]),
                    reverse('citas:eliminar_cita', args=[cita.pk])]:
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 200)
            self.assertContains(respuesta, self.datos['paciente_nombre'])

        formulario_registro = RegistroMedicoForm({'cita_id': str(cita.pk)})
        formulario_registro.is_valid()
        self.assertNotIn('cita_id', formulario_registro.errors)

        respuesta = self.client.post(reverse('citas:actualizar_cita', args=[cita.pk]), {
            'estado': 'CANCELADA', 'motivo_consulta': 'Control actualizado',
            'motivo_cancelacion': 'Solicitud del paciente',
        })
        self.assertRedirects(respuesta, detalle)
        cita.refresh_from_db()
        self.assertEqual(cita.estado, 'CANCELADA')
        self.assertEqual(cita.doctor['id'], self.datos['doctor_id'])

        respuesta = self.client.post(reverse('citas:eliminar_cita', args=[cita.pk]))
        self.assertRedirects(respuesta, reverse('citas:listar_citas'))
        self.assertEqual(Cita.objects.count(), 0)
        formulario_registro = RegistroMedicoForm({'cita_id': str(cita.pk)})
        formulario_registro.is_valid()
        self.assertIn('cita_id', formulario_registro.errors)

    def test_formulario_rechaza_duracion_invalida_y_muestra_error(self):
        self.datos['duracion_minutos'] = '0'
        respuesta = self.client.post(reverse('citas:crear_cita'), self.datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'errorlist')
        self.assertEqual(Cita.objects.count(), 0)

    def test_registro_rechaza_identificador_incompatible(self):
        formulario = RegistroMedicoForm({'cita_id': '65f1a2b3c4d5e6f7a8b9c001'})
        formulario.is_valid()
        self.assertIn('cita_id', formulario.errors)

    def test_migracion_convierte_horarios_antiguos_sin_alter_column(self):
        estado_anterior = MigrationLoader(connection).project_state(('citas', '0001_initial'))
        HorarioAnterior = estado_anterior.apps.get_model('citas', 'HorarioMedico')
        horario = HorarioAnterior.objects.create(
            doctor={'id': 'doctor-prueba', 'nombre_completo': 'Medico', 'especialidad': 'General'},
            dia_semana=1, minuto_inicio=480, minuto_fin=720,
            duracion_consulta_minutos=30, activo='NO',
        )
        migracion = import_module('citas.migrations.0002_alinear_campos_embebidos')
        with connection.schema_editor() as editor:
            migracion.convertir_activo(apps, editor)
        self.assertIs(HorarioMedico.objects.get(pk=horario.pk).activo, False)
