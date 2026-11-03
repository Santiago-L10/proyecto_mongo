from functools import wraps
from urllib.parse import urlencode

from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from usuarios.models import User

ZONA = 'America/Bogota'
GESTORES = ('ADMIN', 'RECEPCIONISTA')


def acceso_citas(vista):
    @wraps(vista)
    def protegida(request, *args, **kwargs):
        try:
            clave = User._meta.pk.to_python(request.session.get('user_id'))
        except (ValidationError, ValueError, TypeError):
            clave = None
        usuario = User.objects.filter(pk=clave).first() if clave is not None else None
        if usuario is None or usuario.activo != 'SI':
            return redirect(reverse('usuarios:login_sesion') + '?' + urlencode({'next': request.get_full_path()}))
        rol = (usuario.rol or {}).get('nombre')
        if rol not in GESTORES + ('DOCTOR', 'PACIENTE'):
            return HttpResponseForbidden('Tu rol no tiene acceso al módulo de citas.')
        request.usuario_citas = usuario
        request.rol_citas = rol
        request.gestiona_citas = rol in GESTORES
        with timezone.override(ZONA):
            return vista(request, *args, **kwargs)
    return protegida


def puede_ver(request, cita):
    if request.gestiona_citas:
        return True
    parte = cita.doctor if request.rol_citas == 'DOCTOR' else cita.paciente
    return str((parte or {}).get('id')) == str(request.usuario_citas.pk)


def obtener_cita(request, cita_id):
    from .models import Cita
    try:
        cita = Cita.objects.get(pk=cita_id)
    except Cita.DoesNotExist:
        raise Http404('La cita no existe.')
    if not puede_ver(request, cita):
        raise Http404('La cita no existe.')
    return cita


def acciones(request, cita):
    pendiente = cita.estado in ('PROGRAMADA', 'EN_ESPERA')
    paciente = request.rol_citas == 'PACIENTE'
    return {
        'editar': not paciente and cita.estado not in ('COMPLETADA', 'CANCELADA', 'NO_ASISTIO'),
        'reprogramar': cita.estado == 'PROGRAMADA' and
            (request.gestiona_citas or paciente) and cita.fecha_inicio > timezone.now(),
        'cancelar': pendiente and (request.gestiona_citas or paciente) and
            (not paciente or cita.fecha_inicio > timezone.now()),
        'eliminar': request.rol_citas == 'ADMIN' and cita.estado == 'CANCELADA',
    }
