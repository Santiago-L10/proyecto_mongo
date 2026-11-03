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
    telefono = models.CharField(max_length=30, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.nombre_completo} - Usuario: {self.id_user}"

class HorarioMedico(models.Model):
    DIAS = [(0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'), (3, 'Jueves'),
            (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo')]
    doctor = models.EmbeddedField(model_container=DoctorSnapshot)
    dia_semana = models.IntegerField(choices=DIAS)
    minuto_inicio = models.IntegerField()
    minuto_fin = models.IntegerField()
    duracion_consulta_minutos = models.IntegerField(default=30)
    zona_horaria = models.CharField(max_length=50, default='America/Bogota')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "horarios_medicos"

    def __str__(self):
        return f"Horario Día {self.dia_semana} - {self.doctor['nombre_completo']}"


class Cita(models.Model):
    ESTADOS_CITA = [
        ('PROGRAMADA', 'Programada'),
        ('EN_ESPERA', 'En espera'),
        ('EN_CONSULTA', 'En consulta'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
        ('NO_ASISTIO', 'No asistió'),
    ]

    paciente = models.EmbeddedField(model_container=PacienteSnapshot)
    doctor = models.EmbeddedField(model_container=DoctorSnapshot)
    horario_id = models.CharField(max_length=24, null=True, blank=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    duracion_minutos = models.IntegerField(default=30)
    estado = models.CharField(max_length=20, choices=ESTADOS_CITA, default='PROGRAMADA')
    motivo_consulta = models.TextField(null=True, blank=True)
    motivo_cancelacion = models.TextField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)
    historial = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "citas"

    def __str__(self):
        return f"Cita: {self.paciente['nombre_completo']} - {self.estado}"


class BloqueoAgenda(models.Model):
    """Serializa las escrituras del módulo, incluso entre procesos del servidor."""
    clave = models.CharField(max_length=40, unique=True)
    token = models.CharField(max_length=32)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'citas_bloqueos_agenda'
