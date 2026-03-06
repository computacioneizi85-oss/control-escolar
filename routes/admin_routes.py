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

@admin_bp.route("/crear_alumno", methods=["POST"])
def crear_alumno():

    nombre = request.form.get("nombre")
    grupo = request.form.get("grupo")

    alumnos.insert_one({

        "nombre": nombre,
        "grupo": grupo

    })

    return redirect("/alumnos")

@admin_bp.route("/alumnos")
def ver_alumnos():

    if "rol" not in session:
        return redirect("/")

    lista_alumnos = list(alumnos.find())
    lista_grupos = list(grupos.find())

    return render_template(
        "alumnos.html",
        alumnos=lista_alumnos,
        grupos=lista_grupos
    )

from bson.objectid import ObjectId


@admin_bp.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):

    alumnos.delete_one({

        "_id": ObjectId(id)

    })

    return redirect("/alumnos")

@admin_bp.route("/editar_alumno/<id>")
def editar_alumno(id):

    alumno = alumnos.find_one({

        "_id": ObjectId(id)

    })

    lista_grupos = list(grupos.find())

    return render_template(
        "editar_alumno.html",
        alumno=alumno,
        grupos=lista_grupos
    )

@admin_bp.route("/actualizar_alumno/<id>", methods=["POST"])
def actualizar_alumno(id):

    nombre = request.form.get("nombre")
    grupo = request.form.get("grupo")

    alumnos.update_one(

        {"_id": ObjectId(id)},

        {"$set": {

            "nombre": nombre,
            "grupo": grupo

        }}

    )

    return redirect("/alumnos")