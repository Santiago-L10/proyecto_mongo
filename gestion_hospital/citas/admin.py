from django.contrib import admin
from .models import HorarioMedico, Cita

@admin.register(HorarioMedico)
class HorarioMedicoAdmin(admin.ModelAdmin):
    list_display = ('doctor_nombre', 'dia_semana', 'minuto_inicio', 'minuto_fin', 'activo')
    list_filter = ('dia_semana', 'activo')

    def doctor_nombre(self, obj):
        return obj.doctor.nombre_completo if obj.doctor else "-"
    doctor_nombre.short_description = 'Médico'


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('paciente_nombre', 'doctor_nombre', 'fecha_inicio', 'duracion_minutos', 'estado')
    list_filter = ('estado', 'fecha_inicio')
    search_fields = ('paciente__nombre_completo', 'doctor__nombre_completo', 'paciente__id_user')

    def paciente_nombre(self, obj):
        return obj.paciente.nombre_completo if obj.paciente else "-"
    paciente_nombre.short_description = 'Paciente'

    def doctor_nombre(self, obj):
        return obj.doctor.nombre_completo if obj.doctor else "-"
    doctor_nombre.short_description = 'Medico'