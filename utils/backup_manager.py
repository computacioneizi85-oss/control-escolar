import json

from io import BytesIO

from datetime import datetime, timedelta

from flask import send_file

from bson import json_util

from bson import ObjectId

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
    bitacora_restauraciones,
    backups_archivos,
    calificaciones,
    admins_secundarios,
    bitacora,
    auditoria

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
            ),

            "estado": "Correcto",

            "version": "1.0",

            "restaurado": False

        }

    )

def registrar_restauracion(

    usuario,

    tipo,

    archivo,

    resultado,

    mensaje

):

    bitacora_restauraciones.insert_one(

        {

            "usuario": usuario,

            "tipo": tipo,

            "archivo": archivo,

            "resultado": resultado,

            "mensaje": mensaje,

            "fecha": datetime.now()

        }

    )

def crear_backup_financiero_interno():

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

    return data

def crear_backup_control_escolar_interno():

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
        ),

        "calificaciones": list(
            calificaciones.find({}, {"_id": 0})
        ),

        "admins_secundarios": list(
            admins_secundarios.find({}, {"_id": 0})
        ),

        "bitacora": list(
            bitacora.find({}, {"_id": 0})
        ),

        "auditoria": list(
            auditoria.find({}, {"_id": 0})
        )

    }

    nombre = nombre_backup(
        "control_escolar_auto"
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

    return data

def crear_backup_sistema_interno():

    data = {

        # =========================
        # CONTROL ESCOLAR
        # =========================

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
        ),

        "calificaciones": list(
            calificaciones.find({}, {"_id": 0})
        ),

        "admins_secundarios": list(
            admins_secundarios.find({}, {"_id": 0})
        ),

        # =========================
        # FINANCIERO
        # =========================

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
        ),

        # =========================
        # CONFIGURACIÓN
        # =========================

        "configuracion": list(
            configuracion.find({}, {"_id": 0})
        ),

        # =========================
        # AUDITORÍA
        # =========================

        "bitacora": list(
            bitacora.find({}, {"_id": 0})
        ),

        "auditoria": list(
            auditoria.find({}, {"_id": 0})
        )

    }

    nombre = nombre_backup(
        "sistema_auto"
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

    return data

def obtener_historial_backups(
    tipo=None,
    limite=100
):

    consulta = {}

    if tipo is not None:
        consulta["tipo"] = tipo

    historial = list(

        backups_archivos.find(
            consulta
        ).sort(
            "fecha",
            -1
        ).limit(
            limite
        )

    )

    return historial

def eliminar_backup(
    backup_id
):

    backups_archivos.delete_one(

        {

            "_id": ObjectId(
                backup_id
            )

        }

    )

def crear_backup_sistema():

    data = {

        # =========================
        # CONTROL ESCOLAR
        # =========================

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
        ),

        "calificaciones": list(
            calificaciones.find({}, {"_id": 0})
        ),

        "admins_secundarios": list(
            admins_secundarios.find({}, {"_id": 0})
        ),

        # =========================
        # FINANCIERO
        # =========================

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
        ),

        # =========================
        # CONFIGURACIÓN
        # =========================

        "configuracion": list(
            configuracion.find({}, {"_id": 0})
        ),

        # =========================
        # AUDITORÍA
        # =========================

        "bitacora": list(
            bitacora.find({}, {"_id": 0})
        ),

        "auditoria": list(
            auditoria.find({}, {"_id": 0})
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
        ),

        "calificaciones": list(
            calificaciones.find({}, {"_id": 0})
        ),

        "admins_secundarios": list(
            admins_secundarios.find({}, {"_id": 0})
        ),

        "bitacora": list(
            bitacora.find({}, {"_id": 0})
        ),

        "auditoria": list(
            auditoria.find({}, {"_id": 0})
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

def obtener_backup_por_id(
    backup_id
):

    return backups_archivos.find_one(

        {

            "_id": ObjectId(
                backup_id
            )

        }

    )

# def restaurar_backup_financiero(
#    backup_id,
#    usuario="Administrador"
#):

#    backup = obtener_backup_por_id(
#        backup_id
#    )

#    if backup is None:

#        return False, "No existe el respaldo."

#    if backup.get("tipo") != "financiero":

#        return False, "El respaldo seleccionado no es #financiero."

def restaurar_backup(
    backup_id,
    usuario="Administrador"
):

    backup = obtener_backup_por_id(
        backup_id
    )

    if backup is None:

        return False, "No existe el respaldo."

    tipo = backup.get(
        "tipo"
    )

    datos = backup.get(
        "contenido",
        {}
    )

    try:

        # ===========================
        # FINANCIERO
        # ===========================

        if tipo == "financiero":

            crear_backup_financiero_interno()

            pagos.delete_many({})

            movimientos_pagos.delete_many({})

            mensualidades.delete_many({})

            config_recargos.delete_many({})

            bitacora_pagos.delete_many({})

            if datos.get("pagos"):

                pagos.insert_many(
                    datos["pagos"]
                )

            if datos.get("movimientos_pagos"):

                movimientos_pagos.insert_many(
                    datos["movimientos_pagos"]
                )

            if datos.get("mensualidades"):

                mensualidades.insert_many(
                    datos["mensualidades"]
                )

            if datos.get("config_recargos"):

                config_recargos.insert_many(
                    datos["config_recargos"]
                )

            if datos.get("bitacora_pagos"):

                bitacora_pagos.insert_many(
                    datos["bitacora_pagos"]
                )

            backups_archivos.update_one(

                {

                    "_id": backup["_id"]

                },

                {

                    "$set": {

                        "restaurado": True,

                        "fecha_restauracion": datetime.now(),

                        "restaurado_por": usuario

                    }

                }

            )

            registrar_restauracion(

                usuario,

                tipo,

                backup["nombre"],

                "Correcto",

                "Restauración completada"

            )

            return True, "Restauración completada."

        # ===========================
        # CONTROL ESCOLAR
        # ===========================

        elif tipo == "control_escolar":

            return _restaurar_control_escolar(

                datos,

                backup,

                usuario

            )

        # ===========================
        # SISTEMA
        # ===========================

        elif tipo == "sistema":

            return _restaurar_sistema(

                datos,

                backup,

                usuario

            )


    except Exception as e:

        registrar_restauracion(

            usuario,

            tipo,

            backup["nombre"],

            "Error",

            str(e)

        )

        return False, str(e)

def _restaurar_control_escolar(
    datos,
    backup,
    usuario
):

    crear_backup_control_escolar_interno()

    colecciones = [

        (alumnos, "alumnos"),

        (maestros, "maestros"),

        (grupos, "grupos"),

        (materias, "materias"),

        (horarios, "horarios"),

        (reportes, "reportes"),

        (citatorios, "citatorios"),

        (avisos, "avisos"),

        (usuarios, "usuarios"),

        (padres, "padres"),

        (calificaciones, "calificaciones"),

        (admins_secundarios, "admins_secundarios"),

        (bitacora, "bitacora"),

        (auditoria, "auditoria")

    ]

    for coleccion, nombre in colecciones:

        coleccion.delete_many({})

        if datos.get(nombre):

            coleccion.insert_many(

                datos[nombre]

            )

    backups_archivos.update_one(

        {

            "_id": backup["_id"]

        },

        {

            "$set": {

                "restaurado": True,

                "fecha_restauracion": datetime.now(),

                "restaurado_por": usuario

            }

        }

    )

    registrar_restauracion(

        usuario,

        "control_escolar",

        backup["nombre"],

        "Correcto",

        "Restauración completada"

    )

    return True, "Restauración de Control Escolar completada."

def _restaurar_sistema(
    datos,
    backup,
    usuario
):

    crear_backup_sistema_interno()

    colecciones = [

        (alumnos, "alumnos"),

        (maestros, "maestros"),

        (grupos, "grupos"),

        (materias, "materias"),

        (horarios, "horarios"),

        (reportes, "reportes"),

        (citatorios, "citatorios"),

        (avisos, "avisos"),

        (usuarios, "usuarios"),

        (padres, "padres"),

        (calificaciones, "calificaciones"),

        (admins_secundarios, "admins_secundarios"),

        (pagos, "pagos"),

        (movimientos_pagos, "movimientos_pagos"),

        (mensualidades, "mensualidades"),

        (config_recargos, "config_recargos"),

        (bitacora_pagos, "bitacora_pagos"),

        (configuracion, "configuracion"),

        (bitacora, "bitacora"),

        (auditoria, "auditoria")

    ]

    for coleccion, nombre in colecciones:

        coleccion.delete_many({})

        if datos.get(nombre):

            coleccion.insert_many(

                datos[nombre]

            )

    backups_archivos.update_one(

        {

            "_id": backup["_id"]

        },

        {

            "$set": {

                "restaurado": True,

                "fecha_restauracion": datetime.now(),

                "restaurado_por": usuario

            }

        }

    )


    registrar_restauracion(

        usuario,

        "sistema",

        backup["nombre"],

        "Correcto",

        "Restauración completa del sistema realizada correctamente."

    )

    return True, "Restauración completa del sistema realizada correctamente."