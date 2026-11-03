# Proyecto MongoDB - Gestión Hospitalaria

Proyecto académico con Django, Djongo y MongoDB. Los módulos se ejecutan dentro
del mismo proyecto Django.

## Instalación en Windows

MongoDB debe estar iniciado en `mongodb://localhost:27017`. La base configurada
es `gestion_hospital_db`.

Desde la raíz del repositorio:

```powershell
cd gestion_hospital
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip check
python manage.py check
python manage.py migrate --run-syncdb
python manage.py runserver
```

Si `venv` ya existe, omitir su creación. Usar siempre el Python de ese entorno;
también se puede ejecutar directamente `.\venv\Scripts\python.exe manage.py check`.
La integración de citas se verificó con Python 3.12, Django 3.1.12,
Djongo 1.3.7 y PyMongo 3.11.4, según las dependencias del equipo.

Rutas principales:

- Panel: <http://127.0.0.1:8000/panel/>
- Citas: <http://127.0.0.1:8000/citas/>
- Registros médicos: <http://127.0.0.1:8000/registros_medicos/>
- Facturación: <http://127.0.0.1:8000/facturacion/homeFact/>

## Integración del módulo de citas

Si aparece `cannot import name 'six' from 'django.utils'`, comprobar la versión
efectivamente instalada:

```powershell
python -m pip show Django djongo pymongo
python -m pip install -r requirements.txt
```

El entorno anterior tenía Djongo 1.2.31 aunque el archivo de dependencias pedía
1.3.7. Con la versión del equipo no hace falta inyectar `six` en `manage.py`
ni modificar archivos de `site-packages`.

Citas usa `models.EmbeddedField`, como usuarios, farmacia y facturación. Sus
snapshots de paciente y médico se guardan y recuperan como diccionarios a través
del ORM de Django. La migración inicial también usa este campo, de modo que
Django puede cargar el historial con Djongo 1.3.7.

La migración `0002_alinear_campos_embebidos` alinea los defaults y validaciones
con los modelos actuales y convierte los valores antiguos `SI`/`NO` de los
horarios en booleanos mediante el ORM. Evita `ALTER COLUMN TYPE`, que este
conector no implementa. La conversión de datos no tiene reversión automática.
Para incorporar únicamente las migraciones de citas a una base ya integrada:

```powershell
python manage.py migrate citas
```

Las citas conservan su clave primaria numérica `id`. Registros médicos valida
esa clave con `Cita.objects.filter(pk=...).exists()`; no necesita una llave
foránea. Pacientes y médicos se seleccionan entre usuarios activos registrados.
El servidor construye los snapshots y conserva sus datos históricos. Como
`User` no tiene cédula, `id_user` referencia el ID del usuario.
La migración `0004` completa los IDs que faltan en usuarios antiguos y mantiene
los demás datos. Después de actualizar, cerrar sesión y volver a ingresar.

Las plantillas viven en `citas/templates/citas/` y el CSS en
`citas/static/citas/style.css`, para evitar que oculten el `layout.html` y el
`style.css` del módulo de registros médicos.

## Verificación

Con MongoDB en ejecución:

```powershell
python manage.py check
python manage.py makemigrations citas --check --dry-run
python manage.py test citas --keepdb --noinput
```

Las pruebas usan la base separada `test_gestion_hospital_db`. Comprueban el CRUD
con persistencia real de subdocumentos, horarios, cruces de agenda, solicitudes
simultáneas, permisos, reprogramación, estados, historial, referencias a registros
médicos, migraciones, CSRF y separación de plantillas y recursos estáticos.

## Uso de citas

1. Iniciar sesión en `/panel/login/`.
2. Registrar usuarios con rol `PACIENTE` y `DOCTOR`. El médico debe tener especialidad.
3. Entrar a **Horarios médicos** y crear sus franjas semanales, por ejemplo lunes
   de 08:00 a 12:00 con consultas de 30 minutos.
4. En **Agendar cita**, seleccionar médico y fecha, consultar disponibilidad,
   seleccionar paciente y turno, indicar el motivo y confirmar.
5. Desde el detalle se puede reprogramar, cancelar con motivo o avanzar la atención,
   según el rol y el estado. Las horas se interpretan y muestran en Bogotá.

Administración y recepción gestionan la agenda; cada médico ve sus citas y
administra sus horarios; cada paciente ve, agenda, reprograma y cancela sus citas
futuras. Solo administración puede eliminar citas canceladas sin registros médicos.

Ver [reglas, pruebas y operación de la agenda](docs/citas.md).
