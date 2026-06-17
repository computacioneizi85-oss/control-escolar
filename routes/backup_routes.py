from flask import Blueprint, send_file, request, redirect
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
    bitacora,
    auditoria,
    pagos,
    movimientos_pagos,
    mensualidades,
    config_recargos,
    bitacora_pagos,
    historial_backups,
    configuracion_backups
)

from flask import render_template

from datetime import datetime, timedelta

import os

import json
from io import BytesIO

backup_bp = Blueprint("backup", __name__, url_prefix="/admin/backup")

BASE_BACKUP = "backups"

CARPETA_SISTEMA = os.path.join(
    BASE_BACKUP,
    "sistema"
)

CARPETA_FINANCIERO = os.path.join(
    BASE_BACKUP,
    "financiero"
)

CARPETA_ESCOLAR = os.path.join(
    BASE_BACKUP,
    "escolar"
)

os.makedirs(
    CARPETA_SISTEMA,
    exist_ok=True
)

os.makedirs(
    CARPETA_FINANCIERO,
    exist_ok=True
)

os.makedirs(
    CARPETA_ESCOLAR,
    exist_ok=True
)

def nombre_backup(
    tipo
):

    fecha = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return f"backup_{tipo}_{fecha}.json"

# =========================
# DESCARGAR BACKUP
# =========================
@backup_bp.route("/descargar")
def descargar_backup():

    data = {
        "alumnos": list(alumnos.find({}, {"_id": 0})),
        "reportes": list(reportes.find({}, {"_id": 0})),
        "citatorios": list(citatorios.find({}, {"_id": 0})),
        "configuracion": list(configuracion.find({}, {"_id": 0}))
    }

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

    return send_file(
        buffer,
        as_attachment=True,
        download_name="backup_sistema.json",
        mimetype="application/json"
    )

# =========================
# RESTAURAR BACKUP
# =========================
@backup_bp.route("/restaurar", methods=["POST"])
def restaurar_backup():

    archivo = request.files.get("archivo")

    if not archivo:
        return "❌ No se subió archivo"

    try:
        data = json.load(archivo)

        # ⚠️ BORRAR DATOS ACTUALES (controlado)
        alumnos.delete_many({})
        reportes.delete_many({})
        citatorios.delete_many({})
        configuracion.delete_many({})

        # 🔥 INSERTAR BACKUP
        if "alumnos" in data:
            alumnos.insert_many(data["alumnos"])

        if "reportes" in data:
            reportes.insert_many(data["reportes"])

        if "citatorios" in data:
            citatorios.insert_many(data["citatorios"])

        if "configuracion" in data:
            configuracion.insert_many(data["configuracion"])

        return redirect("/admin")

    except Exception as e:
        return f"🔥 ERROR AL RESTAURAR: {str(e)}"

@backup_bp.route("/financiero")
def descargar_backup_financiero():

    data = {

        "pagos": list(
            pagos.find(
                {},
                {"_id": 0}
            )
        ),

        "movimientos_pagos": list(
            movimientos_pagos.find(
                {},
                {"_id": 0}
            )
        ),

        "mensualidades": list(
            mensualidades.find(
                {},
                {"_id": 0}
            )
        ),

        "config_recargos": list(
            config_recargos.find(
                {},
                {"_id": 0}
            )
        ),

        "bitacora_pagos": list(
            bitacora_pagos.find(
                {},
                {"_id": 0}
            )
        )

    }

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

    return send_file(
        buffer,
        as_attachment=True,
        download_name="backup_financiero.json",
        mimetype="application/json"
    )

@backup_bp.route("/control_escolar")
def descargar_backup_control_escolar():

    data = {

        "alumnos": list(
            alumnos.find(
                {},
                {"_id": 0}
            )
        ),

        "maestros": list(
            maestros.find(
                {},
                {"_id": 0}
            )
        ),

        "grupos": list(
            grupos.find(
                {},
                {"_id": 0}
            )
        ),

        "materias": list(
            materias.find(
                {},
                {"_id": 0}
            )
        ),

        "horarios": list(
            horarios.find(
                {},
                {"_id": 0}
            )
        ),

        "reportes": list(
            reportes.find(
                {},
                {"_id": 0}
            )
        ),

        "citatorios": list(
            citatorios.find(
                {},
                {"_id": 0}
            )
        ),

        "avisos": list(
            avisos.find(
                {},
                {"_id": 0}
            )
        ),

        "usuarios": list(
            usuarios.find(
                {},
                {"_id": 0}
            )
        ),

        "padres": list(
            padres.find(
                {},
                {"_id": 0}
            )
        )

    }

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

    return send_file(
        buffer,
        as_attachment=True,
        download_name="backup_control_escolar.json",
        mimetype="application/json"
    )

def verificar_respaldos_automaticos():

    ahora = datetime.now()

    configuraciones = configuracion_backups.find(
        {
            "activo": True
        }
    )

    for config in configuraciones:

        proxima = config.get(
            "proxima_ejecucion"
        )

        if not proxima:
            continue

        if ahora < proxima:
            continue

        tipo = config.get(
            "tipo"
        )

        if tipo == "sistema":

            configuracion_backups.update_one(

                {
                    "_id": config["_id"]
                },

                {
                    "$set": {

                        "ultima_ejecucion": ahora,

                        "proxima_ejecucion":
                            ahora + timedelta(
                                hours=config.get(
                                    "intervalo",
                                    24
                                )
                            )

                    }

                }

            )

        elif tipo == "financiero":

            configuracion_backups.update_one(

                {
                    "_id": config["_id"]
                },

                {
                    "$set": {

                        "ultima_ejecucion": ahora,

                        "proxima_ejecucion":
                            ahora + timedelta(
                                hours=config.get(
                                    "intervalo",
                                    24
                                )
                            )

                    }

                }

            )

        elif tipo == "control_escolar":

            configuracion_backups.update_one(

                {
                    "_id": config["_id"]
                },

                {
                    "$set": {

                        "ultima_ejecucion": ahora,

                        "proxima_ejecucion":
                            ahora + timedelta(
                                hours=config.get(
                                    "intervalo",
                                    24
                                )
                            )

                    }

                }

            )

@backup_bp.route("/")
def vista_backups():

    verificar_respaldos_automaticos()

    configuraciones = list(

        configuracion_backups.find()

    )

    return render_template(

        "backups.html",

        configuraciones=configuraciones

    )
@backup_bp.route(
    "/guardar_configuracion",
    methods=["POST"]
)
def guardar_configuracion_backup():

    tipo = request.form.get(
        "tipo"
    )

    unidad = request.form.get(
        "unidad"
    )

    activo = request.form.get(
        "activo"
    ) == "on"

    intervalo = int(
        request.form.get(
            "intervalo",
            24
        )
    )
    ahora = datetime.now()

    if unidad == "horas":

        proxima = ahora + timedelta(
            hours=intervalo
        )

    elif unidad == "dias":

        proxima = ahora + timedelta(
            days=intervalo
        )

    else:

        proxima = ahora

    configuracion_backups.update_one(

        {
            "tipo": tipo
        },

        {
            "$set": {

                "tipo": tipo,

                "unidad": unidad,

                "intervalo": intervalo,

                "activo": activo,

                "ultima_actualizacion": ahora,

                "proxima_ejecucion": proxima

            }

        },

        upsert=True

    )

    return redirect(
        "/admin/backup/"
    )