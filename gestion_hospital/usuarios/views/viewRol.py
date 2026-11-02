from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .. import models
from ..acceso import nombres_modulos, modulos_de
from ..auditoria import registrar_log
from ..forms.formRol import PerfilForm
from .viewComunes import paramToId, perfiles_con_modulos


#Listar los perfiles (roles) con sus modulos.
def perfil_lista(request):
    perfiles = perfiles_con_modulos(models.Perfil.objects.all())
    return render(request, "usuarios/perfiles/lista.html", {"perfiles": perfiles})


#Editar el nombre y la descripcion de un perfil (rol).
def perfil_editar(request, perfil_id):
    perfil = get_object_or_404(models.Perfil, id=paramToId(perfil_id))
    if request.method == "POST":
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            registrar_log(request, "Editar rol", "Se editó el rol " + perfil.get_nombre_display(), "EXITOSO")
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("usuarios:perfil_lista")
        registrar_log(request, "Editar rol", "No se pudo editar el rol " + perfil.get_nombre_display(), "FALLIDO")
    else:
        form = PerfilForm(instance=perfil)
    contexto = {
        "form": form,
        "perfil": perfil,
        "modulos": nombres_modulos(modulos_de(perfil.nombre)),
    }
    return render(request, "usuarios/perfiles/form.html", contexto)
