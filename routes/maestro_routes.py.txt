from flask import Blueprint, render_template, session, redirect
from database.mongo import alumnos

maestro_bp = Blueprint("maestro", __name__, url_prefix="/maestro")

@maestro_bp.route("/dashboard")
def dashboard():

    if session.get("rol") != "maestro":
        return redirect("/")

    lista_alumnos = list(alumnos.find())

    return render_template(
        "maestro/dashboard.html",
        alumnos=lista_alumnos
    )