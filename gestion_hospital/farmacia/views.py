from django.shortcuts import render, redirect, get_object_or_404

from .models import MedicationCatalog


def inicio(request):
    total = MedicationCatalog.objects.count()
    return render(request, 'farmacia/inicio.html', {'total': total})


def consultarMedicamentos(request):
    medicamentos = MedicationCatalog.objects.all()
    return render(request, 'farmacia/medicamentos/lista.html', {'medicamentos': medicamentos})


def consultarMedicamento(request, id):
    medicamento = get_object_or_404(MedicationCatalog, id=id)
    return render(request, 'farmacia/medicamentos/detalle.html', {'medicamento': medicamento})


def crearMedicamento(request):
    if request.method == 'GET':
        return render(request, 'farmacia/medicamentos/formulario.html', {'titulo': 'Crear medicamento'})
    else:
        interacciones = [i.strip() for i in request.POST['interacciones'].split(',') if i.strip()]

        MedicationCatalog.objects.create(nombre_generico=request.POST['nombre_generico'],
                                         nombre_comercial=request.POST['nombre_comercial'],
                                         presentacion=request.POST['presentacion'],
                                         concentracion=request.POST['concentracion'],
                                         lote=request.POST['lote'],
                                         fecha_vencimiento=request.POST['fecha_vencimiento'],
                                         precio_unitario=float(request.POST['precio_unitario']),
                                         stock_disponible=int(request.POST['stock_disponible']),
                                         requiere_receta='requiere_receta' in request.POST,
                                         interacciones=interacciones
                                         )
        return redirect('farmacia:medicamentos')


def actualizarMedicamento(request, id):
    medicamento = get_object_or_404(MedicationCatalog, id=id)

    if request.method == 'GET':
        return render(request, 'farmacia/medicamentos/formulario.html', {'titulo': 'Actualizar medicamento', 'medicamento': medicamento})
    else:
        medicamento.nombre_generico = request.POST['nombre_generico']
        medicamento.nombre_comercial = request.POST['nombre_comercial']
        medicamento.presentacion = request.POST['presentacion']
        medicamento.concentracion = request.POST['concentracion']
        medicamento.lote = request.POST['lote']
        medicamento.fecha_vencimiento = request.POST['fecha_vencimiento']
        medicamento.precio_unitario = float(request.POST['precio_unitario'])
        medicamento.stock_disponible = int(request.POST['stock_disponible'])
        medicamento.requiere_receta = 'requiere_receta' in request.POST
        medicamento.interacciones = [i.strip() for i in request.POST['interacciones'].split(',') if i.strip()]
        medicamento.save()
        return redirect('farmacia:medicamentos')


def eliminarMedicamento(request, id):
    medicamento = get_object_or_404(MedicationCatalog, id=id)

    if request.method == 'GET':
        return render(request, 'farmacia/medicamentos/eliminar.html', {'medicamento': medicamento})
    else:
        medicamento.delete()
        return redirect('farmacia:medicamentos')
