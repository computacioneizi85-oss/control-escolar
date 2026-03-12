from flask import Blueprint, render_template, request, redirect, session, send_file
from bson.objectid import ObjectId
import os
from werkzeug.utils import secure_filename

from database.mongo import alumnos, grupos, materias, maestros, reportes, configuracion, horarios, citatorios
from pdf.generador import generar_kardex, generar_boleta, generar_reporte_pdf, generar_citatorio_pdf


admin_bp = Blueprint("admin", __name__)


# =========================
# VERIFICAR ADMIN
# =========================

def verificar_admin():

    if "rol" not in session:
        return False

    if session["rol"] != "admin":
        return False

    return True


# =========================
# DASHBOARD
# =========================

@admin_bp.route("/admin")
def admin_dashboard():

    if not verificar_admin():
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
# REPORTES DISCIPLINARIOS
# =========================

@admin_bp.route("/reportes")
def ver_reportes():

    if not verificar_admin():
        return redirect("/")

    lista_reportes = list(reportes.find())

    return render_template(
        "reportes_admin.html",
        reportes=lista_reportes
    )


@admin_bp.route("/aprobar_reporte/<id>")
def aprobar_reporte(id):

    if not verificar_admin():
        return redirect("/")

    reporte = reportes.find_one({"_id": ObjectId(id)})

    if not reporte:
        return redirect("/reportes")

    ruta_pdf = generar_reporte_pdf(reporte)

    reportes.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "estatus": "aprobado",
                "pdf": ruta_pdf
            }
        }
    )

    return send_file(
        ruta_pdf,
        as_attachment=True
    )


# =========================
# GENERAR KARDEX
# =========================

@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):

    if not verificar_admin():
        return redirect("/")

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

    if not verificar_admin():
        return redirect("/")

    archivo = generar_boleta(nombre)

    return send_file(
        archivo,
        as_attachment=True
    )


# =========================
# CITATORIOS
# =========================

@admin_bp.route("/citatorios")
def ver_citatorios():

    if not verificar_admin():
        return redirect("/")

    lista_citatorios = list(citatorios.find())
    lista_alumnos = list(alumnos.find())

    return render_template(
        "citatorios.html",
        citatorios=lista_citatorios,
        alumnos=lista_alumnos
    )


@admin_bp.route("/generar_citatorio/<id>")
def generar_citatorio(id):

    if not verificar_admin():
        return redirect("/")

    citatorio = citatorios.find_one({"_id": ObjectId(id)})

    if not citatorio:
        return redirect("/citatorios")

    ruta_pdf = generar_citatorio_pdf(citatorio)

    citatorios.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"pdf": ruta_pdf}}
    )

    return send_file(
        ruta_pdf,
        as_attachment=True
    )