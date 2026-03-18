from flask import Blueprint, send_file, request, redirect
from database.mongo import alumnos, reportes, citatorios, configuracion
import json
from io import BytesIO

backup_bp = Blueprint("backup", __name__, url_prefix="/admin/backup")


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
    buffer.write(json.dumps(data, indent=4).encode("utf-8"))
    buffer.seek(0)

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