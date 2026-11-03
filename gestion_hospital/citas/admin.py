from django.contrib import admin
from .models import HorarioMedico, Cita


class ConsultaAgendaAdmin(admin.ModelAdmin):
    # Los formularios del módulo aplican las reglas y el bloqueo de agenda.
    # El admin queda disponible para consulta, sin una vía de escritura paralela.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HorarioMedico)
class HorarioMedicoAdmin(ConsultaAgendaAdmin):
    list_display = ('doctor_nombre', 'dia_semana', 'minuto_inicio', 'minuto_fin', 'activo')
    list_filter = ('dia_semana', 'activo')

    def doctor_nombre(self, obj):
        return obj.doctor.get('nombre_completo', '-') if obj.doctor else "-"
    doctor_nombre.short_description = 'Médico'


@admin.register(Cita)
class CitaAdmin(ConsultaAgendaAdmin):
    list_display = ('paciente_nombre', 'doctor_nombre', 'fecha_inicio', 'duracion_minutos', 'estado')
    list_filter = ('estado', 'fecha_inicio')

    def paciente_nombre(self, obj):
        return obj.paciente.get('nombre_completo', '-') if obj.paciente else "-"
    paciente_nombre.short_description = 'Paciente'

    def doctor_nombre(self, obj):
        return obj.doctor.get('nombre_completo', '-') if obj.doctor else "-"
    doctor_nombre.short_description = 'Medico'
