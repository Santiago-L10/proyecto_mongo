from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from bson import ObjectId
from bson.errors import InvalidId

from . import models
from .acceso import MODULOS_POR_ROL, nombres_modulos, modulos_de
from .forms import PerfilForm

#Convierte el id recibido por la URL al tipo de dato que usa Mongo.
def paramToId(valor):
    try:
        return ObjectId(valor)
    except (InvalidId, TypeError):
        return valor

#Mostrar el nombre de los modulos por perfil
def perfiles_con_modulos(perfiles):
    resultado = []
    for perfil in perfiles:
        resultado.append(
            {
                "perfil": perfil,
                "modulos": nombres_modulos(modulos_de(perfil.nombre)),
            }
        )
    return resultado


# --------------------------------------------------------------------------
# Panel
# --------------------------------------------------------------------------

def panel_home(request):
    contexto = {
        "total_perfiles": models.Perfil.objects.count(),
        "modulos_por_rol": MODULOS_POR_ROL,
    }
    return render(request, "usuarios/panel.html", contexto)


# --------------------------------------------------------------------------
# Perfiles / Roles
# --------------------------------------------------------------------------

def perfil_lista(request):
    perfiles = perfiles_con_modulos(models.Perfil.objects.all())
    return render(request, "usuarios/perfiles/lista.html", {"perfiles": perfiles})


def perfil_editar(request, perfil_id):
    perfil = get_object_or_404(models.Perfil, id=paramToId(perfil_id))
    if request.method == "POST":
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("usuarios:perfil_lista")
    else:
        form = PerfilForm(instance=perfil)
    contexto = {
        "form": form,
        "perfil": perfil,
        "modulos": nombres_modulos(modulos_de(perfil.nombre)),
    }
    return render(request, "usuarios/perfiles/form.html", contexto)
