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
            cd = form.cleaned_data

            # 1. Cálculo de BMI (float)
            peso = float(cd['peso_kg'])
            estatura = float(cd['estatura_cm'])
            bmi = round(peso / ((estatura / 100) ** 2), 2) if estatura > 0 else 0.0

            # 2. Procesar lista de alergias (array de strings en Mongo)
            alergias_raw = cd.get('alergias_relevantes') or ''
            lista_alergias = [a.strip() for a in alergias_raw.split(',') if a.strip()]

            # 3. Armar objetos embebidos (Snapshots NoSQL) cumpliendo el $jsonSchema
            paciente_doc = {
                "id_paciente": str(cd['id_paciente']),
                "nombre_paciente": str(cd['nombre_paciente']),
                "tipo_sangre": str(cd['tipo_sangre']),
                "alergias_relevantes": lista_alergias
            }

            doctor_doc = {
                "id_doctor": str(cd['id_doctor']),
                "nombre_doctor": str(cd['nombre_doctor']),
                "especialidad": str(cd['especialidad']),
                "registro_medico": str(cd.get('registro_medico') or '')
            }

            signos_vitales_doc = {
                "presion_arterial": str(cd['presion_arterial']),
                "frecuencia_cardiaca": float(cd['frecuencia_cardiaca']),
                "frecuencia_respiratoria": float(cd['frecuencia_respiratoria']),
                "temperatura": float(cd['temperatura']),
                "peso_kg": peso,
                "estatura_cm": estatura,
                "bmi": bmi
            }

            diagnostico_doc = [
                {
                    "codigo": str(cd['codigo_diagnostico']),
                    "descripcion": str(cd['descripcion_diagnostico'])
                }
            ]

            # 4. Guardar con el ORM de Django (Estilo guía PDF: Creación Posterior)
            nuevo_registro = RegistroMedico(
                fecha=timezone.now(),
                cita_id=str(cd.get('cita_id') or ''),
                paciente=paciente_doc,
                doctor=doctor_doc,
                queja_principal=str(cd['queja_principal']),
                examen_fisico=str(cd['examen_fisico']),
                signos_vitales=signos_vitales_doc,
                diagnostico=diagnostico_doc,
                tratamiento=str(cd['tratamiento']),
                notas_adicionales=str(cd.get('notas_adicionales') or '')
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
            data = form.cleaned_data

            nuevo_estudio = EstudioLaboratorio(
                registro_medico_id=data.get('registro_medico_id') or None,
                paciente={
                    "id_paciente": str(data['id_paciente']),
                    "nombre_paciente": str(data['nombre_paciente'])
                },
                solicitado_por={
                    "id_doctor": str(data['id_doctor']),
                    "nombre_doctor": str(data['nombre_doctor']),
                    "especialidad": str(data.get('especialidad') or '')
                },
                nombre_estudio=str(data['nombre_estudio']),
                categoria=str(data['categoria']),
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
                # .strip() quita los espacios en blanco. 
                # Si alguno de los dos está vacío, la condición es False y lo salta por completo:
                resultado_dinamico[nombre.strip()] = valor.strip()

        if hallazgos:
            resultado_dinamico["Hallazgos"] = hallazgos

        actualizar_lab.resultado = resultado_dinamico
        actualizar_lab.interpretacion = request.POST.get('interpretacion')
        actualizar_lab.save()

        return redirect('registros_medicos:listar_estudios_laboratorio')

    resultado_actual = actualizar_lab.resultado if isinstance(actualizar_lab.resultado, dict) else {}
    hallazgos_previos = resultado_actual.get("Hallazgos", "")
    
    # Lista de tuplas (clave, valor) excluyendo "Hallazgos"
    parametros_previos = [
        (k, v) for k, v in resultado_actual.items() if k != "Hallazgos"
    ]

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

    resultado_actual = lab.resultado if isinstance(lab.resultado, dict) else {}
    hallazgos = resultado_actual.get("Hallazgos", "")
    parametros = [
        (k, v) for k, v in resultado_actual.items() if k != "Hallazgos"
    ]

    context = {
        'laboratorio': lab,
        'parametros': parametros,
        'hallazgos': hallazgos,
    }
    return render(request, 'detalle_laboratorio.html', context)    
    

def eliminar_registro_medico(request, id):
    try:
        # 1. Convertir el string de la URL a ObjectId de MongoDB
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

