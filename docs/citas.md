# Citas médicas

## Puesta en marcha

Desde `gestion_hospital`, usar el entorno virtual del equipo:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate --run-syncdb
python manage.py check
python manage.py runserver
```

`--run-syncdb` crea las colecciones de las apps que el repositorio entrega sin
paquete de migraciones activo, como usuarios y registros médicos. Para actualizar
una instalación que ya funciona basta con `python manage.py migrate citas`.
La migración `0003_agenda_y_control_de_citas` crea el índice único del bloqueo de
agenda y añade versiones e historial. Debe aplicarse antes de usar las pantallas.

La migración `0004_identificadores_usuarios` corrige usuarios antiguos que se
guardaron sin `id`. Mantiene el atributo `User.id` que utilizan las otras apps,
ahora como cadena de hasta 24 caracteres generada por el modelo, y añade su índice
único. Los IDs numéricos anteriores conservan el mismo valor textual que usan las
referencias embebidas. Los usuarios sin ID reciben uno; se conservan sus demás
datos. Si detecta correos o IDs duplicados, se detiene para evitar asociaciones
ambiguas. Después de esta actualización hay que cerrar sesión e iniciarla de nuevo.

## Flujo

Entrar en `/panel/login/`. Los roles médico, paciente y recepción llegan a
`/citas/`; administración tiene accesos desde el panel. Un médico necesita una
especialidad y un horario activo antes de que puedan agendarse sus turnos.

Los horarios son semanales, en `America/Bogota`, con un día entre lunes y domingo,
hora inicial, hora final y duración de consulta entre 5 y 240 minutos. Se pueden
crear varias franjas por día; sus intervalos activos no se pueden solapar para
el mismo médico. Las franjas no atraviesan medianoche. El tiempo sobrante al final
que no alcanza para una consulta no genera un turno.

El formulario muestra solo turnos futuros, dentro de los próximos 365 días.
La duración procede del horario, no de datos enviados por el navegador. Los
pacientes y médicos deben existir, estar activos y tener el rol correcto.
Los snapshots se construyen en el servidor; no se aceptan nombres ni IDs de
usuarios inexistentes como reemplazo de la selección. El modelo de usuarios
del equipo no incluye documento de identidad: no se inventa una cédula.

Se consideran cruces los intervalos donde `inicio_existente < fin_nuevo` y
`fin_existente > inicio_nuevo`. Se comprueba tanto el médico como el paciente,
incluyendo citas con otro especialista. Dos turnos adyacentes sí son válidos.
Las canceladas y las inasistencias liberan el intervalo. La comprobación se repite
al guardar para cubrir cambios posteriores a la consulta de disponibilidad.

La reprogramación mantiene paciente y médico, permite elegir otra fecha/turno y
exige un motivo. Conserva el snapshot y anota turno anterior, nuevo y autor.
Solo se reprograman citas `PROGRAMADA` que aún no han iniciado y no tienen registro
médico. Para cambiar de médico, cancelar la cita y agendar una nueva.

## Estados y conservación

| Estado actual | Cambios permitidos |
| --- | --- |
| PROGRAMADA | EN_ESPERA, CANCELADA, NO_ASISTIO |
| EN_ESPERA | EN_CONSULTA, CANCELADA |
| EN_CONSULTA | COMPLETADA |
| COMPLETADA, CANCELADA, NO_ASISTIO | Ninguno |

En estados abiertos también puede guardarse una corrección del motivo sin
cambiar el estado. La atención comienza el mismo día del turno, desde 30 minutos
antes; completar exige que haya llegado la hora de inicio. La inasistencia solo
puede registrarse después de que termine el turno. Cancelar exige motivo.

Las citas finalizadas son de consulta. Las canceladas se conservan normalmente;
solo administración puede eliminarlas definitivamente, con confirmación y si no
tienen registros médicos. Un GET nunca elimina datos.

Una cita vinculada a un registro médico no se cancela, marca ausente, reprograma
ni elimina. La vista de creación de registros médicos usa el mismo bloqueo y
revalida la referencia antes de guardar, para no apuntar a una cita que desapareció
o fue cancelada mientras el usuario completaba el formulario.

## Acceso

| Rol | Agenda visible | Operaciones |
| --- | --- | --- |
| ADMIN | Todas las citas | Agendar, horarios, atención, reprogramar, cancelar y eliminar canceladas sin registros |
| RECEPCIONISTA | Todas las citas | Agendar, horarios, atención, reprogramar y cancelar |
| DOCTOR | Solo sus citas | Sus horarios y avance de la atención |
| PACIENTE | Solo sus citas | Agendar para sí mismo; reprogramar y cancelar antes del inicio |
| FARMACEUTICO / sin sesión | Sin acceso | Iniciar sesión con un rol autorizado |

Los permisos de citas se verifican en el servidor en cada petición usando el
usuario activo y su rol actual, además de comprobar a quién pertenece la cita.
Ocultar botones no sustituye esa comprobación. Esto se aplica al módulo de citas;
los permisos de las otras apps siguen siendo responsabilidad de sus módulos.

## Organización del código

- `models.py`: citas, snapshots, horarios y bloqueo de escritura; sin ForeignKey ni JOIN.
- `servicios.py`: reglas de negocio y persistencia mediante el ORM.
- `forms.py`: validación y selección de usuarios/turnos; sin consultas nativas de MongoDB.
- `acceso.py`: sesión, roles y pertenencia.
- `usuarios/identificadores.py`: generación de IDs; usar `ObjectId` para generarlos
  no realiza ninguna consulta ni escritura nativa de MongoDB.
- `views.py`: coordinación de formularios, servicios, mensajes y plantillas.
- `templates/citas/` y `static/citas/`: recursos sin colisiones con las otras apps.

La agenda incluye búsqueda por nombre, médico, especialidad o ID, filtros de
estado/fechas y páginas de 15 resultados. Se filtran en Python las partes embebidas
para evitar diferencias de consultas entre versiones de Djongo; para volúmenes
grandes habría que revisar índices y paginación directamente en la base.

## Escrituras simultáneas y recuperación

Djongo en este proyecto no ofrece transacciones de múltiples documentos.
`BloqueoAgenda.clave` tiene un índice único; una escritura adquiere el bloqueo
`agenda`, comprueba otra vez los datos y lo libera al terminar, incluso ante
errores de validación. Si otra petición intenta escribir al mismo tiempo, obtiene
un mensaje para reintentar. Esta protección cubre las vistas y servicios del módulo,
incluyendo procesos distintos del servidor. El admin de Django permite consultar
citas/horarios, pero no escribir saltándose esas reglas.

Los formularios incluyen una versión. Si otro usuario guardó antes, la versión
antigua se rechaza y hay que recargar. Las escrituras manuales externas al módulo
no participan en estas protecciones.

Si el proceso es terminado forzosamente durante una escritura, puede quedar un
bloqueo huérfano. No se borra automáticamente por tiempo, para no interrumpir una
escritura todavía activa. Para recuperarlo:

1. Detener todos los procesos de servidor que usen esta base y comprobar el último
   movimiento, porque una petición interrumpida podría haberse guardado.
2. Consultar su token mediante el ORM:

   ```powershell
   python manage.py shell -c "from citas.models import BloqueoAgenda; print(list(BloqueoAgenda.objects.values('token', 'fecha_creacion')))"
   ```

3. Liberar únicamente el token que se acaba de revisar y volver a iniciar el servidor:

   ```powershell
   python manage.py liberar_agenda --token TOKEN_REVISADO --servidor-detenido
   ```

No se debe liberar un bloqueo mientras otra instancia esté atendiendo solicitudes.

## Pruebas

```powershell
python manage.py check
python manage.py makemigrations citas --check --dry-run
python manage.py test citas --keepdb --noinput
python -m pip check
```

Las pruebas de integración usan MongoDB real en `test_gestion_hospital_db`,
separado de la base de trabajo. Cubren el flujo completo, permisos, snapshots,
zona horaria, cruces exactos/parciales/adyacentes, formularios manipulados, fechas
inválidas, reprogramación, cancelación, estados, registros vinculados, horarios,
versiones antiguas, solicitudes simultáneas, recuperación del bloqueo y CSRF.
