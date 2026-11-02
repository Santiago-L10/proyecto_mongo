from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from bson import ObjectId
from bson.errors import InvalidId

from . import models
from .acceso import MODULOS_POR_ROL, SECCION_POR_ROL, nombres_modulos, modulos_de
from .forms import PerfilForm, SeleccionRolForm, UsuarioForm

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
        "total_usuarios": models.User.objects.count(),
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


# --------------------------------------------------------------------------
# Usuarios
# --------------------------------------------------------------------------

#Paso 1: elegir el rol del nuevo usuario.
def usuario_crear(request):
    if request.method == "POST":
        form = SeleccionRolForm(request.POST)
        if form.is_valid():
            return redirect(
                "usuarios:usuario_crear_datos",
                rol_nombre=form.cleaned_data["rol"],
            )
    else:
        form = SeleccionRolForm()
    return render(request, "usuarios/usuarios/crear_rol.html", {"form": form})

#Paso 2: llenar los datos del usuario según el rol elegido.
def usuario_crear_datos(request, rol_nombre):
    perfiles = {}
    for perfil in models.Perfil.objects.all():
        if perfil.activo:
            perfiles[perfil.nombre] = perfil
    if rol_nombre not in perfiles:
        messages.error(request, "El rol seleccionado no es válido.")
        return redirect("usuarios:usuario_crear")

    if request.method == "POST":
        form = UsuarioForm(request.POST, rol_nombre=rol_nombre)
        if form.is_valid():
            form.guardar()
            messages.success(request, "Usuario registrado correctamente.")
            return redirect("usuarios:panel_home")
    else:
        form = UsuarioForm(rol_nombre=rol_nombre)

    contexto = {
        "form": form,
        "rol_nombre": rol_nombre,
        "rol_display": perfiles[rol_nombre].get_nombre_display(),
        "seccion": SECCION_POR_ROL.get(rol_nombre),
    }
    return render(request, "usuarios/usuarios/crear.html", contexto)
