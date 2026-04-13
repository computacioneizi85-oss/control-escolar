from flask import Blueprint, render_template, session, redirect, request
from database.mongo import alumnos

padre_bp = Blueprint("padre", __name__)


def verificar_padre():
    return "rol" in session and session["rol"] == "padre"


@padre_bp.route("/panel_padre")
def panel_padre():

    if not verificar_padre():
        return redirect("/")

    alumno = alumnos.find_one({"nombre": session["alumno"]})

    return render_template(
        "panel_padre.html",
        alumno=alumno
    )


@padre_bp.route("/enterado", methods=["POST"])
def marcar_enterado():

    if not verificar_padre():
        return redirect("/")

    alumno_nombre = request.form.get("alumno")
    materia = request.form.get("materia")

    alumnos.update_one(
        {
            "nombre": alumno_nombre,
            "calificaciones.materia": materia
        },
        {
            "$set": {
                "calificaciones.$.enterado": True
            }
        }
    )

    return redirect("/panel_padre")