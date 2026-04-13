from flask import Blueprint, render_template, session, redirect
from database.mongo import alumnos

alumno_bp = Blueprint("alumno", __name__)


def verificar_alumno():
    return session.get("rol") == "alumno"


@alumno_bp.route("/panel_alumno")
def panel_alumno():

    if not verificar_alumno():
        return redirect("/")

    # 🔥 CORREGIDO (usar usuario)
    alumno = alumnos.find_one({"usuario": session["usuario"]})

    if not alumno:
        return "Alumno no encontrado"

    return render_template(
        "panel_alumno.html",
        alumno=alumno
    )