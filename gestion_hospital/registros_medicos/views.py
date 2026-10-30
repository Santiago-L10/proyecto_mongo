from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import RegistroMedico, EstudioLaboratorio
from django.core.exceptions import ObjectDoesNotExist
from .forms import FormularioAutor

# Create your views here.
def inicio(request): # Todas las peticiones reciben como parametro un request que es la peticion como tal
    return HttpResponse("<h1>Hola mundo</h1><br><p>Texto</p>") # Por debajo de HttpResponse lee el mensaje como HTML, se usa 
                                                               # cuando se necesita que se renderice directamente en un html sin 
                                                               # pasar por el template


def goIndex(request, decision):
    data = {'id': 1, 'nombre': 'Santiago', 'esAdministrador': decision}
    data_ciclos = [
        {
            "id":"1020",
            "nombre":"naproxeno",
            "costo": 45000 
        },
        {
            "id":"1020",
            "nombre":"naproxeno",
            "costo": 45000 
        },
        {
            "id":"1020",
            "nombre":"naproxeno",
            "costo": 45000 
        }
    ]
    return render(request, 'lista.html', {"usuario":data, "medicamentos":data_ciclos}) 
    # render espera una plantilla (template) y un diccionario de datos 
    # data = Persona.objects.create(nombre = 'Bryan') -> Esto es una entidad osea un objeto creado
    # return render(request, 'index.html', {'persona': data})


def goParams(request, id):
    return HttpResponse(f"<h1>El id ingresado es {id}</h1>")


def createAutor(request):
    if request.method == 'GET':
        print("Estoy ingresando tipo GET")
        return render(request, 'crear-autor.html', {'formulario': FormularioAutor})
    
    else:
        if 'nombre' in request.POST:
            nombre = request.POST['nombre'] # 
            
        return redirect('inicio')

    


def crear_registro_medico(request):
    nuevo_registro = RegistroMedico.objects.create(
        cita_id="652f1e2b8c9d0e1a2b3c4d5e",
        paciente={
            "id_paciente": "1000381747",
            "nombre_paciente": "Santiago León",
            "tipo_sangre": "O+",
            "alergias_relevantes": ["Penicilina", "Ibuprofeno"]
        },
        doctor={
            "id_doctor": "80998877",
            "nombre_doctor": "Dra. Laura Gomez",
            "especialidad": "Medicina General",
            "registro_medico": "RM-2024-COL"
        },
        queja_principal="Cefalea intensa y fiebre persistente desde hace 3 dias",
        examen_fisico="Paciente orientado en tres esferas, mucosas hidratadas, faringe hiperémica",
        signos_vitales={
            "presion_arterial": "120/80",
            "frecuencia_cardiaca": 82.0,
            "frecuencia_respiratoria": 19.0,
            "temperatura": 38.6,
            "peso_kg": 72.5,
            "estatura_cm": 174.0,
            "bmi": 23.95
        },
        diagnostico=[
            {"codigo": "J00", "descripcion": "Rinofaringitis aguda"},
            {"codigo": "R51", "descripcion": "Cefalea"}
        ],
        tratamiento="Reposo domiciliario 48 horas, hidratacion abundante y acetaminofen 500mg cada 8 horas",
        notas_adicionales="Se solicita hemograma de control si la fiebre persiste"
    )

    return render(request, 'crear_registro.html', {'registro': nuevo_registro})


def crear_estudio_laboratorio(request):
    nuevo_estudio = EstudioLaboratorio(
        registro_medico_id="652f1e2b8c9d0e1a2b3c4d5e",
        paciente={
            "id_paciente": "1000381646",
            "nombre_paciente": "Carlos Alberto Mendoza"
        },
        solicitado_por={
            "id_doctor": "80998877",
            "nombre_doctor": "Dra. Laura Gomez",
            "especialidad": "Medicina General"
        },
        nombre_estudio="Cuadro Hemático Completo",
        categoria="LABORATORIO",
        estatus="SOLICITADO",
        resultado=None,
        interpretacion=None
    )

    nuevo_estudio.save()

    return render(request, 'crear_estudio.html', {'estudio': nuevo_estudio})


def listar_registros_medicos(request):
    listar_registros = RegistroMedico.objects.all()
    return render(request, 'listar_registros.html', {'registro': listar_registros})


def listar_estudios_laboratorio(request):
    listar_laboratorios = EstudioLaboratorio.objects.all()
    return render(request, 'listar_laboratorios.html', {'laboratorio': listar_laboratorios})
    

def actualizar_laboratorio(request):
    try:
        actualizar_lab = EstudioLaboratorio.objects.get(_id = "652f1e2b8c9d0e1a2b3c4d5e")
            
        actualizar_lab.estatus = "COMPLETADO"

        actualizar_lab.resultado = {
            "leucocitos": "6.800 /mm3",
            "hemoglobina": "14.5 g/dL",
            "hematocrito": "43 %",
            "plaquetas": "240.000 /mm3"
        }

        actualizar_lab.interpretacion = "Valores de hemograma dentro de los rangos normales. Sin indicios de infección bacteriana " \
                                        "aguda."

        actualizar_lab.save()

        return render(request, 'actualizar_laboratorios.html', {'laboratorio': actualizar_lab})
    
    except ObjectDoesNotExist:
        actualizar_lab = None

        return HttpResponse("<p>No se encontro el laboratorio para actualizar</p>")


def eliminar_registro_medico(request):
    try:
        eliminar_registro = RegistroMedico.objects.get(_id="652f1e2b8c9d0e1a2b3c4d5e")

        eliminar_registro.delete()

        return HttpResponse("<p>El registro se elimino exitosamente</p>")
    
    except ObjectDoesNotExist:
        eliminar_registro = None

        return HttpResponse("<p>No se encontro el registro para eliminar</p>")

    
    
def eliminar_estudios_cancelados(request):
    try:
        EstudioLaboratorio.objects.filter(estatus="CANCELADO").delete()

        return HttpResponse("<p>Laboratorios CANCELADOS eliminados correctamente</p>")
    except:
        return HttpResponse("<p>No hay laboratorios con estatus CANCELADO</p>")

