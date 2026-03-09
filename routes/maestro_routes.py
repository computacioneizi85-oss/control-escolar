from flask import Blueprint, render_template, request, redirect, session
from bson.objectid import ObjectId

from database.mongo import maestros, alumnos, materias, grupos

maestro_bp = Blueprint("maestro", __name__)


# PANEL MAESTRO
@maestro_bp.route("/panel_maestro")
def panel_maestro():

    if "rol" not in session or session["rol"] != "maestro":
        return redirect("/")

    nombre_maestro = session["usuario"]

    lista_alumnos = list(alumnos.find())
    lista_materias = list(materias.find())

    return render_template(
        "panel_maestro.html",
        alumnos=lista_alumnos,
        materias=lista_materias,
        maestro=nombre_maestro
    )


# CAPTURAR CALIFICACIONES
@maestro_bp.route("/capturar_calificaciones", methods=["POST"])
def capturar_calificaciones():

    if "rol" not in session or session["rol"] != "maestro":
        return redirect("/")

    alumno = request.form.get("alumno")
    materia = request.form.get("materia")

    cal1 = request.form.get("cal1")
    cal2 = request.form.get("cal2")
    cal3 = request.form.get("cal3")

    alumnos.update_one(
        {"nombre": alumno},
        {
            "$push": {
                "calificaciones": {
                    "materia": materia,
                    "cal1": cal1,
                    "cal2": cal2,
                    "cal3": cal3
                }
            }
        }
    )

    return redirect("/panel_maestro")