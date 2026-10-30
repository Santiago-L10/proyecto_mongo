from djongo import models


class Paciente(models.Model):
     id_paciente = models.CharField(max_length = 50)
     nombre_paciente = models.CharField(max_length=150)
     tipo_sangre = models.CharField(max_length = 5, blank = True, null = True)
     alergias_relevantes = models.JSONField(default=list, blank=True, null=True)

     class Meta:
          abstract = True


class Doctor(models.Model):
     id_doctor = models.CharField(max_length=50)
     nombre_doctor = models.CharField(max_length = 150)
     especialidad = models.CharField(max_length = 100)
     registro_medico = models.CharField(max_length = 100, blank = True, null = True)

     class Meta:
          abstract = True


class SignosVitales(models.Model):
     presion_arterial = models.CharField(max_length = 20)
     frecuencia_cardiaca = models.FloatField()
     frecuencia_respiratoria = models.FloatField()
     temperatura = models.FloatField()
     peso_kg = models.FloatField()
     estatura_cm = models.FloatField()
     bmi = models.FloatField(blank = True, null = True)

     class Meta:
          abstract = True


class Diagnostico(models.Model):
     codigo = models.CharField(max_length = 20)
     descripcion = models.TextField()

     class Meta:
          abstract = True


class RegistroMedico(models.Model):
     _id = models.ObjectIdField()
     fecha = models.DateTimeField(auto_now_add = True)
     cita_id = models.CharField(max_length=24, null=True, blank=True)
     paciente = models.EmbeddedField(model_container = Paciente)
     doctor = models.EmbeddedField(model_container = Doctor)
     queja_principal = models.TextField()
     examen_fisico = models.TextField()
     signos_vitales = models.EmbeddedField(model_container = SignosVitales)
     diagnostico = models.ArrayField(model_container = Diagnostico)
     tratamiento = models.TextField()
     notas_adicionales = models.TextField(blank = True, null = True)

     class Meta:
        db_table = "registros_medicos"



class EstudioLaboratorio(models.Model):
     _id = models.ObjectIdField()
     registro_medico_id = models.CharField(max_length=24, null=True, blank=True)
     paciente = models.EmbeddedField(model_container = Paciente)
     solicitado_por = models.EmbeddedField(model_container = Doctor)
     nombre_estudio = models.CharField(max_length = 150)
     CATEGORIAS_OPCIONES = [
        ("LABORATORIO", "LABORATORIO"),
        ("IMAGENOLOGIA", "IMAGENOLOGIA"),
        ("PATOLOGIA", "PATOLOGIA"),
        ("OTRO", "OTRO")                                
        ]
     categoria = models.CharField(max_length = 15, choices = CATEGORIAS_OPCIONES)
     ESTATUS_OPCIONES = [
        ("SOLICITADO", "SOLICITADO"),
        ("EN_PROCESO", "EN_PROCESO"),
        ("COMPLETADO", "COMPLETADO"),
        ("CANCELADO", "CANCELADO")
        ]
     estatus = models.CharField(max_length = 15, choices = ESTATUS_OPCIONES)
     solicitud_examen = models.DateTimeField(auto_now_add = True)
     reporte_resultado = models.DateTimeField(blank = True, null = True)
     resultado = models.JSONField(blank=True, null=True)
     interpretacion = models.TextField(blank = True, null = True)


     class Meta:
        db_table = "estudios_laboratorio"
