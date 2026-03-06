from flask import Blueprint, render_template, session, redirect, request
from database.mongo import alumnos

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/dashboard")
def admin_dashboard():

    if "rol" not in session:
        return redirect("/")

    if session["rol"] != "admin":
        return redirect("/")

    lista_alumnos = list(alumnos.find())

    return render_template("admin.html", alumnos=lista_alumnos)


@admin_bp.route("/admin/crear_alumno", methods=["POST"])
def crear_alumno():

    nombre = request.form.get("nombre")
    grupo = request.form.get("grupo")

    alumnos.insert_one({
        "nombre": nombre,
        "grupo": grupo
    })

    return redirect("/admin/dashboard")