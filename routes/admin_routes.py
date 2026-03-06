from flask import Blueprint, render_template, request, redirect, session, send_file
from bson.objectid import ObjectId

from database.mongo import db
from pdf.generador import generar_kardex, generar_boleta


admin_bp = Blueprint("admin", __name__)


# COLECCIONES

alumnos = db.alumnos
grupos = db.grupos
maestros = db.maestros
materias = db.materias
reportes = db.reportes


# ----------------------------
# DASHBOARD
# ----------------------------

@admin_bp.route("/admin")
def dashboard():

    if "rol" not in session:
        return redirect("/")

    lista_alumnos = list(alumnos.find())
    lista_grupos = list(grupos.find())
    lista_maestros = list(maestros.find())
    lista_reportes = list(reportes.find())

    return render_template(
        "admin.html",
        alumnos=lista_alumnos,
        grupos=lista_grupos,
        maestros=lista_maestros,
        reportes=lista_reportes
    )


# ----------------------------
# VER ALUMNOS
# ----------------------------

@admin_bp.route("/alumnos")
def ver_alumnos():

    lista_alumnos = list(alumnos.find())
    lista_grupos = list(grupos.find())

    return render_template(
        "alumnos.html",
        alumnos=lista_alumnos,
        grupos=lista_grupos
    )


# ----------------------------
# CREAR ALUMNO
# ----------------------------

@admin_bp.route("/crear_alumno", methods=["POST"])
def crear_alumno():

    nombre = request.form.get("nombre")
    grupo = request.form.get("grupo")

    alumnos.insert_one({

        "nombre": nombre,
        "grupo": grupo

    })

    return redirect("/alumnos")


# ----------------------------
# ELIMINAR ALUMNO
# ----------------------------

@admin_bp.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):

    alumnos.delete_one({
        "_id": ObjectId(id)
    })

    return redirect("/alumnos")


# ----------------------------
# EDITAR ALUMNO
# ----------------------------

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


# ----------------------------
# ACTUALIZAR ALUMNO
# ----------------------------

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


# ----------------------------
# VER GRUPOS
# ----------------------------

@admin_bp.route("/grupos")
def ver_grupos():

    lista_grupos = list(grupos.find())

    return render_template(
        "grupos.html",
        grupos=lista_grupos
    )


# ----------------------------
# CREAR GRUPO
# ----------------------------

@admin_bp.route("/crear_grupo", methods=["POST"])
def crear_grupo():

    nombre = request.form.get("nombre")

    grupos.insert_one({

        "nombre": nombre

    })

    return redirect("/grupos")


# ----------------------------
# ELIMINAR GRUPO
# ----------------------------

@admin_bp.route("/eliminar_grupo/<id>")
def eliminar_grupo(id):

    grupos.delete_one({

        "_id": ObjectId(id)

    })

    return redirect("/grupos")


# ----------------------------
# VER MATERIAS
# ----------------------------

@admin_bp.route("/materias")
def ver_materias():

    lista_materias = list(materias.find())
    lista_grupos = list(grupos.find())

    return render_template(
        "materias.html",
        materias=lista_materias,
        grupos=lista_grupos
    )


# ----------------------------
# CREAR MATERIA
# ----------------------------

@admin_bp.route("/crear_materia", methods=["POST"])
def crear_materia():

    nombre = request.form.get("nombre")
    grupo = request.form.get("grupo")

    materias.insert_one({

        "nombre": nombre,
        "grupo": grupo

    })

    return redirect("/materias")


# ----------------------------
# ELIMINAR MATERIA
# ----------------------------

@admin_bp.route("/eliminar_materia/<id>")
def eliminar_materia(id):

    materias.delete_one({

        "_id": ObjectId(id)

    })

    return redirect("/materias")


# ----------------------------
# GENERAR KARDEX PDF
# ----------------------------

@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):

    archivo = generar_kardex(nombre)

    return send_file(
        archivo,
        as_attachment=True
    )


# ----------------------------
# GENERAR BOLETA PDF
# ----------------------------

@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):

    archivo = generar_boleta(nombre)

    return send_file(
        archivo,
        as_attachment=True
    )