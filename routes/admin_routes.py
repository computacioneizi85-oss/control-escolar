from flask import Blueprint, render_template, request, redirect, session, send_file
from bson.objectid import ObjectId

import os
from werkzeug.utils import secure_filename

from database.mongo import (
    alumnos,
    grupos,
    materias,
    maestros,
    reportes,
    configuracion
)

from pdf.generador import generar_kardex, generar_boleta


admin_bp = Blueprint("admin", __name__)


# =========================
# DASHBOARD
# =========================

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


# =========================
# ALUMNOS
# =========================

@admin_bp.route("/alumnos")
def ver_alumnos():

    lista_alumnos = list(alumnos.find())
    lista_grupos = list(grupos.find())

    return render_template(
        "alumnos.html",
        alumnos=lista_alumnos,
        grupos=lista_grupos
    )


@admin_bp.route("/crear_alumno", methods=["POST"])
def crear_alumno():

    nombre = request.form.get("nombre")
    grupo = request.form.get("grupo")

    alumnos.insert_one({
        "nombre": nombre,
        "grupo": grupo
    })

    return redirect("/alumnos")


@admin_bp.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):

    alumnos.delete_one({
        "_id": ObjectId(id)
    })

    return redirect("/alumnos")


# =========================
# MAESTROS
# =========================

@admin_bp.route("/maestros")
def ver_maestros():

    lista_maestros = list(maestros.find())

    return render_template(
        "maestros.html",
        maestros=lista_maestros
    )


@admin_bp.route("/crear_maestro", methods=["POST"])
def crear_maestro():

    nombre = request.form.get("nombre")
    usuario = request.form.get("usuario")
    password = request.form.get("password")

    maestros.insert_one({
        "nombre": nombre,
        "usuario": usuario,
        "password": password
    })

    return redirect("/maestros")


@admin_bp.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):

    maestros.delete_one({
        "_id": ObjectId(id)
    })

    return redirect("/maestros")


# =========================
# GRUPOS
# =========================

@admin_bp.route("/grupos")
def ver_grupos():

    lista_grupos = list(grupos.find())

    return render_template(
        "grupos.html",
        grupos=lista_grupos
    )


@admin_bp.route("/crear_grupo", methods=["POST"])
def crear_grupo():

    nombre = request.form.get("nombre")

    grupos.insert_one({
        "nombre": nombre
    })

    return redirect("/grupos")


@admin_bp.route("/eliminar_grupo/<id>")
def eliminar_grupo(id):

    grupos.delete_one({
        "_id": ObjectId(id)
    })

    return redirect("/grupos")


# =========================
# MATERIAS
# =========================

@admin_bp.route("/materias")
def ver_materias():

    lista_materias = list(materias.find())
    lista_grupos = list(grupos.find())

    return render_template(
        "materias.html",
        materias=lista_materias,
        grupos=lista_grupos
    )


@admin_bp.route("/crear_materia", methods=["POST"])
def crear_materia():

    nombre = request.form.get("nombre")
    grupo = request.form.get("grupo")

    materias.insert_one({
        "nombre": nombre,
        "grupo": grupo
    })

    return redirect("/materias")


@admin_bp.route("/eliminar_materia/<id>")
def eliminar_materia(id):

    materias.delete_one({
        "_id": ObjectId(id)
    })

    return redirect("/materias")


# =========================
# REPORTES DISCIPLINARIOS
# =========================

@admin_bp.route("/reportes")
def ver_reportes():

    lista_reportes = list(reportes.find())

    return render_template(
        "reportes_admin.html",
        reportes=lista_reportes
    )


# =========================
# CONFIGURACION ESCOLAR
# =========================

@admin_bp.route("/configuracion")
def ver_configuracion():

    datos = configuracion.find_one()

    return render_template(
        "configuracion.html",
        config=datos
    )


@admin_bp.route("/guardar_configuracion", methods=["POST"])
def guardar_configuracion():

    escuela = request.form.get("escuela")
    ciclo = request.form.get("ciclo")
    director = request.form.get("director")
    direccion = request.form.get("direccion")

    archivo = request.files.get("escudo")

    escudo_path = None

    if archivo and archivo.filename != "":

        nombre_archivo = secure_filename(archivo.filename)

        carpeta = "static/uploads"

        if not os.path.exists(carpeta):
            os.makedirs(carpeta)

        ruta = os.path.join(carpeta, nombre_archivo)

        archivo.save(ruta)

        escudo_path = ruta

    datos = {
        "escuela": escuela,
        "ciclo": ciclo,
        "director": director,
        "direccion": direccion
    }

    if escudo_path:
        datos["escudo"] = escudo_path

    configuracion.update_one(
        {},
        {"$set": datos},
        upsert=True
    )

    return redirect("/configuracion")


# =========================
# GENERAR KARDEX
# =========================

@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):

    archivo = generar_kardex(nombre)

    return send_file(
        archivo,
        as_attachment=True
    )


# =========================
# GENERAR BOLETA
# =========================

@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):

    archivo = generar_boleta(nombre)

    return send_file(
        archivo,
        as_attachment=True
    )