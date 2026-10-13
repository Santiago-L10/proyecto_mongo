from django.shortcuts import render

from .. import models
from ..acceso import MODULOS_POR_ROL


#Mostrar el panel principal del administrador.
def panel_home(request):
    contexto = {
        "total_perfiles": models.Perfil.objects.count(),
        "total_usuarios": models.User.objects.count(),
        "total_logs": models.Log.objects.count(),
        "modulos_por_rol": MODULOS_POR_ROL,
    }
    return render(request, "usuarios/panel.html", contexto)
