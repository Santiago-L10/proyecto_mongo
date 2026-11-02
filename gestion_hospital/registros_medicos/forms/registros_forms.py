from django import forms
from bson import ObjectId
from bson.errors import InvalidId
#from citas.models import Cita


class RegistroMedicoForm(forms.Form):
    # Cita origen
    cita_id = forms.CharField(max_length=24, required=False)

    # Paciente
    id_paciente = forms.CharField(max_length=50, required=True)
    nombre_paciente = forms.CharField(max_length=150, required=True)
    tipo_sangre = forms.CharField(max_length=5, required=True)
    alergias_relevantes = forms.CharField(required=False)

    # Doctor
    id_doctor = forms.CharField(max_length=50, required=True)
    nombre_doctor = forms.CharField(max_length=150, required=True)
    especialidad = forms.CharField(max_length=100, required=True)
    registro_medico = forms.CharField(max_length=100, required=False)

    # Signos Vitales
    presion_arterial = forms.CharField(max_length=20, required=True)
    frecuencia_cardiaca = forms.FloatField(required=True)
    frecuencia_respiratoria = forms.FloatField(required=True)
    temperatura = forms.FloatField(required=True)
    peso_kg = forms.FloatField(required=True)
    estatura_cm = forms.FloatField(required=True)

    # Evaluación Clínica
    queja_principal = forms.CharField(required=True)
    examen_fisico = forms.CharField(required=True)
    codigo_diagnostico = forms.CharField(max_length=20, required=True)
    descripcion_diagnostico = forms.CharField(required=True)
    tratamiento = forms.CharField(required=True)
    notas_adicionales = forms.CharField(required=False)

    def clean_cita_id(self):
        cita_id = self.cleaned_data.get('cita_id')

        # 1. Si se deja vacío (urgencia), retorna None sin consultar la base de datos
        if not cita_id or cita_id.strip() == "":
            return None

        cita_id = cita_id.strip()

        # 2. Verificar que tenga formato válido de ObjectId (24 caracteres hexadecimales)
        try:
            obj_id = ObjectId(cita_id)
        except InvalidId:
            raise forms.ValidationError("El ID de la cita no tiene un formato ObjectId válido.")

        # 3. Verificar con el ORM (.exists()) en la otra aplicación si la cita existe
        if not Cita.objects.filter(_id=obj_id).exists():
            raise forms.ValidationError("No existe ninguna cita registrada con este ID en la base de datos.")

        return cita_id