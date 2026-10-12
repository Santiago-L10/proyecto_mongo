from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

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

#Devuelve el nombre del rol guardado en el usuario.
def nombre_rol(user):
    rol = user.rol
    if isinstance(rol, dict):
        return rol.get("nombre")
    return getattr(rol, "nombre", None)


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

#Listar los usuarios, con filtro por rol.
def usuario_lista(request):
    rol_sel = request.GET.get("rol", "")

    perfiles = []
    for perfil in models.Perfil.objects.all():
        perfiles.append(perfil)

    etiquetas_rol = {}
    for codigo, etiqueta in models.Rol.Nombre.choices:
        etiquetas_rol[codigo] = etiqueta

    usuarios = []
    for user in models.User.objects.all().order_by("-fecha_creacion"):
        rol_nombre = nombre_rol(user)
        if rol_sel != "" and rol_nombre != rol_sel:
            continue
        usuarios.append(
            {
                "user": user,
                "rol_nombre": rol_nombre,
                "rol_display": etiquetas_rol.get(rol_nombre, rol_nombre),
            }
        )

    contexto = {
        "perfiles": perfiles,
        "rol_sel": rol_sel,
        "usuarios": usuarios,
    }
    return render(request, "usuarios/usuarios/lista.html", contexto)

#Eliminar un usuario (solo por POST).
def usuario_eliminar(request, usuario_id):
    user = get_object_or_404(models.User, id=paramToId(usuario_id))
    if request.method == "POST":
        user.delete()
        messages.success(request, "Usuario eliminado correctamente.")
    rol_sel = request.POST.get("rol", "")
    url = reverse("usuarios:usuario_lista")
    if rol_sel:
        url = url + "?rol=" + rol_sel
    return redirect(url)
