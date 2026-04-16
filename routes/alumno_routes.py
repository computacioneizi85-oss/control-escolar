from flask import Blueprint, render_template, session, redirect
from database.mongo import alumnos, avisos

alumno_bp = Blueprint("alumno", __name__)


def verificar_alumno():
    return session.get("rol") == "alumno"


@alumno_bp.route("/panel_alumno")
def panel_alumno():

    if not verificar_alumno():
        return redirect("/")

    alumno = alumnos.find_one({"usuario": session.get("usuario")})

    if not alumno:
        return "Alumno no encontrado"

    return render_template("panel_alumno.html", alumno=alumno)


@alumno_bp.route("/avisos_alumno")
def ver_avisos_alumno():

    if not verificar_alumno():
        return redirect("/")

    alumno = alumnos.find_one({"usuario": session.get("usuario")})

    lista_avisos = list(avisos.find({
        "$or": [
            {"tipo": "alumno"},
            {"tipo": "grupo", "grupo": alumno.get("grupo")}
        ]
    }))

    return render_template("avisos_alumno.html", avisos=lista_avisos)