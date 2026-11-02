from django import forms
from bson import ObjectId
from bson.errors import InvalidId
from ..models import RegistroMedico


class EstudioLaboratorioForm(forms.Form):
    registro_medico_id = forms.CharField(max_length=24, required=False) # Nombre que debe tener la funcion clean
    id_paciente = forms.CharField(max_length=50, required=True)
    nombre_paciente = forms.CharField(max_length=150, required=True)
    id_doctor = forms.CharField(max_length=50, required=True)
    nombre_doctor = forms.CharField(max_length=150, required=True)
    especialidad = forms.CharField(max_length=100, required=False)
    nombre_estudio = forms.CharField(max_length=150, required=True)
    categoria = forms.CharField(max_length=15, required=True)

    def clean_registro_medico_id(self): 
        # En Django, la convención para validar un campo específico exige que el método se llame estrictamente clean_<nombre_del_campo>()

        registro_id = self.cleaned_data.get('registro_medico_id')

        # 1. Si se deja en blanco, retorna None sin ejecutar .exists()
        if not registro_id or registro_id.strip() == "":
            return None

        registro_id = registro_id.strip()

        # 2. Verificar que el texto tenga formato válido de ObjectId (24 caracteres hex)
        try:
            obj_id = ObjectId(registro_id)
        except InvalidId:
            raise forms.ValidationError("El ID ingresado no tiene un formato ObjectId válido.")

        # 3. Verificar en MongoDB si el Registro Médico existe usando .exists() del ORM
        if not RegistroMedico.objects.filter(_id=obj_id).exists():
            raise forms.ValidationError("No existe ningún registro médico con este ID en la base de datos.")

        return registro_id