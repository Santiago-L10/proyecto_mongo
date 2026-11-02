from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import RegistroMedico, EstudioLaboratorio
from django.core.exceptions import ObjectDoesNotExist
from .forms.registros_forms import RegistroMedicoForm
from .forms.laboratorio_forms import EstudioLaboratorioForm
from django.utils import timezone
from bson import ObjectId


def crear_registro_medico(request):
    if request.method == 'POST':
        form = RegistroMedicoForm(request.POST)

        if form.is_valid():
            datos_limpios = form.cleaned_data

            peso = float(datos_limpios['peso_kg'])

            estatura = float(datos_limpios['estatura_cm'])
            
            if estatura > 0:
                bmi = round(peso / ((estatura / 100) ** 2), 2)     
            else:
                bmi = 0.0

            alergias = datos_limpios.get('alergias_relevantes') or ''

            lista_alergias = []

            for alergia in alergias.split(','):
                alergia_limpia = alergia.strip()

                if alergia_limpia: 
                    lista_alergias.append(alergia_limpia)

            paciente_doc = {
                "id_paciente": str(datos_limpios['id_paciente']),
                "nombre_paciente": str(datos_limpios['nombre_paciente']),
                "tipo_sangre": str(datos_limpios['tipo_sangre']),
                "alergias_relevantes": lista_alergias
            }

            doctor_doc = {
                "id_doctor": str(datos_limpios['id_doctor']),
                "nombre_doctor": str(datos_limpios['nombre_doctor']),
                "especialidad": str(datos_limpios['especialidad']),
                "registro_medico": str(datos_limpios.get('registro_medico') or '')
            }

            signos_vitales_doc = {
                "presion_arterial": str(datos_limpios['presion_arterial']),
                "frecuencia_cardiaca": float(datos_limpios['frecuencia_cardiaca']),
                "frecuencia_respiratoria": float(datos_limpios['frecuencia_respiratoria']),
                "temperatura": float(datos_limpios['temperatura']),
                "peso_kg": peso,
                "estatura_cm": estatura,
                "bmi": bmi
            }

            diagnostico_doc = [
                {
                    "codigo": str(datos_limpios['codigo_diagnostico']),
                    "descripcion": str(datos_limpios['descripcion_diagnostico'])
                }
            ]

            nuevo_registro = RegistroMedico(
                fecha=timezone.now(),
                cita_id=str(datos_limpios.get('cita_id') or ''),
                paciente=paciente_doc,
                doctor=doctor_doc,
                queja_principal=str(datos_limpios['queja_principal']),
                examen_fisico=str(datos_limpios['examen_fisico']),
                signos_vitales=signos_vitales_doc,
                diagnostico=diagnostico_doc,
                tratamiento=str(datos_limpios['tratamiento']),
                notas_adicionales=str(datos_limpios.get('notas_adicionales') or '')
            )

            nuevo_registro.save()

            return redirect('registros_medicos:listar_registros_medicos')
    else:
        form = RegistroMedicoForm()

    return render(request, 'crear_registro.html', {'form': form})


def crear_estudio_laboratorio(request):
    if request.method == 'POST':
        form = EstudioLaboratorioForm(request.POST)

        if form.is_valid():
            datos_limpios = form.cleaned_data

            nuevo_estudio = EstudioLaboratorio(
                registro_medico_id=datos_limpios.get('registro_medico_id') or None,
                paciente={
                    "id_paciente": str(datos_limpios['id_paciente']),
                    "nombre_paciente": str(datos_limpios['nombre_paciente'])
                },
                solicitado_por={
                    "id_doctor": str(datos_limpios['id_doctor']),
                    "nombre_doctor": str(datos_limpios['nombre_doctor']),
                    "especialidad": str(datos_limpios.get('especialidad') or '')
                },
                nombre_estudio=str(datos_limpios['nombre_estudio']),
                categoria=str(datos_limpios['categoria']),
                estatus="SOLICITADO",
                solicitud_examen=timezone.now(),
                reporte_resultado=None,
                resultado={},
                interpretacion=None
            )

            nuevo_estudio.save()
            
            return redirect('registros_medicos:listar_estudios_laboratorio')
    else:
        form = EstudioLaboratorioForm()

    return render(request, 'crear_estudio.html', {'form': form})


def listar_registros_medicos(request):
    listar_registros = RegistroMedico.objects.all().order_by('-fecha')
    return render(request, 'listar_registros.html', {'registros': listar_registros})


def listar_estudios_laboratorio(request):
    listar_laboratorios = EstudioLaboratorio.objects.all().order_by('-solicitud_examen')
    return render(request, 'listar_laboratorios.html', {'laboratorios': listar_laboratorios})
    

def actualizar_laboratorio(request, id):
    try:
        obj_id = ObjectId(id)
        actualizar_lab = EstudioLaboratorio.objects.get(_id=obj_id)

    except (ObjectDoesNotExist, Exception):
            return HttpResponse("<p>No se encontró el laboratorio para actualizar</p>", status=404)

    if request.method == 'POST':
        actualizar_lab.estatus = request.POST.get('estatus', 'COMPLETADO')

        actualizar_lab.reporte_resultado = timezone.now()

        nombres = request.POST.getlist('parametro_nombre')

        valores = request.POST.getlist('parametro_valor')

        hallazgos = request.POST.get('hallazgos', '').strip()

        resultado_dinamico = {}

        for nombre, valor in zip(nombres, valores):
            if nombre.strip() and valor.strip():
                resultado_dinamico[nombre.strip()] = valor.strip()

        if hallazgos:
            resultado_dinamico["Hallazgos"] = hallazgos

        actualizar_lab.resultado = resultado_dinamico

        actualizar_lab.interpretacion = request.POST.get('interpretacion')

        actualizar_lab.save()

        return redirect('registros_medicos:listar_estudios_laboratorio')

    if isinstance(actualizar_lab.resultado, dict):
        resultado_actual = actualizar_lab.resultado
    else:
        resultado_actual = {}

    hallazgos_previos = resultado_actual.get("Hallazgos", "")
    
    parametros_previos = []

    for key, value in resultado_actual.items():
        if key != "Hallazgos":
            parametros_previos.append((key, value))

    context = {
        'laboratorio': actualizar_lab,
        'parametros_previos': parametros_previos,
        'hallazgos_previos': hallazgos_previos,
    }

    return render(request, 'actualizar_laboratorios.html', context)


def detalle_registro_medico(request, id):
    try:
        obj_id = ObjectId(str(id).strip())

        registro = RegistroMedico.objects.get(_id=obj_id)

    except (ObjectDoesNotExist, Exception):
        return HttpResponse("<p>No se encontró el registro médico solicitado</p>", status=404)

    return render(request, 'detalle_registro.html', {'registro': registro})


def detalle_laboratorio(request, id):
    try:
        obj_id = ObjectId(str(id).strip())

        lab = EstudioLaboratorio.objects.get(_id=obj_id)

    except (ObjectDoesNotExist, Exception):
        return HttpResponse("<p>No se encontró el estudio de laboratorio</p>", status=404)

    if isinstance(lab.resultado, dict):
        resultado_actual = lab.resultado 
    else:
        resultado_actual = {}

    hallazgos = resultado_actual.get("Hallazgos", "")

    parametros = []

    for key, value in resultado_actual.items():
        if key != "Hallazgos":
            parametros.append((key, value))

    context = {
        'laboratorio': lab,
        'parametros': parametros,
        'hallazgos': hallazgos,
    }

    return render(request, 'detalle_laboratorio.html', context)    
    

def eliminar_registro_medico(request, id):
    try:
        obj_id = ObjectId(id) 

        eliminar_registro = RegistroMedico.objects.get(_id=obj_id)

        eliminar_registro.delete()

        return redirect('registros_medicos:listar_registros_medicos')

    except (ObjectDoesNotExist, Exception):
        return HttpResponse("<p>No se encontró el registro para eliminar</p>", status=404)

    
    
def eliminar_estudios_cancelados(request):
    try:
        EstudioLaboratorio.objects.filter(estatus="CANCELADO").delete()

        return redirect('registros_medicos:listar_estudios_laboratorio')
    
    except Exception:
        return HttpResponse("<p>Error al procesar la eliminación masiva</p>", status=500)

