import json

from io import BytesIO

from datetime import datetime, timedelta

from flask import send_file

from bson import json_util

from database.mongo import (
    alumnos,
    reportes,
    citatorios,
    configuracion,
    configuracion_backups,
    backups_archivos
)


def nombre_backup(tipo):

    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"backup_{tipo}_{fecha}.json"

def guardar_backup_mongo(
    tipo,
    nombre,
    datos,
    usuario="Administrador"
):

    backups_archivos.insert_one(

        {

            "tipo": tipo,

            "nombre": nombre,

            "fecha": datetime.now(),

            "usuario": usuario,

            "contenido": datos,

            "tamano": len(
                json.dumps(
                    datos,
                    default=str
                )
            )

        }

    )

def crear_backup_sistema():

    data = {

        "alumnos": list(
            alumnos.find({}, {"_id": 0})
        ),

        "reportes": list(
            reportes.find({}, {"_id": 0})
        ),

        "citatorios": list(
            citatorios.find({}, {"_id": 0})
        ),

        "configuracion": list(
            configuracion.find({}, {"_id": 0})
        )

    }

    nombre = nombre_backup(
        "sistema"
    )

    guardar_backup_mongo(
        "sistema",
        nombre,
        data
    )

    configuracion_backups.update_one(

        {
            "tipo": "sistema"
        },

        {
            "$set": {
                "ultima_ejecucion": datetime.now()
            }
        },

        upsert=True

    )

    buffer = BytesIO()

    buffer.write(

        json.dumps(
            data,
            indent=4,
            default=str,
            ensure_ascii=False
        ).encode("utf-8")

    )

    buffer.seek(0)

    return send_file(

        buffer,

        as_attachment=True,

        download_name=nombre,

        mimetype="application/json"

    )