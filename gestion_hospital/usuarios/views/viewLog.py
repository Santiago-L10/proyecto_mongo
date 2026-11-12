from django.shortcuts import render

from .. import models


def log_lista(request):
    logs = models.Log.objects.all().order_by("-date")
    return render(request, "usuarios/logs/lista.html", {"logs": logs})
