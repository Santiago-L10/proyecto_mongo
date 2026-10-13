from django.shortcuts import redirect, render

from ..forms.formLogin import LoginForm
from .viewComunes import nombre_rol


#Devuelve la ruta a la que se redirige según el rol del usuario.
def ruta_por_rol(rol):
    if rol == "ADMIN":
        return "/panel/"
    elif rol == "DOCTOR":
        # aquí va el path del módulo del doctor (registros médicos / citas)
        return "/doctor/"
    elif rol == "PACIENTE":
        # aquí va el path del módulo del paciente (citas)
        return "/paciente/"
    elif rol == "FARMACEUTICO":
        # aquí va el path del módulo de farmacia
        return "/farmacia/"
    elif rol == "RECEPCIONISTA":
        # aquí va el path del módulo de recepción (citas / facturación)
        return "/recepcion/"
    return "/panel/"


#Iniciar sesión con correo y contraseña (la sesión de Django es el token).
def login_sesion(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            usuario = form.usuario
            rol = nombre_rol(usuario)
            request.session["user_id"] = str(usuario.id)
            request.session["rol"] = rol
            request.session["nombre"] = usuario.first_name + " " + usuario.last_name
            return redirect(ruta_por_rol(rol))
    else:
        form = LoginForm()
    return render(request, "usuarios/login.html", {"form": form})


#Cerrar sesión (borra la sesión actual).
def logout_sesion(request):
    request.session.flush()
    return redirect("usuarios:login_sesion")
