from flask import Blueprint, render_template, session, redirect, request
from bson.objectid import ObjectId
from datetime import datetime
from flask import send_file
from pdf.generador import generar_citatorio_pdf

from database.mongo import (
    alumnos,
    citatorios,
    avisos,
    reportes
)

padre_bp = Blueprint("padre", __name__)


# ================= SEGURIDAD =================
def verificar_padre():
    return session.get("rol") == "padre"


# ================= PANEL =================
@padre_bp.route("/panel_padre")
def panel_padre():

    if not verificar_padre():
        return redirect(url_for("auth.login"))

    alumno_nombre = session.get("alumno")

    alumno = alumnos.find_one({"nombre": alumno_nombre})

    lista_citatorios = list(
        citatorios.find({
            "alumno": alumno_nombre,
            "visible_padre": True
        })
    )

    lista_reportes = list(
        reportes.find({
            "alumno": alumno_nombre,
            "visible_padre": True
        })
    )

    return render_template(
        "panel_padre.html",
        alumno=alumno,
        citatorios=lista_citatorios,
        reportes=lista_reportes
    )


# ================= AVISOS PADRE =================
@padre_bp.route("/avisos_padre")  # 🔥 ruta única
def ver_avisos_padre():

    if not verificar_padre():
        return redirect(url_for("auth.login"))

    alumno = alumnos.find_one({"nombre": session.get("alumno")})

    lista_avisos = list(avisos.find({
        "$or": [
            {"tipo": "padre"},
            {"tipo": "grupo", "grupo": alumno.get("grupo")}
        ]
    }))

    return render_template(
        "avisos_padre.html",
        avisos=lista_avisos
    )


# ================= ENTERADO CALIFICACIONES =================
@padre_bp.route("/enterado", methods=["POST"])
def marcar_enterado():

    if not verificar_padre():
        return redirect(url_for("auth.login"))

    alumnos.update_one(
        {
            "nombre": request.form.get("alumno"),
            "calificaciones.materia": request.form.get("materia")
        },
        {
            "$set": {"calificaciones.$.enterado": True}
        }
    )

    return redirect("/panel_padre")


# ================= ENTERADO CITATORIOS =================
@padre_bp.route("/enterado_citatorio/<id>")
def enterado_citatorio(id):

    if not verificar_padre():
        return redirect(url_for("auth.login"))

    citatorios.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "enterado": True,
                "fecha_enterado": datetime.now()
            }
        }
    )

    return redirect("/panel_padre")

# ================= ENTERADO REPORTE =================
@padre_bp.route("/enterado_reporte/<id>")
def enterado_reporte(id):

    if not verificar_padre():
        return redirect(url_for("auth.login"))

    reportes.update_one(
        {
            "_id": ObjectId(id)
        },
        {
            "$set": {
                "enterado": True,
                "fecha_enterado": datetime.now()
            }
        }
    )

    return redirect("/panel_padre")

# ================= PDF CITATORIO =================
@padre_bp.route("/citatorio_pdf_padre/<id>")
def citatorio_pdf_padre(id):

    if not verificar_padre():
        return redirect(url_for("auth.login"))

    citatorio = citatorios.find_one({
        "_id": ObjectId(id)
    })

    if not citatorio:
        return redirect("/panel_padre")

    pdf = generar_citatorio_pdf(citatorio)

    return send_file(
        pdf,
        download_name="citatorio.pdf",
        as_attachment=False,
        mimetype="application/pdf"
    )