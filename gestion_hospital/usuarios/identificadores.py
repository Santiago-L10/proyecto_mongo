from bson import ObjectId


def nuevo_id_usuario():
    return str(ObjectId())
