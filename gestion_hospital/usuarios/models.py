from djongo import models

class Rol(models.Model):

    class Nombre(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        DOCTOR = "DOCTOR", "Doctor"
        PACIENTE = "PACIENTE", "Paciente"
        FARMACEUTICO = "FARMACEUTICO", "Farmacéutico"
        RECEPCIONISTA = "RECEPCIONISTA", "Recepcionista"

    nombre = models.CharField(max_length=20, choices=Nombre.choices)
    permisos = models.JSONField(default=list)

    class Meta:
        abstract = True


class DatosProfesionales(models.Model):

    especialidad = models.CharField(max_length=150, blank=True)
    registro_medico = models.CharField(max_length=100, blank=True)

    class Meta:
        abstract = True


class Cirugia(models.Model):

    procedimiento = models.CharField(max_length=200)
    year = models.IntegerField()
    hospital = models.CharField(max_length=200, blank=True)

    class Meta:
        abstract = True


class AntecedentesClinicos(models.Model):

    class TipoSangre(models.TextChoices):
        A_POS = "A+"
        A_NEG = "A-"
        B_POS = "B+"
        B_NEG = "B-"
        AB_POS = "AB+"
        AB_NEG = "AB-"
        O_POS = "O+"
        O_NEG = "O-"

    tipo_sangre = models.CharField(max_length=3, choices=TipoSangre.choices)
    alergias = models.JSONField(default=list)
    condiciones_cronicas = models.JSONField(default=list)
    cirugias = models.ArrayField(model_container=Cirugia, default=list)
    historial_familiar = models.JSONField(default=list)
    fecha_actualizacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class User(models.Model):

    class Activo(models.TextChoices):
        SI = "SI", "Sí"
        NO = "NO", "No"

    id_user = models.CharField(
        max_length=50,
        unique=True,
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    telefono = models.CharField(max_length=30, blank=True)
    activo = models.CharField(max_length=2, choices=Activo.choices, default=Activo.SI)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    rol = models.EmbeddedField(model_container=Rol)
    datos_profesionales = models.EmbeddedField(
        model_container=DatosProfesionales,
        null=True,
        blank=True,
    )
    antecedentes_clinicos = models.EmbeddedField(
        model_container=AntecedentesClinicos,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "users"



class RefreshToken(models.Model):

    token_jti = models.CharField(max_length=255, unique=True)
    user_id = models.GenericObjectIdField()
    expire = models.DateTimeField()
    revoked = models.BooleanField(default=False)

    class Meta:
        db_table = "RefreshToken"



class Log(models.Model):

    user_id = models.GenericObjectIdField()
    action = models.CharField(max_length=100)
    date = models.DateTimeField()
    details = models.TextField()
    status = models.CharField(max_length=20)

    class Meta:
        db_table = "Logs"
