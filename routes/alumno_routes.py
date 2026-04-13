from flask import Blueprint, render_template, session, redirect
from database.mongo import alumnos

alumno_bp = Blueprint("alumno", __name__)


def verificar_alumno():
    return "rol" in session and session["rol"] == "alumno"


@alumno_bp.route("/panel_alumno")
def panel_alumno():

    if not verificar_alumno():
        return redirect("/")

    alumno = alumnos.find_one({"nombre": session["usuario"]})

    return render_template(
        "panel_alumno.html",
        alumno=alumno
    )