from flask import Blueprint, render_template, request, redirect, session, url_for, send_file
from bson.objectid import ObjectId
from datetime import datetime

from database.mongo import (
    alumnos,
    maestros,
    horarios,
    configuracion,
    citatorios,
    avisos,
    reportes
)

from pdf.generador import generar_citatorio_pdf

maestro_bp = Blueprint("maestro", __name__)


# ================= SEGURIDAD =================
def verificar_maestro():
    return session.get("rol") == "maestro"


# ================= PANEL =================
@maestro_bp.route("/panel_maestro")
def panel_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({
        "usuario": session.get("usuario")
    }) or {}

    grupos = maestro.get("grupos", [])
    materias_maestro = maestro.get("materias", [])

    lista_alumnos = list(
        alumnos.find({
            "grupo": {
                "$in": grupos
            }
        })
    )

    lista_horarios = list(
        horarios.find({
            "grupo": {
                "$in": grupos
            }
        })
    )

    config = configuracion.find_one() or {
        "captura_evaluaciones": True,
        "trimestre_1": True,
        "trimestre_2": False,
        "trimestre_3": False
    }

    return render_template(
        "panel_maestro.html",
        alumnos=lista_alumnos,
        grupos=grupos,
        materias=materias_maestro,
        horarios=lista_horarios,
        config=config
    )


# ================= GUARDAR CALIFICACIONES =================
@maestro_bp.route("/guardar_calificaciones_ajax", methods=["POST"])
def guardar_calificaciones_ajax():

    if not verificar_maestro():
        return {"status": "error"}

    config = configuracion.find_one() or {}

    if not config.get("captura_evaluaciones", True):
        return {
            "status": "error",
            "msg": "Captura deshabilitada"
        }

    alumno = request.form.get("alumno")
    materia = request.form.get("materia")
    trimestre = request.form.get("trimestre")

    try:
        cal = float(request.form.get("cal1") or 0)
    except:
        cal = 0

    maestro_actual = maestros.find_one({
        "usuario": session.get("usuario")
    }) or {}

    nombre_maestro = maestro_actual.get("nombre", "")

    alumno_db = alumnos.find_one({
        "nombre": {
            "$regex": f"^{alumno}$",
            "$options": "i"
        }
    })

    if not alumno_db:
        return {
            "status": "error",
            "msg": "Alumno no encontrado"
        }

    grupo = alumno_db.get("grupo", "")

    alumnos.update_one(
        {"_id": alumno_db["_id"]},
        {
            "$pull": {
                "calificaciones": {
                    "materia": materia,
                    "trimestre": trimestre
                }
            }
        }
    )

    alumnos.update_one(
        {"_id": alumno_db["_id"]},
        {
            "$push": {
                "calificaciones": {
                    "materia": materia,
                    "calificacion": cal,
                    "trimestre": trimestre,
                    "grupo": grupo,
                    "maestro": nombre_maestro,
                    "fecha": datetime.now()
                }
            }
        }
    )

    return {"status": "ok"}