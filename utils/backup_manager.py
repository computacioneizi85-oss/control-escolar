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

    maestros,
    grupos,
    materias,
    horarios,
    avisos,
    usuarios,
    padres,

    pagos,
    movimientos_pagos,
    mensualidades,
    config_recargos,
    bitacora_pagos,

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

def obtener_historial_backups(
    tipo=None
):

    consulta = {}

    if tipo:

        consulta["tipo"] = tipo

    return list(

        backups_archivos.find(

            consulta

        ).sort(

            "fecha",

            -1

        )

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

def crear_backup_financiero():

    data = {

        "pagos": list(
            pagos.find({}, {"_id": 0})
        ),

        "movimientos_pagos": list(
            movimientos_pagos.find({}, {"_id": 0})
        ),

        "mensualidades": list(
            mensualidades.find({}, {"_id": 0})
        ),

        "config_recargos": list(
            config_recargos.find({}, {"_id": 0})
        ),

        "bitacora_pagos": list(
            bitacora_pagos.find({}, {"_id": 0})
        )

    }

    nombre = nombre_backup(
        "financiero"
    )

    guardar_backup_mongo(
        "financiero",
        nombre,
        data
    )

    configuracion_backups.update_one(

        {
            "tipo": "financiero"
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

def crear_backup_control_escolar():

    data = {

        "alumnos": list(
            alumnos.find({}, {"_id": 0})
        ),

        "maestros": list(
            maestros.find({}, {"_id": 0})
        ),

        "grupos": list(
            grupos.find({}, {"_id": 0})
        ),

        "materias": list(
            materias.find({}, {"_id": 0})
        ),

        "horarios": list(
            horarios.find({}, {"_id": 0})
        ),

        "reportes": list(
            reportes.find({}, {"_id": 0})
        ),

        "citatorios": list(
            citatorios.find({}, {"_id": 0})
        ),

        "avisos": list(
            avisos.find({}, {"_id": 0})
        ),

        "usuarios": list(
            usuarios.find({}, {"_id": 0})
        ),

        "padres": list(
            padres.find({}, {"_id": 0})
        )

    }

    nombre = nombre_backup(
        "control_escolar"
    )

    guardar_backup_mongo(
        "control_escolar",
        nombre,
        data
    )

    configuracion_backups.update_one(

        {
            "tipo": "control_escolar"
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