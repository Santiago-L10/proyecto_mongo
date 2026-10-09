from django.core.validators import MinValueValidator
from djongo import models


class MedicationCatalog(models.Model):

    nombre_generico = models.CharField(
        max_length=200
    )
    nombre_comercial = models.CharField(max_length=200, blank=True)
    presentacion = models.CharField(
        max_length=100
    )
    concentracion = models.CharField(
        max_length=100
    )
    lote = models.CharField(max_length=100)
    fecha_vencimiento = models.DateField()
    precio_unitario = models.FloatField(validators=[MinValueValidator(0)])
    stock_disponible = models.IntegerField(validators=[MinValueValidator(0)])
    requiere_receta = models.BooleanField(default=False)
    interacciones = models.JSONField(default=list)

    class Meta:
        db_table = "medication_catalog"


class Paciente(models.Model):

    id_user = models.CharField(max_length=50)
    nombre_completo = models.CharField(max_length=200)

    class Meta:
        abstract = True


class Doctor(models.Model):

    nombre_completo = models.CharField(max_length=200)
    registro_medico = models.CharField(max_length=100)

    class Meta:
        abstract = True


class MedicamentoRecetado(models.Model):

    nombre_generico = models.CharField(max_length=200)
    concentracion = models.CharField(max_length=100)
    presentacion = models.CharField(max_length=100)
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    dosis = models.CharField(
        max_length=200
    )
    duracion_dias = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
    )
    precio_unitario = models.FloatField(
        validators=[MinValueValidator(0)]
    )

    class Meta:
        abstract = True


class DispensadoPor(models.Model):

    nombre_completo = models.CharField(max_length=200, blank=True)

    class Meta:
        abstract = True

class Prescription(models.Model):

    class Estado(models.TextChoices):
        EMITIDA = "EMITIDA", "Emitida"
        DISPENSADA = "DISPENSADA", "Dispensada"
        VENCIDA = "VENCIDA", "Vencida"
        CANCELADA = "CANCELADA", "Cancelada"

    codigo_validacion = models.CharField(
        max_length=100,
        unique=True
    )
    fecha_emision = models.DateTimeField()
    registro_medico_id = models.GenericObjectIdField(
        null=True,
        blank=True
    )

    paciente = models.EmbeddedField(model_container=Paciente)
    doctor = models.EmbeddedField(model_container=Doctor)
    medicamentos = models.ArrayField(model_container=MedicamentoRecetado)

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.EMITIDA,
    )
    fecha_dispensacion = models.DateTimeField(null=True, blank=True)
    dispensado_por = models.EmbeddedField(
        model_container=DispensadoPor,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "prescriptions"
