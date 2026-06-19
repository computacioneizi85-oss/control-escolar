from flask import (
    Blueprint,
    send_file,
    request,
    redirect,
    render_template,
    flash,
    url_for
)

from database.mongo import (
    alumnos,
    reportes,
    citatorios,
    configuracion,
    configuracion_backups
)

from utils.backup_manager import *

from datetime import datetime, timedelta

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

                "proxima_ejecucion": proxima

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