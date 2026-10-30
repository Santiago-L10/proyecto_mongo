from djongo import models

class DoctorSnapshot(models.Model):
    id = models.CharField(max_length=24)
    nombre_completo = models.CharField(max_length=200)
    especialidad = models.CharField(max_length=150)

    class Meta:
        abstract = True

    def __str__(self):
        return f"Dr(a). {self.nombre_completo} ({self.especialidad})"


class PacienteSnapshot(models.Model):
    id = models.CharField(max_length=24)
    id_user = models.CharField(max_length=50)
    nombre_completo = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.nombre_completo} - CC: {self.id_user}"

class HorarioMedico(models.Model):
    doctor = models.EmbeddedModelField(model_container=DoctorSnapshot)
    dia_semana = models.IntegerField()
    minuto_inicio = models.IntegerField()
    minuto_fin = models.IntegerField()
    duracion_consulta_minutos = models.IntegerField(default=30)
    zona_horaria = models.CharField(max_length=50, default='America/Bogota')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "horarios_medicos"

    def __str__(self):
        return f"Horario Día {self.dia_semana} - {self.doctor.nombre_completo}"


class Cita(models.Model):
    ESTADOS_CITA = [
        ('PROGRAMADA', 'PROGRAMADA'),
        ('EN_ESPERA', 'EN_ESPERA'),
        ('EN_CONSULTA', 'EN_CONSULTA'),
        ('COMPLETADA', 'COMPLETADA'),
        ('CANCELADA', 'CANCELADA'),
    ]

    paciente = models.EmbeddedModelField(model_container=PacienteSnapshot)
    doctor = models.EmbeddedModelField(model_container=DoctorSnapshot)
    horario_id = models.CharField(max_length=24, null=True, blank=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    duracion_minutos = models.IntegerField(default=30)
    estado = models.CharField(max_length=20, choices=ESTADOS_CITA, default='PROGRAMADA')
    motivo_consulta = models.TextField(null=True, blank=True)
    motivo_cancelacion = models.TextField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "citas"

    def __str__(self):
        return f"Cita: {self.paciente.nombre_completo} - {self.estado}"