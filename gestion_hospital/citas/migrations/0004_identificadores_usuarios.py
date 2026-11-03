from django.db import migrations, models

from usuarios.identificadores import nuevo_id_usuario


def normalizar_usuarios(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'User')
    usuarios = Usuario.objects.using(schema_editor.connection.alias)
    documentos = list(usuarios.values('email', 'id'))
    correos = [u['email'] for u in documentos]
    if len(correos) != len(set(correos)):
        raise RuntimeError('Hay correos de usuario duplicados. Deben corregirse antes de asignar identificadores.')
    usados = set()
    cambios = []
    for documento in documentos:
        valor = documento['id']
        clave = nuevo_id_usuario() if valor is None or str(valor) in ('', 'None') else str(valor)
        if clave in usados:
            raise RuntimeError('Hay identificadores de usuario duplicados. Revisa los usuarios antes de continuar.')
        usados.add(clave)
        cambios.append((documento['email'], clave))
    # Se consulta por correo único porque los documentos antiguos no tienen id.
    # Los IDs numéricos válidos conservan su representación textual, de modo
    # que las referencias string de los otros módulos siguen siendo iguales.
    for correo, clave in cambios:
        usuarios.filter(email=correo).update(id=clave)
    with schema_editor.connection.cursor() as cursor:
        indices = schema_editor.connection.introspection.get_constraints(cursor, Usuario._meta.db_table)
    if not any(i.get('unique') and i.get('columns') == ['id'] for i in indices.values()):
        schema_editor.add_constraint(Usuario, models.UniqueConstraint(fields=['id'], name='users_id_unico'))


class Migration(migrations.Migration):
    atomic = False
    dependencies = [('citas', '0003_agenda_y_control_de_citas')]
    operations = [migrations.RunPython(normalizar_usuarios)]
