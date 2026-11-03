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
python manage.py migrate
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
foránea. Los IDs del paciente y del médico dentro de los snapshots son cadenas
independientes que se ingresan en el formulario.

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
con persistencia real de subdocumentos, el vínculo con registros médicos, la
conversión de horarios antiguos, los errores del formulario y la separación de
plantillas y recursos estáticos.
