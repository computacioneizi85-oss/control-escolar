from flask import Blueprint, render_template, request, redirect, session, send_file
from bson.objectid import ObjectId
import os
import uuid

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash

from database.mongo import alumnos, grupos, materias, maestros, reportes, configuracion, horarios, citatorios
from pdf.generador import generar_kardex, generar_boleta, generar_reporte_pdf, generar_citatorio_pdf

admin_bp = Blueprint("admin", __name__)


# =========================
# VERIFICAR ADMIN
# =========================

def verificar_admin():
    return "rol" in session and session["rol"] == "admin"


# =========================
# DASHBOARD
# =========================

@admin_bp.route("/admin")
def admin_dashboard():

    if not verificar_admin():
        return redirect("/")

    return render_template(
        "admin.html",
        alumnos=list(alumnos.find()),
        grupos=list(grupos.find()),
        maestros=list(maestros.find()),
        reportes=list(reportes.find())
    )


# =========================
# ALUMNOS
# =========================

@admin_bp.route("/alumnos")
def ver_alumnos():

    if not verificar_admin():
        return redirect("/")

    return render_template(
        "alumnos.html",
        alumnos=list(alumnos.find()),
        grupos=list(grupos.find()),
        maestros=list(maestros.find())
    )


# =========================
# CREAR ALUMNO
# =========================

@admin_bp.route("/crear_alumno", methods=["POST"])
def crear_alumno():

    if not verificar_admin():
        return redirect("/")

    nombre = request.form.get("nombre")
    grupo = request.form.get("grupo")

    if not nombre or not grupo:
        return redirect("/alumnos")

    foto = request.files.get("foto")

    foto_ruta = ""

    if foto and foto.filename != "":

        extensiones = ["jpg", "jpeg", "png"]

        if "." in foto.filename:
            ext = foto.filename.rsplit(".", 1)[1].lower()

            if ext in extensiones:

                nombre_archivo = str(uuid.uuid4()) + "_" + secure_filename(foto.filename)

                carpeta = "static/uploads/alumnos"

                if not os.path.exists(carpeta):
                    os.makedirs(carpeta)

                ruta = os.path.join(carpeta, nombre_archivo)

                foto.save(ruta)

                foto_ruta = ruta.replace("\\", "/")

    alumnos.insert_one({
        "nombre": nombre,
        "grupo": grupo,
        "foto": foto_ruta,
        "calificaciones": [],
        "asistencias": []
    })

    return redirect("/alumnos")


# =========================
# CAMBIAR FOTO
# =========================

@admin_bp.route("/subir_foto_alumno/<id>", methods=["POST"])
def subir_foto_alumno(id):

    if not verificar_admin():
        return redirect("/")

    foto = request.files.get("foto")

    if foto and foto.filename != "":

        nombre_archivo = str(uuid.uuid4()) + "_" + secure_filename(foto.filename)

        carpeta = "static/uploads/alumnos"

        if not os.path.exists(carpeta):
            os.makedirs(carpeta)

        ruta = os.path.join(carpeta, nombre_archivo)

        foto.save(ruta)

        alumnos.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"foto": ruta.replace("\\", "/")}}
        )

    return redirect("/alumnos")


# =========================
# MAESTROS
# =========================

@admin_bp.route("/maestros")
def ver_maestros():

    if not verificar_admin():
        return redirect("/")

    return render_template(
        "maestros.html",
        maestros=list(maestros.find()),
        grupos=list(grupos.find())
    )


@admin_bp.route("/crear_maestro", methods=["POST"])
def crear_maestro():

    if not verificar_admin():
        return redirect("/")

    password_hash = generate_password_hash(request.form.get("password"))

    maestros.insert_one({
        "nombre": request.form.get("nombre"),
        "usuario": request.form.get("usuario"),
        "password": password_hash,
        "grupos": [],
        "materias": []
    })

    return redirect("/maestros")


# =========================
# REPORTES
# =========================

@admin_bp.route("/reportes")
def ver_reportes():

    if not verificar_admin():
        return redirect("/")

    return render_template(
        "reportes_admin.html",
        reportes=list(reportes.find())
    )


@admin_bp.route("/aprobar_reporte/<id>")
def aprobar_reporte(id):

    if not verificar_admin():
        return redirect("/")

    reporte = reportes.find_one({"_id": ObjectId(id)})

    if not reporte:
        return redirect("/reportes")

    pdf_buffer = generar_reporte_pdf(reporte)

    reportes.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estatus": "aprobado"}}
    )

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"reporte_{reporte.get('alumno','')}.pdf"
    )


# =========================
# KARDEX
# =========================

@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):

    if not verificar_admin():
        return redirect("/")

    return send_file(
        generar_kardex(nombre),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"kardex_{nombre}.pdf"
    )


# =========================
# BOLETA
# =========================

@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):

    if not verificar_admin():
        return redirect("/")

    return send_file(
        generar_boleta(nombre),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"boleta_{nombre}.pdf"
    )


# =========================
# CITATORIOS
# =========================

@admin_bp.route("/citatorios")
def ver_citatorios():

    if not verificar_admin():
        return redirect("/")

    return render_template(
        "citatorios.html",
        citatorios=list(citatorios.find()),
        alumnos=list(alumnos.find())
    )


@admin_bp.route("/generar_citatorio/<id>")
def generar_citatorio(id):

    if not verificar_admin():
        return redirect("/")

    citatorio = citatorios.find_one({"_id": ObjectId(id)})

    if not citatorio:
        return redirect("/citatorios")

    pdf_buffer = generar_citatorio_pdf(citatorio)

    citatorios.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estado": "generado"}}
    )

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"citatorio_{citatorio.get('alumno','')}.pdf"
    )


# =========================
# CONFIGURACION
# =========================

@admin_bp.route("/configuracion")
def ver_configuracion():

    if not verificar_admin():
        return redirect("/")

    return render_template(
        "configuracion.html",
        config=configuracion.find_one()
    )