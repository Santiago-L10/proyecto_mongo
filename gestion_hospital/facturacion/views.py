from django.shortcuts import render, redirect

from .models import Polizas, Facturas

# Create your views here.
def inicio(request):
    return render(request, 'facturacion/inicio.html')



def consultarPolizas(request):
    polizas = Polizas.objects.all()
    return render(request, 'facturacion/polizas/lista.html', {'polizas': polizas})


def crearPoliza(request):
    if request.method == 'GET':
        return render(request, 'facturacion/polizas/formulario.html', {'titulo': 'Crear póliza'})
    else:
        Polizas.objects.create(codigo_poliza=request.POST['codigo_poliza'],
                               titular={'id': request.POST['id'],
                                        'id_user': request.POST['id_user'],
                                        'nombre_completo': request.POST['nombre_completo']},
                               aseguradora=request.POST['aseguradora'],
                               tipo_servicio=request.POST['tipo_servicio'],
                               porcentaje_cobertura_general=request.POST['porcentaje_cobertura_general'],
                               fecha_inicio=request.POST['fecha_inicio'],
                               fecha_fin=request.POST['fecha_fin'],
                               coberturas={}
                               )
        return redirect('facturacion:polizas')


def actualizarPoliza(request, id):
    poliza = Polizas.objects.get(id=id)

    if request.method == 'GET':
        return render(request, 'facturacion/polizas/formulario.html', {'titulo': 'Actualizar póliza', 'poliza': poliza})
    else:
        poliza.codigo_poliza = request.POST['codigo_poliza']
        poliza.aseguradora = request.POST['aseguradora']
        poliza.tipo_servicio = request.POST['tipo_servicio']
        poliza.porcentaje_cobertura_general = request.POST['porcentaje_cobertura_general']
        poliza.fecha_inicio = request.POST['fecha_inicio']
        poliza.fecha_fin = request.POST['fecha_fin']
        poliza.save()
        return redirect('facturacion:polizas')


def eliminarPoliza(request, id):
    poliza = Polizas.objects.get(id=id)

    if request.method == 'GET':
        return render(request, 'facturacion/polizas/eliminar.html', {'poliza': poliza})
    else:
        poliza.delete()
        return redirect('facturacion:polizas')



def consultarTitular(request, id):
    poliza = Polizas.objects.get(id=id)
    return render(request, 'facturacion/titular/detalle.html', {'poliza': poliza})


def actualizarTitular(request, id):
    poliza = Polizas.objects.get(id=id)

    if request.method == 'GET':
        return render(request, 'facturacion/titular/formulario.html', {'poliza': poliza})
    else:
        poliza.titular = {'id': request.POST['id'],
                          'id_user': request.POST['id_user'],
                          'nombre_completo': request.POST['nombre_completo']}
        poliza.save()
        return redirect('facturacion:titular', id=id)



def consultarFacturas(request):
    facturas = Facturas.objects.all()
    return render(request, 'facturacion/facturas/lista.html', {'facturas': facturas})


def crearFactura(request):
    if request.method == 'GET':
        return render(request, 'facturacion/facturas/formulario.html', {'titulo': 'Crear factura'})
    else:
        subtotal = int(request.POST['cantidad']) * float(request.POST['precio_unitario'])

        Facturas.objects.create(numero_factura=request.POST['numero_factura'],
                                fecha_emision=request.POST['fecha_emision'],
                                estado=request.POST['estado'],
                                metodo_pago=request.POST['metodo_pago'],
                                paciente={'id': request.POST['id'],
                                          'id_user': request.POST['id_user'],
                                          'nombre_completo': request.POST['nombre_completo']},
                                items=[{'concepto': request.POST['concepto'],
                                        'tipo': request.POST['tipo'],
                                        'referencia_id': request.POST['referencia_id'],
                                        'cantidad': request.POST['cantidad'],
                                        'precio_unitario': request.POST['precio_unitario'],
                                        'subtotal': subtotal}],
                                total_bruto=request.POST['total_bruto'],
                                iva=request.POST['iva'],
                                valor_neto_pagar=request.POST['valor_neto_pagar']
                                )
        return redirect('facturacion:facturas')


def actualizarFactura(request, id):
    factura = Facturas.objects.get(id=id)

    if request.method == 'GET':
        return render(request, 'facturacion/facturas/formulario.html', {'titulo': 'Actualizar factura', 'factura': factura})
    else:
        factura.numero_factura = request.POST['numero_factura']
        factura.fecha_emision = request.POST['fecha_emision']
        factura.estado = request.POST['estado']
        factura.metodo_pago = request.POST['metodo_pago']
        factura.total_bruto = request.POST['total_bruto']
        factura.iva = request.POST['iva']
        factura.valor_neto_pagar = request.POST['valor_neto_pagar']
        factura.save()
        return redirect('facturacion:facturas')


def eliminarFactura(request, id):
    factura = Facturas.objects.get(id=id)

    if request.method == 'GET':
        return render(request, 'facturacion/facturas/eliminar.html', {'factura': factura})
    else:
        factura.delete()
        return redirect('facturacion:facturas')



def consultarPaciente(request, id):
    factura = Facturas.objects.get(id=id)
    return render(request, 'facturacion/paciente/detalle.html', {'factura': factura})


def actualizarPaciente(request, id):
    factura = Facturas.objects.get(id=id)

    if request.method == 'GET':
        return render(request, 'facturacion/paciente/formulario.html', {'factura': factura})
    else:
        factura.paciente = {'id': request.POST['id'],
                            'id_user': request.POST['id_user'],
                            'nombre_completo': request.POST['nombre_completo']}
        factura.save()
        return redirect('facturacion:paciente', id=id)


def consultarItems(request, id):
    factura = Facturas.objects.get(id=id)
    return render(request, 'facturacion/items/lista.html', {'factura': factura})


def crearItem(request, id):
    factura = Facturas.objects.get(id=id)

    if request.method == 'GET':
        return render(request, 'facturacion/items/formulario.html', {'titulo': 'Agregar concepto al detalle', 'factura': factura})
    else:
        subtotal = int(request.POST['cantidad']) * float(request.POST['precio_unitario'])

        factura.items.append({'concepto': request.POST['concepto'],
                              'tipo': request.POST['tipo'],
                              'referencia_id': request.POST['referencia_id'],
                              'cantidad': request.POST['cantidad'],
                              'precio_unitario': request.POST['precio_unitario'],
                              'subtotal': subtotal})
        factura.save()
        return redirect('facturacion:items', id=id)


def actualizarItem(request, id, posicion):
    factura = Facturas.objects.get(id=id)

    if request.method == 'GET':
        item = factura.items[posicion]
        return render(request, 'facturacion/items/formulario.html', {'titulo': 'Actualizar concepto del detalle', 'factura': factura, 'item': item})
    else:
        subtotal = int(request.POST['cantidad']) * float(request.POST['precio_unitario'])

        factura.items[posicion] = {'concepto': request.POST['concepto'],
                                   'tipo': request.POST['tipo'],
                                   'referencia_id': request.POST['referencia_id'],
                                   'cantidad': request.POST['cantidad'],
                                   'precio_unitario': request.POST['precio_unitario'],
                                   'subtotal': subtotal}
        factura.save()
        return redirect('facturacion:items', id=id)


def eliminarItem(request, id, posicion):
    factura = Facturas.objects.get(id=id)

    if request.method == 'GET':
        item = factura.items[posicion]
        cantidad_items = len(factura.items)
        return render(request, 'facturacion/items/eliminar.html', {'factura': factura, 'item': item, 'cantidad_items': cantidad_items})
    else:
        if len(factura.items) > 1:
            factura.items.pop(posicion)
            factura.save()
        return redirect('facturacion:items', id=id)


def consultarCobertura(request, id):
    factura = Facturas.objects.get(id=id)
    return render(request, 'facturacion/cobertura/detalle.html', {'factura': factura})


def crearCobertura(request, id):
    factura = Facturas.objects.get(id=id)

    if request.method == 'GET':
        return render(request, 'facturacion/cobertura/formulario.html', {'titulo': 'Agregar cobertura', 'factura': factura})
    else:
        factura.cobertura_seguro = {'codigo_poliza': request.POST['codigo_poliza'],
                                    'aseguradora': request.POST['aseguradora'],
                                    'monto_cubierto': request.POST['monto_cubierto']}
        factura.save()
        return redirect('facturacion:cobertura', id=id)


def actualizarCobertura(request, id):
    factura = Facturas.objects.get(id=id)

    if request.method == 'GET':
        return render(request, 'facturacion/cobertura/formulario.html', {'titulo': 'Actualizar cobertura', 'factura': factura, 'cobertura': factura.cobertura_seguro})
    else:
        factura.cobertura_seguro = {'codigo_poliza': request.POST['codigo_poliza'],
                                    'aseguradora': request.POST['aseguradora'],
                                    'monto_cubierto': request.POST['monto_cubierto']}
        factura.save()
        return redirect('facturacion:cobertura', id=id)


def eliminarCobertura(request, id):
    factura = Facturas.objects.get(id=id)

    if request.method == 'GET':
        return render(request, 'facturacion/cobertura/eliminar.html', {'factura': factura})
    else:
        factura.cobertura_seguro = None
        factura.save()
        return redirect('facturacion:cobertura', id=id)
