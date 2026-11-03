from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Cita, HorarioMedico
from .servicios import TRANSICIONES, TZ, turnos_disponibles, usuarios_activos


def opciones_usuarios(rol, usuario=None):
    usuarios = usuarios_activos(rol)
    if rol == 'PACIENTE' and usuario and (usuario.rol or {}).get('nombre') == 'PACIENTE':
        usuarios = [u for u in usuarios if u.pk == usuario.pk]
    return [('', 'Selecciona una opción')] + [
        (str(u.pk), f"{u.first_name} {u.last_name} · " +
         ((u.datos_profesionales or {}).get('especialidad', 'Sin especialidad') if rol == 'DOCTOR' else u.email))
        for u in usuarios]


class FechaAgendaMixin:
    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        hoy = timezone.localtime(timezone.now(), TZ).date()
        if fecha < hoy or fecha > hoy + timedelta(days=365):
            raise ValidationError('Elige una fecha entre hoy y los próximos 365 días.')
        return fecha


class FormularioDisponibilidad(FechaAgendaMixin, forms.Form):
    doctor_id = forms.ChoiceField(label='Médico')
    fecha = forms.DateField(label='Fecha de la consulta', widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doctor_id'].choices = opciones_usuarios('DOCTOR')


class FormularioCita(FechaAgendaMixin, forms.Form):
    paciente_id = forms.ChoiceField(label='Paciente')
    doctor_id = forms.ChoiceField(widget=forms.HiddenInput)
    fecha = forms.DateField(widget=forms.HiddenInput)
    fecha_inicio = forms.ChoiceField(label='Turno disponible', error_messages={
        'invalid_choice': 'El turno seleccionado ya no está disponible. Consulta la agenda nuevamente.'})
    motivo_consulta = forms.CharField(label='Motivo de consulta', max_length=2000,
                                     widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paciente_id'].choices = opciones_usuarios('PACIENTE', usuario)
        self.fields['doctor_id'].choices = opciones_usuarios('DOCTOR')
        valores = self.data if self.is_bound else self.initial
        try:
            fecha = forms.DateField().clean(valores.get('fecha'))
        except ValidationError:
            fecha = None
        turnos = turnos_disponibles(valores.get('doctor_id'), fecha) if fecha else []
        self.fields['fecha_inicio'].choices = [('', 'Selecciona una hora')] + [
            (t['valor'], t['etiqueta']) for t in turnos]


class FormularioReprogramar(FechaAgendaMixin, forms.Form):
    version = forms.IntegerField(widget=forms.HiddenInput, min_value=1)
    fecha = forms.DateField(widget=forms.HiddenInput)
    fecha_inicio = forms.ChoiceField(label='Nuevo turno', error_messages={
        'invalid_choice': 'Este turno ya no está disponible. Consulta de nuevo.'})
    motivo = forms.CharField(label='Motivo de reprogramación', max_length=1000,
                             widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, cita, **kwargs):
        super().__init__(*args, **kwargs)
        valores = self.data if self.is_bound else self.initial
        try:
            fecha = forms.DateField().clean(valores.get('fecha'))
        except ValidationError:
            fecha = None
        turnos = turnos_disponibles(cita.doctor['id'], fecha, cita.paciente['id'], cita.pk) if fecha else []
        self.fields['fecha_inicio'].choices = [('', 'Selecciona una hora')] + [
            (t['valor'], t['etiqueta']) for t in turnos]


class FormularioEditarCita(forms.Form):
    version = forms.IntegerField(widget=forms.HiddenInput, min_value=1)
    estado = forms.ChoiceField(label='Estado')
    motivo_consulta = forms.CharField(label='Motivo de consulta', max_length=2000,
                                     widget=forms.Textarea(attrs={'rows': 3}))
    motivo_cancelacion = forms.CharField(label='Motivo de cancelación', required=False,
                                        max_length=1000, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, cita, puede_cancelar=True, **kwargs):
        super().__init__(*args, **kwargs)
        permitidos = TRANSICIONES.get(cita.estado, ())
        self.fields['estado'].choices = [(v, etiqueta) for v, etiqueta in Cita.ESTADOS_CITA
                                         if v in permitidos and (puede_cancelar or v != 'CANCELADA')]

    def clean(self):
        datos = super().clean()
        if datos.get('estado') == 'CANCELADA' and not datos.get('motivo_cancelacion'):
            self.add_error('motivo_cancelacion', 'Indica por qué se cancela la cita.')
        return datos


class FormularioCancelar(forms.Form):
    version = forms.IntegerField(widget=forms.HiddenInput, min_value=1)
    motivo_cancelacion = forms.CharField(label='Motivo de cancelación', max_length=1000,
                                        widget=forms.Textarea(attrs={'rows': 3}))


class FormularioEliminar(forms.Form):
    version = forms.IntegerField(widget=forms.HiddenInput, min_value=1)
    confirmar = forms.BooleanField(label='Confirmo la eliminación definitiva de esta cita cancelada')


class FormularioHorario(forms.Form):
    version = forms.IntegerField(widget=forms.HiddenInput, min_value=1, initial=1)
    doctor_id = forms.ChoiceField(label='Médico')
    dia_semana = forms.TypedChoiceField(label='Día de la semana', choices=HorarioMedico.DIAS, coerce=int)
    hora_inicio = forms.TimeField(label='Hora inicial', input_formats=['%H:%M'],
                                 widget=forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'))
    hora_fin = forms.TimeField(label='Hora final', input_formats=['%H:%M'],
                              widget=forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'))
    duracion_consulta_minutos = forms.IntegerField(label='Minutos por consulta', min_value=5, max_value=240, initial=30)
    activo = forms.BooleanField(label='Horario activo', required=False, initial=True)

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        opciones = opciones_usuarios('DOCTOR')
        if usuario and (usuario.rol or {}).get('nombre') == 'DOCTOR':
            opciones = [(clave, texto) for clave, texto in opciones if clave == str(usuario.pk)]
        self.fields['doctor_id'].choices = opciones

    def clean(self):
        datos = super().clean()
        inicio, fin = datos.get('hora_inicio'), datos.get('hora_fin')
        if inicio and fin and fin <= inicio:
            self.add_error('hora_fin', 'Debe ser posterior a la hora inicial.')
        return datos


class FormularioFiltros(forms.Form):
    q = forms.CharField(label='Buscar paciente, médico o ID de cita', max_length=100, required=False)
    estado = forms.ChoiceField(label='Estado', required=False,
                               choices=[('', 'Todos los estados')] + Cita.ESTADOS_CITA)
    desde = forms.DateField(label='Desde', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    hasta = forms.DateField(label='Hasta', required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def clean(self):
        datos = super().clean()
        if datos.get('desde') and datos.get('hasta') and datos['desde'] > datos['hasta']:
            raise ValidationError('La fecha inicial no puede ser posterior a la final.')
        return datos
