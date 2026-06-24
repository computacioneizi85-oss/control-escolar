from flask import (
    Blueprint,
    send_file,
    request,
    redirect,
    render_template,
    flash,
    url_for
)

from io import BytesIO



from database.mongo import (
    alumnos,
    reportes,
    citatorios,
    configuracion,
    configuracion_backups
)

from utils.backup_manager import *

from datetime import datetime, timedelta

import json

backup_bp = Blueprint("backup", __name__, url_prefix="/admin/backup")


# =========================
# DESCARGAR BACKUP
# =========================
@backup_bp.route("/descargar")
def descargar_backup():

    return crear_backup_sistema()

# =========================
# RESTAURAR BACKUP
# =========================
@backup_bp.route("/restaurar", methods=["POST"])
def restaurar_backup_archivo():

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

    return crear_backup_financiero()

@backup_bp.route("/control_escolar")
def descargar_backup_control_escolar():

    return crear_backup_control_escolar()

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

            crear_backup_sistema()

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

            crear_backup_financiero()

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

            crear_backup_control_escolar()

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

    configuraciones = list(
        configuracion_backups.find()
    )

    historial = obtener_historial_backups()

    return render_template(

        "backups.html",

        configuraciones=configuraciones,

        historial=historial

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

    if intervalo < 1:
        intervalo = 1

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

                "proxima_ejecucion": proxima,

                "ultima_ejecucion": None

            }

        },

        upsert=True

    )

    return redirect(
        "/admin/backup/"
    )

#@backup_bp.route("/historial")
#def historial():

#    historial = obtener_historial_backups()

#    return render_template(
#        "backup_historial.html",
#        historial=historial
#    )

@backup_bp.route(
    "/eliminar/<backup_id>"
)
def eliminar_backup_historial(
    backup_id
):

    eliminar_backup(
        backup_id
    )

    flash(
        "Respaldo eliminado correctamente.",
        "success"
    )

    return redirect(
        "/admin/backup/"
    )

@backup_bp.route(
    "/descargar/<backup_id>"
)
def descargar_backup_historial(
    backup_id
):

    backup = obtener_backup_por_id(
        backup_id
    )

    if backup is None:

        flash(
            "No se encontró el respaldo.",
            "danger"
        )

        return redirect(
            "/admin/backup/"
        )

    contenido = json.dumps(

        backup["contenido"],

        indent=4,

        ensure_ascii=False,

        default=str

    )

    memoria = BytesIO()

    memoria.write(
        contenido.encode("utf-8")
    )

    memoria.seek(0)

    return send_file(

        memoria,

        as_attachment=True,

        download_name=backup["nombre"],

        mimetype="application/json"

    )

# =========================
# RESTAURAR RESPALDO FINANCIERO
# =========================

@backup_bp.route(
    "/restaurar_financiero/<backup_id>",
    methods=["POST"]
)
def restaurar_financiero(
    backup_id
):

    usuario = "Administrador"

    resultado, mensaje = restaurar_backup(

        backup_id,

        usuario

    )

    if resultado:

        flash(

            mensaje,

            "success"

        )

    else:

        flash(

            mensaje,

            "danger"

        )

    return redirect(

        "/admin/backup/"

    )

@backup_bp.route(
    "/restaurar_control_escolar/<backup_id>",
    methods=["POST"]
)
def restaurar_control_escolar(
    backup_id
):

    usuario = "Administrador"

    resultado, mensaje = restaurar_backup(

        backup_id,

        usuario

    )

    if resultado:

        flash(

            mensaje,

            "success"

        )

    else:

        flash(

            mensaje,

            "danger"

        )

    return redirect(

        "/admin/backup/"

    )

@backup_bp.route(
    "/restaurar_sistema/<backup_id>",
    methods=["POST"]
)
def restaurar_sistema(
    backup_id
):

    usuario = "Administrador"

    resultado, mensaje = restaurar_backup(

        backup_id,

        usuario

    )

    if resultado:

        flash(

            mensaje,

            "success"

        )

    else:

        flash(

            mensaje,

            "danger"

        )

    return redirect(

        "/admin/backup/"

    )