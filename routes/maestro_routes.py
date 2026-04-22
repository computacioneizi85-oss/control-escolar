from flask import Blueprint, render_template, request, redirect, session, url_for, send_file
from bson.objectid import ObjectId
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from database.mongo import alumnos, maestros, horarios, configuracion, citatorios, avisos, reportes
from pdf.generador import generar_citatorio_pdf

maestro_bp = Blueprint("maestro", __name__)


# ================= SEGURIDAD =================
def verificar_maestro():
    return session.get("rol") == "maestro"


# ================= PANEL =================
@maestro_bp.route("/panel_maestro")
def panel_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}

    materias = maestro.get("materias", [])
    grupos = maestro.get("grupos", [])

    lista_alumnos = list(alumnos.find({"grupo": {"$in": grupos}}))

    return render_template(
        "panel_maestro.html",
        alumnos=lista_alumnos,
        grupos=grupos,
        materias=materias
    )


# ================= AVISOS =================
@maestro_bp.route("/avisos_maestro")
def avisos_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}

    return render_template(
        "avisos_maestro.html",
        grupos=maestro.get("grupos", [])
    )


@maestro_bp.route("/crear_aviso_maestro", methods=["POST"])
def crear_aviso_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    avisos.insert_one({
        "tipo": "grupo",
        "grupo": request.form.get("grupo"),
        "mensaje": request.form.get("mensaje"),
        "fecha": datetime.now()
    })

    return redirect("/avisos_maestro")


# ================= CITATORIOS =================
@maestro_bp.route("/citatorios")
def ver_citatorios_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}
    grupos = maestro.get("grupos", [])

    return render_template(
        "citatorios_maestro.html",
        citatorios=list(citatorios.find({"grupo": {"$in": grupos}})),
        alumnos=list(alumnos.find({"grupo": {"$in": grupos}}))
    )


@maestro_bp.route("/crear_citatorio", methods=["POST"])
def crear_citatorio_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    citatorios.insert_one({
        "alumno": request.form.get("alumno"),
        "grupo": request.form.get("grupo"),
        "motivo": request.form.get("motivo"),
        "fecha_cita": request.form.get("fecha"),
        "hora": request.form.get("hora"),
        "estatus": "pendiente",
        "maestro": session.get("usuario")
    })

    return redirect("/citatorios")


@maestro_bp.route("/generar_citatorio/<id>")
def generar_citatorio_maestro(id):

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    citatorio = citatorios.find_one({"_id": ObjectId(id)})

    pdf = generar_citatorio_pdf(citatorio)
    pdf.seek(0)

    return send_file(pdf, as_attachment=True, download_name="citatorio.pdf")


# ================= EVALUACIONES =================
@maestro_bp.route("/guardar_calificaciones_ajax", methods=["POST"])
def guardar_calificaciones_ajax():

    if not verificar_maestro():
        return {"status": "error"}

    alumnos.update_one(
        {"nombre": request.form.get("alumno")},
        {
            "$push": {
                "calificaciones": {
                    "materia": request.form.get("materia"),
                    "calificacion": float(request.form.get("cal1") or 0),
                    "trimestre": request.form.get("trimestre")
                }
            }
        }
    )

    return {"status": "ok"}


# ================= ASISTENCIA =================
@maestro_bp.route("/guardar_asistencia_ajax", methods=["POST"])
def guardar_asistencia_ajax():

    if not verificar_maestro():
        return {"status": "error"}

    alumnos.update_one(
        {"nombre": request.form.get("alumno")},
        {
            "$push": {
                "asistencias": {
                    "fecha": request.form.get("fecha"),
                    "estado": request.form.get("estado")
                }
            }
        }
    )

    return {"status": "ok"}


# ================= REPORTES =================
@maestro_bp.route("/crear_reporte", methods=["POST"])
def crear_reporte():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    reportes.insert_one({
        "alumno": request.form.get("alumno"),
        "grupo": request.form.get("grupo"),
        "comentario": request.form.get("comentario"),
        "fecha": request.form.get("fecha"),
        "maestro": session.get("usuario"),
        "estatus": "pendiente"
    })

    return redirect("/panel_maestro")


@maestro_bp.route("/enviar_reportes_maestro", methods=["POST"])
def enviar_reportes_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    reportes.update_many(
        {"maestro": session.get("usuario")},
        {"$set": {"estatus": "enviado"}}
    )

    return redirect("/panel_maestro")