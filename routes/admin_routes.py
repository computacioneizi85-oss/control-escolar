from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId
import base64

from database.mongo import alumnos, grupos, materias, maestros, reportes, configuracion, horarios, citatorios
from pdf.generador import generar_kardex, generar_boleta, generar_reporte_pdf, generar_citatorio_pdf

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# =========================
# VERIFICAR ADMIN
# =========================

def verificar_admin():
    return "rol" in session and session["rol"] == "admin"


# =========================
# DASHBOARD
# =========================

@admin_bp.route("/")
def admin_dashboard():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "admin.html",
        alumnos=list(alumnos.find()),
        grupos=list(grupos.find()),
        maestros=list(maestros.find()),
        reportes=list(reportes.find()),
        total_alumnos=alumnos.count_documents({}),
        total_maestros=maestros.count_documents({}),
        total_reportes=reportes.count_documents({})
    )


# =========================
# ACTIVAR TRIMESTRE
# =========================

@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    configuracion.update_one(
        {"tipo": "trimestre"},
        {"$set": {
            "trimestre": request.form.get("trimestre"),
            "estado": request.form.get("estado")
        }},
        upsert=True
    )

    return redirect(url_for("admin.admin_dashboard"))


# =========================
# ALUMNOS
# =========================

@admin_bp.route("/alumnos")
def ver_alumnos():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

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
        return redirect(url_for("auth.login"))

    foto = request.files.get("foto")
    foto_base64 = ""

    if foto and foto.filename != "":
        foto_base64 = base64.b64encode(foto.read()).decode("utf-8")

    alumnos.insert_one({
        "nombre": request.form.get("nombre"),
        "grupo": request.form.get("grupo"),
        "foto": foto_base64,
        "calificaciones": [],
        "asistencias": []
    })

    return redirect(url_for("admin.ver_alumnos"))


# =========================
# KARDEX
# =========================

@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):

    pdf = generar_kardex(nombre)
    pdf.seek(0)

    return send_file(pdf, mimetype="application/pdf", as_attachment=True)


# =========================
# BOLETA
# =========================

@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):

    pdf = generar_boleta(nombre)
    pdf.seek(0)

    return send_file(pdf, mimetype="application/pdf", as_attachment=True)


# =========================
# 🔥 PDF REPORTES (CORREGIDO)
# =========================

@admin_bp.route("/aprobar_reporte/<string:id>")
def aprobar_reporte(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        reporte = reportes.find_one({"_id": ObjectId(id)})
    except:
        return "ID inválido"

    if not reporte:
        return "Reporte no encontrado"

    pdf = generar_reporte_pdf(reporte)
    pdf.seek(0)

    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=False
    )


# =========================
# 🔥 PDF CITATORIOS (CORREGIDO)
# =========================

@admin_bp.route("/generar_citatorio/<string:id>")
def generar_citatorio(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        citatorio = citatorios.find_one({"_id": ObjectId(id)})
    except:
        return "ID inválido"

    if not citatorio:
        return "Citatorio no encontrado"

    pdf = generar_citatorio_pdf(citatorio)
    pdf.seek(0)

    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=False
    )


# =========================
# CREAR CITATORIO
# =========================

@admin_bp.route("/crear_citatorio", methods=["POST"])
def crear_citatorio():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    citatorios.insert_one({
        "alumno": request.form.get("alumno"),
        "grupo": request.form.get("grupo"),
        "motivo": request.form.get("motivo"),
        "fecha_cita": request.form.get("fecha"),
        "hora": request.form.get("hora"),
        "estado": "pendiente"
    })

    return redirect(url_for("admin.ver_citatorios"))


# =========================
# SUBMENÚS
# =========================

@admin_bp.route("/reportes")
def ver_reportes():
    return render_template(
        "reportes_admin.html",
        reportes=list(reportes.find())
    )


@admin_bp.route("/citatorios")
def ver_citatorios():
    return render_template(
        "citatorios.html",
        citatorios=list(citatorios.find()),
        alumnos=list(alumnos.find())
    )