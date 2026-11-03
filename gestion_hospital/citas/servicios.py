"""Reglas de agenda. Toda la persistencia se realiza mediante el ORM de Django."""
from contextlib import contextmanager
from datetime import datetime, time, timedelta
from uuid import uuid4

import pytz
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.utils import timezone

from usuarios.models import User
from .acceso import ZONA
from .models import BloqueoAgenda, Cita, HorarioMedico

TZ = pytz.timezone(ZONA)
FINALES = ('CANCELADA', 'COMPLETADA', 'NO_ASISTIO')
TRANSICIONES = {
    'PROGRAMADA': ('PROGRAMADA', 'EN_ESPERA', 'CANCELADA', 'NO_ASISTIO'),
    'EN_ESPERA': ('EN_ESPERA', 'EN_CONSULTA', 'CANCELADA'),
    'EN_CONSULTA': ('EN_CONSULTA', 'COMPLETADA'),
}


@contextmanager
def escritura_agenda():
    # La restricción UNIQUE se crea con migrate. No usar transaction.atomic:
    # este backend no ofrece transacciones MongoDB para múltiples documentos.
    token = uuid4().hex
    try:
        BloqueoAgenda.objects.create(clave='agenda', token=token)
    except DatabaseError as error:
        causa = error
        while causa is not None:
            if causa.__class__.__name__ == 'DuplicateKeyError' or 'E11000' in str(causa):
                raise ValidationError('La agenda está procesando otra operación. Intenta nuevamente en unos segundos.') from error
            causa = causa.__cause__ or causa.__context__
        raise
    try:
        yield
    finally:
        BloqueoAgenda.objects.filter(clave='agenda', token=token).delete()


def usuarios_activos(rol):
    # Los filtros de subdocumentos varían entre versiones de Djongo.
    return [u for u in User.objects.filter(activo='SI').order_by('first_name', 'last_name')
            if (u.rol or {}).get('nombre') == rol]


def usuario_activo(clave, rol):
    for usuario in usuarios_activos(rol):
        if str(usuario.pk) == str(clave):
            return usuario
    raise ValidationError('El paciente o médico seleccionado no está activo o ya no tiene ese rol.')


def snapshot_doctor(usuario):
    especialidad = (usuario.datos_profesionales or {}).get('especialidad', '').strip()
    if not especialidad:
        raise ValidationError('El médico debe tener una especialidad registrada en Usuarios.')
    return {'id': str(usuario.pk), 'nombre_completo': f'{usuario.first_name} {usuario.last_name}',
            'especialidad': especialidad}


def snapshot_paciente(usuario):
    # El modelo User del equipo no tiene documento de identidad. id_user
    # conserva la referencia al ID de usuario, sin inventar una cédula.
    return {'id': str(usuario.pk), 'id_user': str(usuario.pk),
            'nombre_completo': f'{usuario.first_name} {usuario.last_name}',
            'telefono': usuario.telefono or ''}


def ocupadas(inicio, fin, excluir=None):
    return [c for c in Cita.objects.filter(fecha_inicio__lt=fin, fecha_fin__gt=inicio)
            if c.pk != excluir and c.estado not in ('CANCELADA', 'NO_ASISTIO')]


def hay_cruce(citas, doctor_id, paciente_id=None):
    for cita in citas:
        if str(cita.doctor['id']) == str(doctor_id):
            return True
        if paciente_id is not None and str(cita.paciente['id']) == str(paciente_id):
            return True
    return False


def turnos_disponibles(doctor_id, fecha, paciente_id=None, excluir=None):
    hoy = timezone.localtime(timezone.now(), TZ).date()
    if fecha < hoy or (fecha - hoy).days > 365:
        return []
    inicio_dia = TZ.localize(datetime.combine(fecha, time.min))
    fin_dia = inicio_dia + timedelta(days=1)
    citas = ocupadas(inicio_dia, fin_dia, excluir)
    ahora = timezone.now()
    turnos = []
    for horario in HorarioMedico.objects.filter(dia_semana=fecha.weekday()).order_by('minuto_inicio'):
        if not horario.activo or str(horario.doctor['id']) != str(doctor_id):
            continue
        duracion = horario.duracion_consulta_minutos
        if duracion < 5 or horario.zona_horaria != ZONA:
            continue
        for minuto in range(horario.minuto_inicio, horario.minuto_fin - duracion + 1, duracion):
            inicio = inicio_dia + timedelta(minutes=minuto)
            fin = inicio + timedelta(minutes=duracion)
            cruces = [c for c in citas if c.fecha_inicio < fin and c.fecha_fin > inicio]
            if inicio <= ahora or hay_cruce(cruces, doctor_id, paciente_id):
                continue
            turnos.append({'valor': inicio.strftime('%Y-%m-%dT%H:%M'),
                           'etiqueta': f'{inicio:%H:%M} – {fin:%H:%M} ({duracion} min)',
                           'inicio': inicio, 'fin': fin, 'horario': horario})
    return sorted(turnos, key=lambda t: t['inicio'])


def turno_valido(doctor_id, paciente_id, fecha, valor, excluir=None):
    usuario_activo(doctor_id, 'DOCTOR')
    usuario_activo(paciente_id, 'PACIENTE')
    for turno in turnos_disponibles(doctor_id, fecha, paciente_id, excluir):
        if turno['valor'] == valor:
            return turno
    raise ValidationError('Ese turno ya no está disponible. Revisa el horario del médico y los cruces del paciente.')


def evento(cita, usuario, accion, **extra):
    cita.historial = list(cita.historial or []) + [{
        'accion': accion, 'fecha': timezone.now().isoformat(),
        'fecha_local': timezone.localtime(timezone.now(), TZ).strftime('%d/%m/%Y %H:%M'),
        'usuario': f'{usuario.first_name} {usuario.last_name}',
        'usuario_id': str(usuario.pk), 'estado': cita.estado, **extra,
    }]


def comprobar_version(objeto, version):
    if objeto.version != version:
        raise ValidationError('Otro usuario modificó este registro. Recarga la página antes de guardar.')


def recargar_cita(cita_id):
    try:
        return Cita.objects.get(pk=cita_id)
    except Cita.DoesNotExist:
        raise ValidationError('La cita ya no existe. Recarga la agenda.')


def tiene_registro(cita):
    from registros_medicos.models import RegistroMedico
    return RegistroMedico.objects.filter(cita_id=str(cita.pk)).exists()


def guardar_registro_medico(registro):
    """Evita crear una referencia a una cita eliminada o cancelada mientras se enviaba el formulario."""
    if not registro.cita_id:
        registro.save()
        return
    with escritura_agenda():
        cita = recargar_cita(Cita._meta.pk.to_python(registro.cita_id))
        if cita.estado in ('CANCELADA', 'NO_ASISTIO'):
            raise ValidationError('No se puede asociar un registro a una cita cancelada o sin asistencia.')
        registro.cita_id = str(cita.pk)
        registro.save()


def crear_cita(datos, usuario):
    with escritura_agenda():
        paciente = usuario_activo(datos['paciente_id'], 'PACIENTE')
        doctor = usuario_activo(datos['doctor_id'], 'DOCTOR')
        turno = turno_valido(doctor.pk, paciente.pk, datos['fecha'], datos['fecha_inicio'])
        cita = Cita(paciente=snapshot_paciente(paciente), doctor=snapshot_doctor(doctor),
                    horario_id=str(turno['horario'].pk), fecha_inicio=turno['inicio'],
                    fecha_fin=turno['fin'], duracion_minutos=turno['horario'].duracion_consulta_minutos,
                    motivo_consulta=datos['motivo_consulta'])
        evento(cita, usuario, 'Agendamiento')
        cita.full_clean()
        cita.save()
        return cita


def reprogramar(cita_id, datos, usuario):
    with escritura_agenda():
        cita = recargar_cita(cita_id)
        comprobar_version(cita, datos['version'])
        if tiene_registro(cita):
            raise ValidationError('La cita tiene un registro médico y no puede reprogramarse.')
        if cita.estado != 'PROGRAMADA' or cita.fecha_inicio <= timezone.now():
            raise ValidationError('Solo se pueden reprogramar citas programadas que aún no han iniciado.')
        turno = turno_valido(cita.doctor['id'], cita.paciente['id'], datos['fecha'], datos['fecha_inicio'], cita.pk)
        anterior = cita.fecha_inicio.isoformat()
        cita.fecha_inicio, cita.fecha_fin = turno['inicio'], turno['fin']
        cita.horario_id = str(turno['horario'].pk)
        cita.duracion_minutos = turno['horario'].duracion_consulta_minutos
        cita.version += 1
        evento(cita, usuario, 'Reprogramación', fecha_anterior=anterior,
               fecha_nueva=cita.fecha_inicio.isoformat(), motivo=datos['motivo'],
               turno_anterior=timezone.localtime(datetime.fromisoformat(anterior), TZ).strftime('%d/%m/%Y %H:%M'),
               turno_nuevo=timezone.localtime(cita.fecha_inicio, TZ).strftime('%d/%m/%Y %H:%M'))
        cita.full_clean()
        cita.save()
        return cita


def cambiar_estado(cita_id, datos, usuario, es_paciente=False):
    with escritura_agenda():
        cita = recargar_cita(cita_id)
        comprobar_version(cita, datos['version'])
        estado = datos['estado']
        if estado in ('CANCELADA', 'NO_ASISTIO') and tiene_registro(cita):
            raise ValidationError('La cita tiene un registro médico y debe conservar su atención.')
        if es_paciente and (estado != 'CANCELADA' or cita.fecha_inicio <= timezone.now()):
            raise ValidationError('Solo puedes cancelar una cita que todavía no ha iniciado.')
        if estado not in TRANSICIONES.get(cita.estado, ()):
            raise ValidationError('El cambio de estado no está permitido. Las citas finalizadas conservan su historial.')
        if estado == 'CANCELADA' and not datos.get('motivo_cancelacion', '').strip():
            raise ValidationError('Debes indicar el motivo de cancelación.')
        ahora = timezone.now()
        if estado in ('EN_ESPERA', 'EN_CONSULTA') and estado != cita.estado:
            if timezone.localtime(ahora, TZ).date() != timezone.localtime(cita.fecha_inicio, TZ).date() or cita.fecha_inicio > ahora + timedelta(minutes=30):
                raise ValidationError('La atención puede comenzar el día de la cita, desde 30 minutos antes del turno.')
        if estado == 'NO_ASISTIO' and ahora < cita.fecha_fin:
            raise ValidationError('Solo se puede marcar inasistencia cuando haya terminado el turno.')
        if estado == 'COMPLETADA' and ahora < cita.fecha_inicio:
            raise ValidationError('No se puede completar una cita antes de su hora de inicio.')
        anterior = cita.estado
        cita.estado = estado
        cita.motivo_consulta = datos.get('motivo_consulta', cita.motivo_consulta)
        cita.motivo_cancelacion = datos.get('motivo_cancelacion', '') if estado == 'CANCELADA' else ''
        cita.version += 1
        evento(cita, usuario, 'Cancelación' if estado == 'CANCELADA' else 'Actualización',
               estado_anterior=anterior, motivo=cita.motivo_cancelacion)
        cita.full_clean()
        cita.save()
        return cita


def borrar_cita(cita_id, version):
    with escritura_agenda():
        cita = recargar_cita(cita_id)
        comprobar_version(cita, version)
        if cita.estado != 'CANCELADA':
            raise ValidationError('Solo se eliminan citas canceladas. Cancela primero para conservar el motivo.')
        if tiene_registro(cita):
            raise ValidationError('Esta cita tiene un registro médico y debe conservarse.')
        cita.delete()


def guardar_horario(datos, usuario, horario_id=None):
    with escritura_agenda():
        doctor = usuario_activo(datos['doctor_id'], 'DOCTOR')
        horario = HorarioMedico.objects.get(pk=horario_id) if horario_id else HorarioMedico()
        if horario_id:
            comprobar_version(horario, datos['version'])
        inicio = datos['hora_inicio'].hour * 60 + datos['hora_inicio'].minute
        fin = datos['hora_fin'].hour * 60 + datos['hora_fin'].minute
        if fin <= inicio:
            raise ValidationError('La hora final debe ser posterior a la inicial; divide los turnos nocturnos por día.')
        duracion = datos['duracion_consulta_minutos']
        if duracion < 5 or duracion > 240:
            raise ValidationError('La consulta debe durar entre 5 y 240 minutos.')
        if (fin - inicio) < duracion:
            raise ValidationError('El horario debe contener al menos una consulta completa.')
        if datos['activo']:
            for otro in HorarioMedico.objects.filter(dia_semana=datos['dia_semana']):
                if otro.pk != horario_id and otro.activo and str(otro.doctor['id']) == str(doctor.pk) and otro.minuto_inicio < fin and otro.minuto_fin > inicio:
                    raise ValidationError('Este horario se cruza con otro horario activo del médico.')
        if horario_id:
            for cita in Cita.objects.filter(horario_id=str(horario_id), fecha_inicio__gt=timezone.now()):
                if cita.estado in FINALES:
                    continue
                local = timezone.localtime(cita.fecha_inicio, TZ)
                minuto = local.hour * 60 + local.minute
                if (not datos['activo'] or str(cita.doctor['id']) != str(doctor.pk) or
                        local.weekday() != datos['dia_semana'] or minuto < inicio or
                        minuto + cita.duracion_minutos > fin or
                        cita.duracion_minutos != duracion or (minuto - inicio) % duracion):
                    raise ValidationError('Hay citas futuras en este horario. Reprográmalas o cancélalas antes de modificarlo.')
            horario.version += 1
        horario.doctor = snapshot_doctor(doctor)
        horario.dia_semana = datos['dia_semana']
        horario.minuto_inicio, horario.minuto_fin = inicio, fin
        horario.duracion_consulta_minutos = duracion
        horario.zona_horaria = ZONA
        horario.activo = datos['activo']
        horario.full_clean()
        horario.save()
        return horario
