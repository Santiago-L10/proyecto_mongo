from djongo import models

# Create your models here.
class Titular(models.Model):
	id = models.CharField(max_length=24)
	id_user = models.CharField(max_length=24)
	nombre_completo = models.CharField(max_length=150) 

	class Meta:
		abstract = True


class Polizas(models.Model):
	codigo_poliza = models.CharField(max_length=20, unique=True, help_text="Ej: POL-1234")
	titular = models.EmbeddedField(model_container=Titular)
	aseguradora = models.CharField(max_length=100)
	tipo_servicio = models.CharField(max_length=100, null=True, blank=True, help_text="Ej: Plan Oro, Medicina Prepagada, EPS")
	porcentaje_cobertura_general = models.FloatField(help_text="De 0 a 100")
	fecha_inicio = models.DateField()
	fecha_fin = models.DateField()
	coberturas = models.JSONField(null=True, blank=True)


class Paciente(models.Model):
	id = models.CharField(max_length=24)
	id_user = models.CharField(max_length=20)
	nombre_completo = models.CharField(max_length=150)

	class Meta:
		abstract = True


class Items(models.Model):
	tipos = [
		("CONSULTA", "Consulta"),
		("MEDICAMENTO", "Medicamento"),
		("LABORATORIO", "Laboratorio"),
		("PROCEDIMIENTO", "Procedimiento")
	]
	concepto = models.CharField(max_length=225)
	tipo = models.CharField(max_length=50, choices=tipos)
	referencia_id = models.CharField(max_length=24, null=True, blank=True)
	cantidad = models.PositiveIntegerField()
	precio_unitario = models.FloatField()
	subtotal = models.FloatField()

	class Meta:
		abstract = True


class CoberturaSeguro(models.Model):
	codigo_poliza = models.CharField(max_length=20, unique=True, help_text="Ej: POL-1234")
	aseguradora = models.CharField(max_length=100)
	monto_cubierto = models.FloatField()

	class Meta:
		abstract = True


class Facturas(models.Model):
	estados = [
		("PENDIENTE", "Pendiente"),
		("PAGADA", "Pagada"),
		("ANULADA", "Anulada")
	]
	metodos_pago = [
		("EFECTIVO", "Efectivo"),
		("TARJETA_CREDITO", "Tarjeta crédito"),
		("TARJETA_DEBITO", "Tarjeta débito"),
		("TRANSFERENCIA", "Transferencia"),
		("SEGURO_TOTAL", "Seguro total")
	]
	numero_factura = models.CharField(max_length=20, unique=True, help_text="Formato FAC-2026-0001")
	fecha_emision = models.DateTimeField()
	estado = models.CharField(max_length=20, choices=estados)
	metodo_pago = models.CharField(max_length=30, choices=metodos_pago)
	paciente = models.EmbeddedField(model_container=Paciente)
	items = models.ArrayField(model_container=Items)
	cobertura_seguro = models.EmbeddedField(model_container=CoberturaSeguro, null=True, blank=True)
	total_bruto = models.FloatField()
	iva = models.FloatField()
	valor_neto_pagar = models.FloatField()