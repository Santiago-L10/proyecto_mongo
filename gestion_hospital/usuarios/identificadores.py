from bson import ObjectId


def nuevo_id_usuario():
    # Solo genera un identificador. La lectura/escritura sigue en el ORM.
    return str(ObjectId())
