from django import forms

class FormularioCita(forms.Form):
    paciente_id = forms.CharField(max_length=24, label='ID Paciente', initial='65f1a2b3c4d5e6f7a8b9c001')
    paciente_documento = forms.CharField(max_length=50, label='Documento del paciente')
    paciente_nombre = forms.CharField(max_length=200, label='Nombre del paciente')
    paciente_telefono = forms.CharField(max_length=20, label='Telefono de contacto')

    doctor_id = forms.CharField(max_length=24, label='ID Médico', initial='65f1a2b3c4d5e6f7a8b9c002')
    doctor_nombre = forms.CharField(max_length=200, label='Nombre del medico')
    doctor_especialidad = forms.CharField(max_length=150, label='Especialidad')

    fecha_inicio = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label='Fecha y hora de Inicio'
    )
    duracion_minutos = forms.IntegerField(label='Duración en minutos', initial=30)
    motivo_consulta = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Motivo de consulta')


class FormularioEditarCita(forms.Form):
    ESTADOS_CHOICES = [
        ('PROGRAMADA', 'PROGRAMADA'),
        ('EN_ESPERA', 'EN_ESPERA'),
        ('EN_CONSULTA', 'EN_CONSULTA'),
        ('COMPLETADA', 'COMPLETADA'),
        ('CANCELADA', 'CANCELADA'),
    ]
    estado = forms.ChoiceField(choices=ESTADOS_CHOICES, label='Estado de la Cita')
    motivo_consulta = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Motivo de consulta', required=False)
    motivo_cancelacion = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Motivo de cancelacion', required=False)