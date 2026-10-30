
from datetime import timedelta
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from .models import Cita, DoctorSnapshot, PacienteSnapshot
from .forms import FormularioCita, FormularioEditarCita


def listar_citas(request):
    citas = Cita.objects.values().order_by('-fecha_inicio')
    total = Cita.objects.count()

    contexto = {
        'titulo': 'Listado General de Citas Medicas',
        'citas': list(citas),
        'total': total,
        'filtro_activo': 'TODAS'
    }
    return render(request, 'listar_citas.html', contexto)


def detalle_cita(request, cita_id):
    cita = Cita.objects.filter(id=cita_id).values().first()

    contexto = {
        'cita': cita,
        'cita_id': cita_id
    }
    return render(request, 'detalle_cita.html', contexto)


def filtrar_citas(request, estado_filtro):
    estado_normalizado = estado_filtro.upper()
    citas = Cita.objects.filter(estado=estado_normalizado).values().order_by('-fecha_inicio')
    total = citas.count()

    contexto = {
        'titulo': f'Citas en estado: {estado_normalizado}',
        'citas': list(citas),
        'total': total,
        'filtro_activo': estado_normalizado
    }
    return render(request, 'filtrar_citas.html', contexto)


def agendar_cita(request):
    if request.method == 'POST':
        formulario = FormularioCita(request.POST)

        if formulario.is_valid():
            datos = formulario.cleaned_data

            doc = DoctorSnapshot(
                id=datos['doctor_id'],
                nombre_completo=datos['doctor_nombre'],
                especialidad=datos['doctor_especialidad']
            )

            pac = PacienteSnapshot(
                id=datos['paciente_id'],
                id_user=datos['paciente_documento'],
                nombre_completo=datos['paciente_nombre'],
                telefono=datos['paciente_telefono']
            )

            inicio = datos['fecha_inicio']
            duracion = datos['duracion_minutos']
            fin = inicio + timedelta(minutes=duracion)

            Cita.objects.create(
                paciente=pac,
                doctor=doc,
                fecha_inicio=inicio,
                fecha_fin=fin,
                duracion_minutos=duracion,
                estado='PROGRAMADA',
                motivo_consulta=datos['motivo_consulta']
            )
            return redirect('citas:listar_citas')
    else:
        formulario = FormularioCita()

    return render(request, 'agendar_cita.html', {'formulario': formulario})


def actualizar_cita(request, cita_id):
    try:
        cita = Cita.objects.get(id=cita_id)
    except ObjectDoesNotExist:
        return redirect('citas:listar_citas')

    if request.method == 'POST':
        formulario = FormularioEditarCita(request.POST)

        if formulario.is_valid():
            datos = formulario.cleaned_data
            cita.estado = datos['estado']
            cita.motivo_consulta = datos['motivo_consulta']
            cita.motivo_cancelacion = datos['motivo_cancelacion']
            cita.save()

            return redirect('citas:detalle_cita', cita_id=cita.id)
    else:
        datos_iniciales = {
            'estado': cita.estado,
            'motivo_consulta': cita.motivo_consulta,
            'motivo_cancelacion': cita.motivo_cancelacion,
        }
        formulario = FormularioEditarCita(initial=datos_iniciales)

    contexto = {
        'formulario': formulario,
        'cita': cita
    }
    return render(request, 'actualizar_cita.html', contexto)


def eliminar_cita(request, cita_id):
    try:
        cita = Cita.objects.get(id=cita_id)
    except ObjectDoesNotExist:
        return redirect('citas:listar_citas')

    if request.method == 'POST':
        cita.delete()
        return redirect('citas:listar_citas')

    return render(request, 'eliminar_cita.html', {'cita': cita})
