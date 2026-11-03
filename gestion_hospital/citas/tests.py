from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time, timedelta
from importlib import import_module
from threading import Barrier
from unittest.mock import patch

from django.apps import apps
from django.contrib.staticfiles import finders
from django.core.exceptions import ValidationError
from django.core.management import call_command, CommandError
from django.db import close_old_connections, connection
from django.db.migrations.loader import MigrationLoader
from django.template.loader import get_template
from django.test import Client, SimpleTestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from registros_medicos.forms.registros_forms import RegistroMedicoForm
from registros_medicos.models import RegistroMedico
from usuarios.models import User
from . import servicios
from .admin import CitaAdmin
from .models import BloqueoAgenda, Cita, HorarioMedico


class RecursosIntegradosTests(SimpleTestCase):
    def test_recursos_no_ocultan_los_de_registros(self):
        self.assertIn('citas', get_template('citas/layout.html').origin.name)
        self.assertIn('registros_medicos', get_template('layout.html').origin.name)
        self.assertIn('citas', finders.find('citas/style.css'))
        self.assertIn('registros_medicos', finders.find('style.css'))

    def test_admin_no_permite_saltar_reglas(self):
        self.assertFalse(CitaAdmin.has_add_permission(None, None))
        self.assertFalse(CitaAdmin.has_change_permission(None, None))
        self.assertFalse(CitaAdmin.has_delete_permission(None, None))


class AgendaTests(TransactionTestCase):
    def usuario(self, nombre, rol, activo='SI'):
        return User.objects.create(first_name=nombre, last_name='Prueba',
            email=nombre.lower() + '@prueba.test', password='clave-prueba', activo=activo,
            telefono='3000000000', rol={'nombre': rol},
            datos_profesionales={'especialidad': 'Medicina general', 'registro_medico': 'RM-1'} if rol == 'DOCTOR' else None,
            antecedentes_clinicos=None)

    def setUp(self):
        self.admin = self.usuario('Administracion', 'ADMIN')
        self.recepcion = self.usuario('Recepcion', 'RECEPCIONISTA')
        self.doctor = self.usuario('Medico', 'DOCTOR')
        self.doctor2 = self.usuario('OtroMedico', 'DOCTOR')
        self.paciente = self.usuario('Paciente', 'PACIENTE')
        self.paciente2 = self.usuario('OtroPaciente', 'PACIENTE')
        self.fecha = timezone.localtime(timezone.now(), servicios.TZ).date() + timedelta(days=8)
        self.horario = self.crear_horario(self.doctor)
        self.crear_horario(self.doctor2)
        self.datos = {'doctor_id': str(self.doctor.pk), 'paciente_id': str(self.paciente.pk),
            'fecha': self.fecha, 'fecha_inicio': self.fecha.isoformat() + 'T09:00',
            'motivo_consulta': 'Control general'}
        self.entrar(self.admin)

    def entrar(self, usuario, cliente=None):
        cliente = cliente or self.client
        sesion = cliente.session
        sesion['user_id'] = str(usuario.pk)
        sesion['rol'] = usuario.rol['nombre']
        sesion.save()

    def crear_horario(self, doctor, **extra):
        datos = {'doctor_id': str(doctor.pk), 'dia_semana': self.fecha.weekday(),
            'hora_inicio': time(8), 'hora_fin': time(12), 'duracion_consulta_minutos': 30,
            'activo': True, 'version': 1, **extra}
        return servicios.guardar_horario(datos, self.admin)

    def crear_cita(self, **extra):
        return servicios.crear_cita({**self.datos, **extra}, self.admin)

    def datos_post(self, **extra):
        return {**self.datos, 'fecha': self.fecha.isoformat(), **extra}

    def cambiar(self, cita, estado, **extra):
        return servicios.cambiar_estado(cita.pk, {'version': cita.version, 'estado': estado,
            'motivo_consulta': cita.motivo_consulta, **extra}, self.admin)

    def test_ciclo_agendar_reprogramar_cancelar_eliminar_e_historial(self):
        respuesta = self.client.post(reverse('citas:crear_cita'), self.datos_post())
        self.assertEqual(respuesta.status_code, 302)
        cita = Cita.objects.get()
        self.assertEqual(cita.paciente['id'], str(self.paciente.pk))
        self.assertEqual(cita.doctor['nombre_completo'], 'Medico Prueba')
        self.assertEqual(timezone.localtime(cita.fecha_inicio, servicios.TZ).hour, 9)
        self.assertEqual((cita.fecha_fin - cita.fecha_inicio).total_seconds(), 1800)
        for nombre in ('detalle_cita', 'actualizar_cita', 'reprogramar_cita', 'cancelar_cita'):
            self.assertEqual(self.client.get(reverse('citas:' + nombre, args=[cita.pk])).status_code, 200)
        nuevo = self.client.post(reverse('citas:reprogramar_cita', args=[cita.pk]), {
            'version': cita.version, 'fecha': self.fecha.isoformat(),
            'fecha_inicio': self.fecha.isoformat() + 'T10:00', 'motivo': 'Cambio solicitado'})
        self.assertEqual(nuevo.status_code, 302)
        cita.refresh_from_db()
        self.assertEqual(timezone.localtime(cita.fecha_inicio, servicios.TZ).hour, 10)
        self.assertEqual(len(cita.historial), 2)
        self.assertEqual(cita.historial[-1]['accion'], 'Reprogramación')
        self.assertEqual(self.client.post(reverse('citas:cancelar_cita', args=[cita.pk]), {
            'version': cita.version, 'motivo_cancelacion': 'Solicitud del paciente'}).status_code, 302)
        cita.refresh_from_db()
        self.assertEqual(cita.estado, 'CANCELADA')
        self.assertEqual(self.client.get(reverse('citas:eliminar_cita', args=[cita.pk])).status_code, 200)
        respuesta = self.client.post(reverse('citas:eliminar_cita', args=[cita.pk]),
                                     {'version': cita.version, 'confirmar': 'on'})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Cita.objects.count(), 0)

    def test_no_acepta_nombres_ni_snapshots_manipulados(self):
        self.client.post(reverse('citas:crear_cita'), self.datos_post(
            doctor_nombre='Nombre falso', paciente_nombre='Nombre falso', duracion_minutos='999'))
        cita = Cita.objects.get()
        self.assertEqual(cita.doctor['nombre_completo'], 'Medico Prueba')
        self.assertEqual(cita.duracion_minutos, 30)

    def test_impide_cruce_del_medico(self):
        self.crear_cita()
        with self.assertRaises(ValidationError):
            self.crear_cita(paciente_id=str(self.paciente2.pk))
        self.assertEqual(Cita.objects.count(), 1)

    def test_impide_cruce_del_paciente_con_otro_medico(self):
        self.crear_cita()
        with self.assertRaises(ValidationError):
            self.crear_cita(doctor_id=str(self.doctor2.pk))

    def test_turnos_adyacentes_si_se_pueden_agendar(self):
        self.crear_cita()
        self.crear_cita(fecha_inicio=self.fecha.isoformat() + 'T09:30')
        self.assertEqual(Cita.objects.count(), 2)

    def test_impide_cruce_parcial_de_distinta_duracion(self):
        self.crear_horario(self.doctor2, hora_inicio=time(13), hora_fin=time(15), duracion_consulta_minutos=45)
        self.crear_cita(doctor_id=str(self.doctor2.pk), fecha_inicio=self.fecha.isoformat() + 'T13:00')
        self.crear_horario(self.doctor, hora_inicio=time(13), hora_fin=time(15))
        with self.assertRaises(ValidationError):
            self.crear_cita(fecha_inicio=self.fecha.isoformat() + 'T13:30')

    def test_no_admite_horas_fuera_de_grilla_o_sin_horario(self):
        for hora in ('09:10', '12:00', '07:30'):
            with self.assertRaises(ValidationError):
                self.crear_cita(fecha_inicio=self.fecha.isoformat() + 'T' + hora)
        self.assertEqual(Cita.objects.count(), 0)

    def test_cancelar_libera_turno_y_exige_motivo(self):
        cita = self.crear_cita()
        with self.assertRaises(ValidationError):
            self.cambiar(cita, 'CANCELADA')
        cita = self.cambiar(cita, 'CANCELADA', motivo_cancelacion='Ya no requiere consulta')
        nueva = self.crear_cita(paciente_id=str(self.paciente2.pk))
        self.assertNotEqual(nueva.pk, cita.pk)

    def test_reprogramacion_no_se_cruza_y_conserva_cita_al_fallar(self):
        cita = self.crear_cita()
        self.crear_cita(paciente_id=str(self.paciente2.pk), fecha_inicio=self.fecha.isoformat() + 'T10:00')
        with self.assertRaises(ValidationError):
            servicios.reprogramar(cita.pk, {'version': cita.version, 'fecha': self.fecha,
                'fecha_inicio': self.fecha.isoformat() + 'T10:00', 'motivo': 'Cambio'}, self.admin)
        cita.refresh_from_db()
        self.assertEqual(timezone.localtime(cita.fecha_inicio, servicios.TZ).hour, 9)
        self.assertEqual(cita.version, 1)

    def test_reprogramar_no_considera_su_propio_turno_como_cruce(self):
        cita = self.crear_cita()
        servicios.reprogramar(cita.pk, {'version': cita.version, 'fecha': self.fecha,
            'fecha_inicio': self.datos['fecha_inicio'], 'motivo': 'Confirmación'}, self.admin)
        self.assertEqual(Cita.objects.count(), 1)

    def test_paginas_antiguas_no_sobrescriben(self):
        cita = self.crear_cita()
        self.cambiar(cita, 'PROGRAMADA', motivo_consulta='Motivo nuevo')
        with self.assertRaises(ValidationError):
            self.cambiar(cita, 'CANCELADA', motivo_cancelacion='Formulario anterior')
        cita.refresh_from_db()
        self.assertEqual(cita.motivo_consulta, 'Motivo nuevo')
        self.assertEqual(cita.estado, 'PROGRAMADA')

    def test_estados_siguen_flujo_y_cita_completada_es_inmutable(self):
        cita = self.crear_cita()
        with self.assertRaises(ValidationError):
            self.cambiar(cita, 'COMPLETADA')
        with self.assertRaises(ValidationError):
            self.cambiar(cita, 'EN_ESPERA')
        with patch('citas.servicios.timezone.now', return_value=cita.fecha_inicio + timedelta(minutes=10)):
            cita = self.cambiar(cita, 'EN_ESPERA')
            cita = self.cambiar(cita, 'EN_CONSULTA')
            cita = self.cambiar(cita, 'COMPLETADA')
            with self.assertRaises(ValidationError):
                self.cambiar(cita, 'PROGRAMADA')

    def test_inasistencia_solo_despues_del_turno(self):
        cita = self.crear_cita()
        with self.assertRaises(ValidationError):
            self.cambiar(cita, 'NO_ASISTIO')
        with patch('citas.servicios.timezone.now', return_value=cita.fecha_fin + timedelta(minutes=1)):
            cita = self.cambiar(cita, 'NO_ASISTIO')
        self.assertEqual(cita.estado, 'NO_ASISTIO')

    def test_login_obligatorio_rol_y_usuario_activo(self):
        self.assertEqual(Client().get('/citas/').status_code, 302)
        farmacia = self.usuario('Farmacia', 'FARMACEUTICO')
        self.entrar(farmacia)
        self.assertEqual(self.client.get('/citas/').status_code, 403)
        farmacia.activo = 'NO'
        farmacia.save()
        self.assertEqual(self.client.get('/citas/').status_code, 302)

    def test_paciente_y_doctor_solo_ven_sus_citas(self):
        cita = self.crear_cita()
        otra = self.crear_cita(doctor_id=str(self.doctor2.pk), paciente_id=str(self.paciente2.pk))
        for usuario in (self.paciente, self.doctor):
            self.entrar(usuario)
            respuesta = self.client.get('/citas/')
            self.assertContains(respuesta, 'Paciente Prueba')
            self.assertNotContains(respuesta, 'OtroPaciente Prueba')
            self.assertEqual(self.client.get(reverse('citas:detalle_cita', args=[otra.pk])).status_code, 404)
            self.assertEqual(self.client.get(reverse('citas:detalle_cita', args=[cita.pk])).status_code, 200)

    def test_paciente_no_agenda_para_otro_ni_cambia_estados_clinicos(self):
        self.entrar(self.paciente)
        respuesta = self.client.post(reverse('citas:crear_cita'), self.datos_post(paciente_id=str(self.paciente2.pk)))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Cita.objects.count(), 0)
        cita = self.crear_cita()
        self.assertEqual(self.client.post(reverse('citas:actualizar_cita', args=[cita.pk]), {'estado': 'COMPLETADA'}).status_code, 403)
        self.assertEqual(self.client.get('/citas/horarios/').status_code, 403)

    def test_doctor_no_agenda_ni_cancela_ni_edita_horario_ajeno(self):
        cita = self.crear_cita()
        self.entrar(self.doctor)
        self.assertEqual(self.client.get('/citas/agendar/').status_code, 403)
        self.assertEqual(self.client.get(reverse('citas:cancelar_cita', args=[cita.pk])).status_code, 403)
        horario_ajeno = [h for h in HorarioMedico.objects.all() if h.pk != self.horario.pk][0]
        self.assertEqual(self.client.get(reverse('citas:editar_horario', args=[horario_ajeno.pk])).status_code, 404)

    def test_paciente_puede_cancelar_su_cita_y_no_una_iniciada(self):
        cita = self.crear_cita()
        self.entrar(self.paciente)
        with patch('citas.servicios.timezone.now', return_value=cita.fecha_inicio):
            self.assertEqual(self.client.get(reverse('citas:cancelar_cita', args=[cita.pk])).status_code, 403)
        respuesta = self.client.post(reverse('citas:cancelar_cita', args=[cita.pk]),
            {'version': cita.version, 'motivo_cancelacion': 'Imprevisto'})
        self.assertEqual(respuesta.status_code, 302)

    def test_usuario_inactivo_no_se_puede_agendar(self):
        self.doctor.activo = 'NO'
        self.doctor.save()
        with self.assertRaises(ValidationError):
            self.crear_cita()

    def test_fecha_pasada_y_peticiones_invalidas(self):
        respuesta = self.client.post('/citas/agendar/', self.datos_post(fecha='2020-01-01', fecha_inicio='2020-01-01T09:00'))
        self.assertContains(respuesta, 'errorlist')
        self.assertEqual(Cita.objects.count(), 0)
        self.assertEqual(self.client.get('/citas/detalle/999999/').status_code, 404)
        self.assertEqual(self.client.get('/citas/estado/inventado/').status_code, 404)
        self.assertEqual(self.client.put('/citas/agendar/').status_code, 405)
        cliente = Client(enforce_csrf_checks=True)
        self.entrar(self.admin, cliente)
        self.assertEqual(cliente.post('/citas/agendar/', self.datos_post()).status_code, 403)

    def test_filtros_por_fecha_busqueda_y_estado(self):
        cita = self.crear_cita()
        respuesta = self.client.get('/citas/', {'q': 'Medico', 'desde': self.fecha.isoformat(), 'estado': 'PROGRAMADA'})
        self.assertContains(respuesta, 'Paciente Prueba')
        self.assertNotContains(self.client.get('/citas/', {'q': 'inexistente'}), 'Paciente Prueba')
        self.assertContains(self.client.get('/citas/', {'desde': '2026-12-31', 'hasta': '2020-01-01'}), 'errorlist')

    def test_horarios_no_se_solapan_y_adyacentes_si(self):
        with self.assertRaises(ValidationError):
            self.crear_horario(self.doctor, hora_inicio=time(11), hora_fin=time(14))
        self.crear_horario(self.doctor, hora_inicio=time(12), hora_fin=time(14))

    def test_no_desactiva_horario_con_citas_futuras(self):
        self.crear_cita()
        datos = {'doctor_id': str(self.doctor.pk), 'dia_semana': self.fecha.weekday(),
            'hora_inicio': time(8), 'hora_fin': time(12), 'duracion_consulta_minutos': 30,
            'activo': False, 'version': self.horario.version}
        with self.assertRaises(ValidationError):
            servicios.guardar_horario(datos, self.admin, self.horario.pk)

    def test_crud_horarios_por_pantalla(self):
        respuesta = self.client.post('/citas/horarios/crear/', {
            'version': 1, 'doctor_id': self.doctor.pk, 'dia_semana': (self.fecha.weekday() + 1) % 7,
            'hora_inicio': '13:00', 'hora_fin': '16:00', 'duracion_consulta_minutos': 30, 'activo': 'on'})
        self.assertEqual(respuesta.status_code, 302)
        self.assertContains(self.client.get('/citas/horarios/'), '13:00')
        horario = HorarioMedico.objects.get(minuto_inicio=780)
        respuesta = self.client.post(reverse('citas:editar_horario', args=[horario.pk]), {
            'version': horario.version, 'doctor_id': self.doctor.pk, 'dia_semana': horario.dia_semana,
            'hora_inicio': '13:00', 'hora_fin': '16:00', 'duracion_consulta_minutos': 30})
        self.assertEqual(respuesta.status_code, 302)
        horario.refresh_from_db()
        self.assertFalse(horario.activo)

    def test_no_elimina_citas_activas_ni_canceladas_con_registro(self):
        cita = self.crear_cita()
        self.assertEqual(self.client.get(reverse('citas:eliminar_cita', args=[cita.pk])).status_code, 403)
        cita = self.cambiar(cita, 'CANCELADA', motivo_cancelacion='Error de agenda')
        RegistroMedico.objects.create(cita_id=str(cita.pk), fecha=timezone.now(), paciente={}, doctor={},
            queja_principal='Control', examen_fisico='Normal', signos_vitales={}, diagnostico={}, tratamiento='Control')
        with self.assertRaises(ValidationError):
            servicios.borrar_cita(cita.pk, cita.version)
        self.assertTrue(Cita.objects.filter(pk=cita.pk).exists())

    def test_recepcion_no_elimina_y_get_nunca_borra(self):
        cita = self.cambiar(self.crear_cita(), 'CANCELADA', motivo_cancelacion='Error')
        self.client.get(reverse('citas:eliminar_cita', args=[cita.pk]))
        self.assertEqual(Cita.objects.count(), 1)
        self.entrar(self.recepcion)
        self.assertEqual(self.client.post(reverse('citas:eliminar_cita', args=[cita.pk]),
            {'version': cita.version, 'confirmar': 'on'}).status_code, 403)

    def test_registros_medicos_validan_clave_de_cita(self):
        cita = self.crear_cita()
        formulario = RegistroMedicoForm({'cita_id': str(cita.pk)})
        formulario.is_valid()
        self.assertNotIn('cita_id', formulario.errors)
        formulario = RegistroMedicoForm({'cita_id': 'id-inventado'})
        formulario.is_valid()
        self.assertIn('cita_id', formulario.errors)

    def test_normaliza_referencia_numerica_para_no_perder_vinculo(self):
        cita = self.crear_cita()
        formulario = RegistroMedicoForm({'cita_id': '00' + str(cita.pk)})
        formulario.is_valid()
        self.assertEqual(formulario.cleaned_data['cita_id'], str(cita.pk))
        registro = RegistroMedico(cita_id='00' + str(cita.pk), fecha=timezone.now(), paciente={}, doctor={},
            queja_principal='Control', examen_fisico='Normal', signos_vitales={}, diagnostico={}, tratamiento='Control')
        servicios.guardar_registro_medico(registro)
        self.assertEqual(registro.cita_id, str(cita.pk))
        self.assertTrue(servicios.tiene_registro(cita))

    def test_bloqueo_se_libera_incluso_si_la_operacion_falla(self):
        with self.assertRaises(ValidationError):
            self.crear_cita(fecha_inicio='fuera-de-agenda')
        self.assertEqual(BloqueoAgenda.objects.count(), 0)
        with servicios.escritura_agenda():
            with self.assertRaises(ValidationError):
                self.crear_cita()
        self.assertEqual(BloqueoAgenda.objects.count(), 0)

    def test_dos_solicitudes_simultaneas_no_duplican_turno(self):
        barrera = Barrier(2)
        def intentar():
            close_old_connections()
            try:
                barrera.wait(timeout=10)
                self.crear_cita()
                return True
            except ValidationError:
                return False
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as ejecutor:
            resultados = list(ejecutor.map(lambda _: intentar(), range(2)))
        self.assertEqual(sorted(resultados), [False, True])
        self.assertEqual(Cita.objects.count(), 1)
        self.assertEqual(BloqueoAgenda.objects.count(), 0)

    def test_login_redirige_a_citas_y_rechaza_next_externo(self):
        cliente = Client()
        respuesta = cliente.post('/panel/login/?next=https://ejemplo.test/',
            {'email': self.paciente.email, 'password': 'clave-prueba'})
        self.assertEqual(respuesta.url, '/citas/')

    def test_usuarios_tienen_identificadores_estables_y_login_real(self):
        self.assertEqual(len(self.paciente.pk), 24)
        self.assertEqual(User.objects.get(email=self.paciente.email).pk, self.paciente.pk)
        cliente = Client()
        respuesta = cliente.post('/panel/login/', {'email': self.paciente.email, 'password': 'clave-prueba'})
        self.assertEqual(respuesta.url, '/citas/')
        self.assertEqual(cliente.get('/citas/').status_code, 200)

    def test_normalizacion_conserva_usuarios_sin_identificador(self):
        User.objects.filter(email=self.paciente.email).update(id=None)
        normalizar = import_module('citas.migrations.0004_identificadores_usuarios').normalizar_usuarios
        with connection.schema_editor() as editor:
            normalizar(apps, editor)
        paciente = User.objects.get(email=self.paciente.email)
        self.assertIsNotNone(paciente.pk)
        self.assertEqual(len(paciente.pk), 24)
        clave = paciente.pk
        with connection.schema_editor() as editor:
            normalizar(apps, editor)
        self.assertEqual(User.objects.get(email=self.paciente.email).pk, clave)

    def test_no_reprograma_ni_cancela_citas_con_atencion_registrada(self):
        cita = self.crear_cita()
        registro = RegistroMedico(cita_id=str(cita.pk), fecha=timezone.now(), paciente={}, doctor={},
            queja_principal='Control', examen_fisico='Normal', signos_vitales={}, diagnostico={}, tratamiento='Control')
        servicios.guardar_registro_medico(registro)
        with self.assertRaises(ValidationError):
            self.cambiar(cita, 'CANCELADA', motivo_cancelacion='Error')
        with self.assertRaises(ValidationError):
            servicios.reprogramar(cita.pk, {'version': cita.version, 'fecha': self.fecha,
                'fecha_inicio': self.fecha.isoformat() + 'T10:00', 'motivo': 'Cambio'}, self.admin)

    def test_no_guarda_registro_con_cita_cancelada_o_eliminada(self):
        cita = self.cambiar(self.crear_cita(), 'CANCELADA', motivo_cancelacion='Error')
        registro = RegistroMedico(cita_id=str(cita.pk), fecha=timezone.now(), paciente={}, doctor={},
            queja_principal='Control', examen_fisico='Normal', signos_vitales={}, diagnostico={}, tratamiento='Control')
        with self.assertRaises(ValidationError):
            servicios.guardar_registro_medico(registro)
        servicios.borrar_cita(cita.pk, cita.version)
        with self.assertRaises(ValidationError):
            servicios.guardar_registro_medico(registro)
        self.assertEqual(RegistroMedico.objects.count(), 0)

    def test_se_conservan_los_snapshots_al_cambiar_usuarios(self):
        cita = self.crear_cita()
        self.paciente.first_name = 'NombreActualizado'
        self.paciente.save()
        cita.refresh_from_db()
        self.assertEqual(cita.paciente['nombre_completo'], 'Paciente Prueba')

    def test_fecha_extrema_no_produce_error_500(self):
        respuesta = self.client.post('/citas/agendar/', self.datos_post(fecha='9999-12-31'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Cita.objects.count(), 0)

    def test_recuperacion_de_bloqueo_exige_token_correcto(self):
        bloqueo = BloqueoAgenda.objects.create(clave='agenda', token='token-prueba')
        with self.assertRaises(CommandError):
            call_command('liberar_agenda', token='token-prueba')
        with self.assertRaises(CommandError):
            call_command('liberar_agenda', token='otro', servidor_detenido=True)
        self.assertEqual(BloqueoAgenda.objects.count(), 1)
        call_command('liberar_agenda', token=bloqueo.token, servidor_detenido=True, verbosity=0)
        self.assertEqual(BloqueoAgenda.objects.count(), 0)

    def test_migracion_convierte_horarios_antiguos(self):
        estado = MigrationLoader(connection).project_state(('citas', '0001_initial'))
        Anterior = estado.apps.get_model('citas', 'HorarioMedico')
        horario = Anterior.objects.create(doctor=servicios.snapshot_doctor(self.doctor),
            dia_semana=1, minuto_inicio=480, minuto_fin=720, duracion_consulta_minutos=30, activo='NO')
        migracion = import_module('citas.migrations.0002_alinear_campos_embebidos')
        with connection.schema_editor() as editor:
            migracion.convertir_activo(apps, editor)
        self.assertIs(HorarioMedico.objects.get(pk=horario.pk).activo, False)
