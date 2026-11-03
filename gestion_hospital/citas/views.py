from datetime import time

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from . import servicios
from .acceso import acceso_citas, acciones, obtener_cita, puede_ver
from .forms import (FormularioCita, FormularioDisponibilidad, FormularioEditarCita,
                    FormularioCancelar, FormularioEliminar, FormularioFiltros,
                    FormularioHorario, FormularioReprogramar)
from .models import Cita, HorarioMedico


def errores(formulario, error):
    for mensaje in error.messages:
        formulario.add_error(None, mensaje)


@acceso_citas
@require_http_methods(['GET'])
def listar_citas(request, estado_filtro=None):
    parametros = request.GET.copy()
    if estado_filtro:
        estado_filtro = estado_filtro.upper()
        if estado_filtro not in dict(Cita.ESTADOS_CITA):
            raise Http404('Estado de cita inválido.')
        parametros['estado'] = estado_filtro
    formulario = FormularioFiltros(parametros)
    citas = []
    if formulario.is_valid():
        datos = formulario.cleaned_data
        consulta = Cita.objects.all().order_by('-fecha_inicio')
        if datos['estado']:
            consulta = consulta.filter(estado=datos['estado'])
        for cita in consulta:
            if not puede_ver(request, cita):
                continue
            fecha = timezone.localtime(cita.fecha_inicio).date()
            if datos['desde'] and fecha < datos['desde'] or datos['hasta'] and fecha > datos['hasta']:
                continue
            texto = f"{cita.pk} {cita.paciente['nombre_completo']} {cita.doctor['nombre_completo']} {cita.doctor['especialidad']}"
            if datos['q'] and datos['q'].casefold() not in texto.casefold():
                continue
            citas.append({'cita': cita, 'acciones': acciones(request, cita)})
    pagina = Paginator(citas, 15).get_page(request.GET.get('page'))
    parametros.pop('page', None)
    return render(request, 'citas/listar_citas.html', {
        'formulario': formulario, 'pagina': pagina, 'total': len(citas),
        'parametros': parametros.urlencode(), 'titulo': 'Agenda de citas',
    })


filtrar_citas = listar_citas


@acceso_citas
@require_http_methods(['GET'])
def detalle_cita(request, cita_id):
    cita = obtener_cita(request, cita_id)
    return render(request, 'citas/detalle_cita.html', {'cita': cita, 'acciones': acciones(request, cita)})


@acceso_citas
@require_http_methods(['GET', 'POST'])
def agendar_cita(request):
    if request.rol_citas == 'DOCTOR':
        return HttpResponseForbidden('El agendamiento lo realiza recepción, administración o el paciente.')
    datos = request.POST if request.method == 'POST' else request.GET
    consulta = FormularioDisponibilidad(datos or None)
    disponible = consulta.is_valid() if consulta.is_bound else False
    inicial = {'doctor_id': datos.get('doctor_id'), 'fecha': datos.get('fecha')}
    if request.rol_citas == 'PACIENTE':
        inicial['paciente_id'] = str(request.usuario_citas.pk)
    formulario = FormularioCita(request.POST if request.method == 'POST' else None,
                                 initial=inicial, usuario=request.usuario_citas)
    if request.method == 'POST' and formulario.is_valid():
        try:
            cita = servicios.crear_cita(formulario.cleaned_data, request.usuario_citas)
        except ValidationError as error:
            errores(formulario, error)
        else:
            messages.success(request, 'Cita agendada correctamente.')
            return redirect('citas:detalle_cita', cita_id=cita.pk)
    return render(request, 'citas/agendar_cita.html', {
        'consulta': consulta, 'disponible': disponible, 'formulario': formulario,
        'hay_turnos': len(formulario.fields['fecha_inicio'].choices) > 1,
    })


@acceso_citas
@require_http_methods(['GET', 'POST'])
def reprogramar_cita(request, cita_id):
    cita = obtener_cita(request, cita_id)
    if not acciones(request, cita)['reprogramar']:
        return HttpResponseForbidden('Esta cita no puede reprogramarse.')
    fecha = request.POST.get('fecha') if request.method == 'POST' else request.GET.get('fecha')
    if not fecha:
        fecha = timezone.localtime(cita.fecha_inicio).date().isoformat()
    consulta = FormularioDisponibilidad({'doctor_id': cita.doctor['id'], 'fecha': fecha})
    disponible = consulta.is_valid()
    consulta.fields['doctor_id'].widget = forms.HiddenInput()
    formulario = FormularioReprogramar(request.POST if request.method == 'POST' else None,
        cita=cita, initial={'fecha': fecha, 'version': cita.version})
    if request.method == 'POST' and formulario.is_valid():
        try:
            servicios.reprogramar(cita.pk, formulario.cleaned_data, request.usuario_citas)
        except ValidationError as error:
            errores(formulario, error)
        else:
            messages.success(request, 'La cita fue reprogramada. Se conservó el historial anterior.')
            return redirect('citas:detalle_cita', cita_id=cita.pk)
    return render(request, 'citas/reprogramar_cita.html', {
        'cita': cita, 'consulta': consulta, 'formulario': formulario, 'disponible': disponible,
        'hay_turnos': len(formulario.fields['fecha_inicio'].choices) > 1,
    })


@acceso_citas
@require_http_methods(['GET', 'POST'])
def actualizar_cita(request, cita_id):
    cita = obtener_cita(request, cita_id)
    if not acciones(request, cita)['editar']:
        return HttpResponseForbidden('No puedes modificar esta cita.')
    formulario = FormularioEditarCita(request.POST if request.method == 'POST' else None,
        cita=cita, puede_cancelar=request.gestiona_citas, initial={
            'version': cita.version, 'estado': cita.estado, 'motivo_consulta': cita.motivo_consulta,
        })
    if request.method == 'POST' and formulario.is_valid():
        try:
            servicios.cambiar_estado(cita.pk, formulario.cleaned_data, request.usuario_citas)
        except ValidationError as error:
            errores(formulario, error)
        else:
            messages.success(request, 'Cita actualizada correctamente.')
            return redirect('citas:detalle_cita', cita_id=cita.pk)
    return render(request, 'citas/actualizar_cita.html', {'cita': cita, 'formulario': formulario})


@acceso_citas
@require_http_methods(['GET', 'POST'])
def cancelar_cita(request, cita_id):
    cita = obtener_cita(request, cita_id)
    if not acciones(request, cita)['cancelar']:
        return HttpResponseForbidden('Esta cita no puede cancelarse desde tu cuenta.')
    formulario = FormularioCancelar(request.POST if request.method == 'POST' else None,
                                    initial={'version': cita.version})
    if request.method == 'POST' and formulario.is_valid():
        try:
            servicios.cambiar_estado(cita.pk, {**formulario.cleaned_data, 'estado': 'CANCELADA'},
                                     request.usuario_citas, request.rol_citas == 'PACIENTE')
        except ValidationError as error:
            errores(formulario, error)
        else:
            messages.success(request, 'Cita cancelada. El turno vuelve a estar disponible.')
            return redirect('citas:detalle_cita', cita_id=cita.pk)
    return render(request, 'citas/cancelar_cita.html', {'cita': cita, 'formulario': formulario})


@acceso_citas
@require_http_methods(['GET', 'POST'])
def eliminar_cita(request, cita_id):
    cita = obtener_cita(request, cita_id)
    if not acciones(request, cita)['eliminar']:
        return HttpResponseForbidden('Solo administración puede eliminar citas canceladas sin registros médicos.')
    formulario = FormularioEliminar(request.POST if request.method == 'POST' else None,
                                    initial={'version': cita.version})
    if request.method == 'POST' and formulario.is_valid():
        try:
            servicios.borrar_cita(cita.pk, formulario.cleaned_data['version'])
        except ValidationError as error:
            errores(formulario, error)
        else:
            messages.success(request, 'Cita cancelada eliminada.')
            return redirect('citas:listar_citas')
    return render(request, 'citas/eliminar_cita.html', {'cita': cita, 'formulario': formulario})


@acceso_citas
@require_http_methods(['GET'])
def listar_horarios(request):
    if request.rol_citas == 'PACIENTE':
        return HttpResponseForbidden('Consulta los turnos disponibles en Agendar cita.')
    horarios = []
    for horario in HorarioMedico.objects.all().order_by('dia_semana', 'minuto_inicio'):
        if request.rol_citas == 'DOCTOR' and str(horario.doctor['id']) != str(request.usuario_citas.pk):
            continue
        horarios.append({'horario': horario,
            'inicio': f'{horario.minuto_inicio // 60:02}:{horario.minuto_inicio % 60:02}',
            'fin': f'{horario.minuto_fin // 60:02}:{horario.minuto_fin % 60:02}'})
    return render(request, 'citas/horarios.html', {'horarios': horarios})


@acceso_citas
@require_http_methods(['GET', 'POST'])
def editar_horario(request, horario_id=None):
    if request.rol_citas == 'PACIENTE':
        return HttpResponseForbidden('No puedes gestionar horarios médicos.')
    horario = get_object_or_404(HorarioMedico, pk=horario_id) if horario_id else None
    if horario and request.rol_citas == 'DOCTOR' and str(horario.doctor['id']) != str(request.usuario_citas.pk):
        raise Http404('El horario no existe.')
    inicial = {'doctor_id': str(request.usuario_citas.pk)} if request.rol_citas == 'DOCTOR' else {}
    if horario:
        inicial = {'version': horario.version, 'doctor_id': horario.doctor['id'],
                   'dia_semana': horario.dia_semana, 'activo': horario.activo,
                   'hora_inicio': time(horario.minuto_inicio // 60, horario.minuto_inicio % 60),
                   'hora_fin': time(horario.minuto_fin // 60, horario.minuto_fin % 60),
                   'duracion_consulta_minutos': horario.duracion_consulta_minutos}
    formulario = FormularioHorario(request.POST if request.method == 'POST' else None,
                                     usuario=request.usuario_citas, initial=inicial)
    if request.method == 'POST' and formulario.is_valid():
        try:
            servicios.guardar_horario(formulario.cleaned_data, request.usuario_citas, horario_id)
        except ValidationError as error:
            errores(formulario, error)
        else:
            messages.success(request, 'Horario guardado correctamente.')
            return redirect('citas:listar_horarios')
    return render(request, 'citas/editar_horario.html', {'horario': horario, 'formulario': formulario})
