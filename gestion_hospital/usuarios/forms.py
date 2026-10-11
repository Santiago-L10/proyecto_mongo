from django import forms

from . import models


class PerfilForm(forms.ModelForm):
    class Meta:
        model = models.Perfil
        fields = ["nombre", "descripcion", "activo"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }
