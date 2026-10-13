from django import forms

from .. import models


#djongo no soporta filtrar por BooleanField, así que se filtra en Python.
def _perfiles_activos():
    activos = []
    for perfil in models.Perfil.objects.all():
        if perfil.activo:
            activos.append(perfil)
    return activos


class PerfilForm(forms.ModelForm):
    class Meta:
        model = models.Perfil
        fields = ["nombre", "descripcion"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }


#Paso 1: elegir el rol del usuario que se va a registrar.
class SeleccionRolForm(forms.Form):

    rol = forms.ChoiceField(label="Rol")

    def __init__(self, data=None):
        super().__init__(data)
        opciones = []
        for perfil in _perfiles_activos():
            opciones.append((perfil.nombre, perfil.get_nombre_display()))
        self.fields["rol"].choices = opciones
