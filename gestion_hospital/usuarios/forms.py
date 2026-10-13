from django import forms
from django.utils import timezone

from . import models
from .acceso import SECCION_POR_ROL


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


#Paso 2: datos del usuario.
class UsuarioForm(forms.Form):

    first_name = forms.CharField(max_length=100, label="Nombres")
    last_name = forms.CharField(max_length=100, label="Apellidos")
    email = forms.EmailField(label="Correo")
    telefono = forms.CharField(max_length=30, required=False, label="Teléfono")
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput,
        label="Contraseña",
    )

    def __init__(self, data=None, rol_nombre=None):
        super().__init__(data)
        self.rol_nombre = rol_nombre
        seccion = SECCION_POR_ROL.get(rol_nombre)

        if seccion == "datos_profesionales":
            self.fields["especialidad"] = forms.CharField(
                max_length=150, required=False, label="Especialidad"
            )
            self.fields["registro_medico"] = forms.CharField(
                max_length=100, required=False, label="Registro médico"
            )
        elif seccion == "antecedentes_clinicos":
            self.fields["tipo_sangre"] = forms.ChoiceField(
                choices=models.AntecedentesClinicos.TipoSangre.choices,
                label="Tipo de sangre",
            )
            self.fields["alergias"] = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Una por línea"}),
                label="Alergias",
            )
            self.fields["condiciones_cronicas"] = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Una por línea"}),
                label="Condiciones crónicas",
            )
            self.fields["cirugia_procedimiento"] = forms.CharField(
                max_length=200, required=False, label="Cirugía: procedimiento"
            )
            self.fields["cirugia_year"] = forms.IntegerField(
                required=False, label="Cirugía: año"
            )
            self.fields["cirugia_hospital"] = forms.CharField(
                max_length=200, required=False, label="Cirugía: hospital"
            )
            self.fields["historial_familiar"] = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Una por línea"}),
                label="Historial familiar",
            )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if models.User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un usuario con ese correo.")
        return email

    #Convierte texto separado por líneas o comas en una lista.
    @staticmethod
    def _a_lista(texto):
        if not texto:
            return []
        items = []
        for linea in texto.replace(",", "\n").splitlines():
            item = linea.strip()
            if item:
                items.append(item)
        return items

    #Convierte los campos de cirugía del formulario en la lista que guarda la BD.
    def _a_cirugias(self, datos):
        procedimiento = datos.get("cirugia_procedimiento", "").strip()
        if not procedimiento:
            return []
        return [
            {
                "procedimiento": procedimiento,
                "year": datos.get("cirugia_year") or 0,
                "hospital": datos.get("cirugia_hospital", ""),
            }
        ]

    #djongo espera dicts (y listas de dicts) en los campos embebidos.
    def guardar(self):
        datos = self.cleaned_data
        user = models.User(
            first_name=datos["first_name"],
            last_name=datos["last_name"],
            email=datos["email"],
            telefono=datos.get("telefono", ""),
            password=datos["password"],
            rol={"nombre": self.rol_nombre},
        )

        seccion = SECCION_POR_ROL.get(self.rol_nombre)
        if seccion == "datos_profesionales":
            user.datos_profesionales = {
                "especialidad": datos.get("especialidad", ""),
                "registro_medico": datos.get("registro_medico", ""),
            }
        elif seccion == "antecedentes_clinicos":
            user.antecedentes_clinicos = {
                "tipo_sangre": datos["tipo_sangre"],
                "alergias": self._a_lista(datos.get("alergias", "")),
                "condiciones_cronicas": self._a_lista(datos.get("condiciones_cronicas", "")),
                "cirugias": self._a_cirugias(datos),
                "historial_familiar": self._a_lista(datos.get("historial_familiar", "")),
                "fecha_actualizacion": timezone.now(),
            }

        user.save()
        return user


#Editar los datos básicos de un usuario (rol y fecha de creación no se tocan).
class UsuarioEditarForm(forms.Form):

    first_name = forms.CharField(max_length=100, label="Nombres")
    last_name = forms.CharField(max_length=100, label="Apellidos")
    email = forms.EmailField(label="Correo")
    telefono = forms.CharField(max_length=30, required=False, label="Teléfono")
    activo = forms.BooleanField(required=False, label="Activo")

    def __init__(self, data=None, usuario=None):
        super().__init__(data)
        self.usuario = usuario

    def clean_email(self):
        email = self.cleaned_data["email"]
        existentes = models.User.objects.filter(email=email)
        if self.usuario is not None:
            existentes = existentes.exclude(id=self.usuario.id)
        if existentes.exists():
            raise forms.ValidationError("Ya existe un usuario con ese correo.")
        return email

    def guardar(self):
        user = self.usuario
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.telefono = self.cleaned_data["telefono"]
        if self.cleaned_data.get("activo"):
            user.activo = "SI"
        else:
            user.activo = "NO"
        user.save()
        return user
