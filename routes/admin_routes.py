from flask import Blueprint, render_template, request, redirect, session
from database.mongo import alumnos, grupos

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin")
def admin_panel():

    if "rol" not in session:
        return redirect("/")

    if session["rol"] != "admin":
        return redirect("/")

    lista_alumnos = list(alumnos.find())
    lista_grupos = list(grupos.find())

    return render_template(
        "admin.html",
        alumnos=lista_alumnos,
        grupos=lista_grupos
    )


# =========================
# Crear grupo
# =========================

@admin_bp.route("/crear_grupo", methods=["POST"])
def crear_grupo():

    nombre = request.form.get("grupo")

    grupos.insert_one({
        "nombre": nombre
    })

    return redirect("/admin")


# =========================
# Crear alumno
# =========================

@admin_bp.route("/crear_alumno", methods=["POST"])
def crear_alumno():

    nombre = request.form.get("nombre")
    grupo = request.form.get("grupo")

    alumnos.insert_one({
        "nombre": nombre,
        "grupo": grupo
    })

    return redirect("/admin")