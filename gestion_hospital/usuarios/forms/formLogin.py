from django import forms

from .. import models


class LoginForm(forms.Form):

    email = forms.EmailField(label="Correo")
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")

    def clean(self):
        datos = super().clean()
        email = datos.get("email")
        password = datos.get("password")
        if not email or not password:
            return datos

        usuario = models.User.objects.filter(email=email).first()
        if usuario is None:
            raise forms.ValidationError("El correo o la contraseña son incorrectos.")
        if usuario.password != password:
            raise forms.ValidationError("El correo o la contraseña son incorrectos.")
        if usuario.activo != "SI":
            raise forms.ValidationError("Tu usuario está inactivo. Contacta al administrador.")

        self.usuario = usuario
        return datos
