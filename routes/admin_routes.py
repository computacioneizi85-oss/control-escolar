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


# =========================
# ASISTENCIAS
# =========================

@admin_bp.route("/asistencias")
def ver_asistencias():

    if not verificar_admin():
        return redirect("/")

    return render_template(
        "asistencias_admin.html",
        alumnos=list(alumnos.find()),
        grupos=list(grupos.find()),
        maestros=list(maestros.find())
    )


# =========================
# GRUPOS
# =========================

@admin_bp.route("/grupos")
def ver_grupos():

    if not verificar_admin():
        return redirect("/")

    return render_template("grupos.html", grupos=list(grupos.find()))


# =========================
# MATERIAS
# =========================

@admin_bp.route("/materias")
def ver_materias():

    if not verificar_admin():
        return redirect("/")

    return render_template(
        "materias.html",
        materias=list(materias.find()),
        grupos=list(grupos.find())
    )


# =========================
# HORARIOS
# =========================

@admin_bp.route("/horarios")
def ver_horarios():

    if not verificar_admin():
        return redirect("/")

    return render_template(
        "horarios.html",
        horarios=list(horarios.find()),
        grupos=list(grupos.find()),
        materias=list(materias.find()),
        maestros=list(maestros.find())
    )


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

    try:
        reporte = reportes.find_one({"_id": ObjectId(id)})
    except:
        return redirect("/reportes")

    if not reporte:
        return redirect("/reportes")

    pdf_buffer = generar_reporte_pdf(reporte)

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="reporte.pdf"
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
        as_attachment=True
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
        as_attachment=True
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

    try:
        citatorio = citatorios.find_one({"_id": ObjectId(id)})
    except:
        return redirect("/citatorios")

    if not citatorio:
        return redirect("/citatorios")

    pdf_buffer = generar_citatorio_pdf(citatorio)

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="citatorio.pdf"
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