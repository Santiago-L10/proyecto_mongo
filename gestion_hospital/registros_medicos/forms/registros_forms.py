from django import forms
from django.core.exceptions import ValidationError
from citas.models import Cita


class RegistroMedicoForm(forms.Form):
    cita_id = forms.CharField(max_length=24, required=False)
    id_paciente = forms.CharField(max_length=50, required=True)
    nombre_paciente = forms.CharField(max_length=150, required=True)
    tipo_sangre = forms.CharField(max_length=5, required=True)
    alergias_relevantes = forms.CharField(required=False)
    id_doctor = forms.CharField(max_length=50, required=True)
    nombre_doctor = forms.CharField(max_length=150, required=True)
    especialidad = forms.CharField(max_length=100, required=True)
    registro_medico = forms.CharField(max_length=100, required=False)
    presion_arterial = forms.CharField(max_length=20, required=True)
    frecuencia_cardiaca = forms.FloatField(required=True)
    frecuencia_respiratoria = forms.FloatField(required=True)
    temperatura = forms.FloatField(required=True)
    peso_kg = forms.FloatField(required=True)
    estatura_cm = forms.FloatField(required=True)
    queja_principal = forms.CharField(required=True)
    examen_fisico = forms.CharField(required=True)
    codigo_diagnostico = forms.CharField(max_length=20, required=True)
    descripcion_diagnostico = forms.CharField(required=True)
    tratamiento = forms.CharField(required=True)
    notas_adicionales = forms.CharField(required=False)


    def clean_cita_id(self):
        cita_id = self.cleaned_data.get('cita_id')

        if not cita_id or cita_id.strip() == "":
            return None

        cita_id = cita_id.strip()

        try:
            clave = Cita._meta.pk.to_python(cita_id)

        except (ValidationError, ValueError, TypeError):
            raise forms.ValidationError("El ID de la cita debe ser un número entero válido.")

        if not Cita.objects.filter(pk=clave).exists():
            raise forms.ValidationError("No existe ninguna cita registrada con este ID en la base de datos.")

        return str(clave)
