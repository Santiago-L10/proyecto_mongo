from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .. import models
from ..acceso import SECCION_POR_ROL
from ..auditoria import registrar_log
from ..forms.formRol import SeleccionRolForm
from ..forms.formUsuario import UsuarioEditarForm, UsuarioForm
from .viewComunes import nombre_rol, paramToId


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
        registrar_log(request, "Registrar usuario", "Rol no válido: " + rol_nombre, "FALLIDO")
        messages.error(request, "El rol seleccionado no es válido.")
        return redirect("usuarios:usuario_crear")

    if request.method == "POST":
        form = UsuarioForm(request.POST, rol_nombre=rol_nombre)
        if form.is_valid():
            form.guardar()
            registrar_log(request, "Registrar usuario", "Se registró el usuario " + form.cleaned_data["email"] + " con rol " + perfiles[rol_nombre].get_nombre_display(), "EXITOSO")
            messages.success(request, "Usuario registrado correctamente.")
            return redirect("usuarios:panel_home")
        registrar_log(request, "Registrar usuario", "No se pudo registrar el usuario " + str(request.POST.get("email")) + " con rol " + perfiles[rol_nombre].get_nombre_display(), "FALLIDO")
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


#Actualizar los datos básicos de un usuario (rol y fecha de creación no se tocan).
def usuario_editar(request, usuario_id):
    user = get_object_or_404(models.User, id=paramToId(usuario_id))
    if request.method == "POST":
        form = UsuarioEditarForm(request.POST, usuario=user)
        if form.is_valid():
            form.guardar()
            messages.success(request, "Usuario actualizado correctamente.")
        else:
            messages.error(request, "No se pudo actualizar. Revisa el correo (puede que ya exista) y los campos obligatorios.")
    rol_sel = request.POST.get("rol", "")
    url = reverse("usuarios:usuario_lista")
    if rol_sel:
        url = url + "?rol=" + rol_sel
    return redirect(url)


#Eliminar un usuario (solo por POST).
def usuario_eliminar(request, usuario_id):
    user = get_object_or_404(models.User, id=paramToId(usuario_id))
    if request.method == "POST":
        correo = user.email
        user.delete()
        registrar_log(request, "Eliminar usuario", "Se eliminó el usuario " + correo, "EXITOSO")
        messages.success(request, "Usuario eliminado correctamente.")
    rol_sel = request.POST.get("rol", "")
    url = reverse("usuarios:usuario_lista")
    if rol_sel:
        url = url + "?rol=" + rol_sel
    return redirect(url)
