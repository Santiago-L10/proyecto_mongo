from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from ..forms.formLogin import LoginForm
from .viewComunes import nombre_rol


def ruta_por_rol(rol):
    if rol == "ADMIN":
        return "/panel/"
    elif rol == "DOCTOR":
        return "/registros_medicos/"
    elif rol == "PACIENTE":
        return "/citas/"
    elif rol == "FARMACEUTICO":
        return "/farmacia/homeFarm/"
    elif rol == "ADMINISTRATIVO":
        return "/facturacion/homeFact/"
    return "/panel/"


def login_sesion(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            usuario = form.usuario
            rol = nombre_rol(usuario)
            request.session.cycle_key()
            request.session["user_id"] = str(usuario.id)
            request.session["email"] = usuario.email
            request.session["rol"] = rol
            request.session["nombre"] = usuario.first_name + " " + usuario.last_name
            destino = request.GET.get('next', '')
            if destino and url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(destino)
            return redirect(ruta_por_rol(rol))
    else:
        form = LoginForm()
    return render(request, "usuarios/login.html", {"form": form})


def logout_sesion(request):
    request.session.flush()
    return redirect("usuarios:login_sesion")
