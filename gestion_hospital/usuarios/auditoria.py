from django.utils import timezone

from . import models


#Registra una acción del usuario logueado en la colección de logs.
def registrar_log(request, action, details, status):
    log = models.Log(
        user_id=request.session.get("email"),
        action=action,
        date=timezone.now(),
        details=details,
        status=status,
    )
    log.save()
    return log
