from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

from database.mongo import (
    alumnos, grupos, materias, maestros,
    reportes, configuracion, horarios,
    citatorios, padres, avisos
)

from pdf.generador import (
    generar_kardex, generar_boleta,
    generar_reporte_pdf, generar_citatorio_pdf
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def verificar_admin():
    return session.get("rol") == "admin"


# ================= DASHBOARD =================
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
        citatorios=list(citatorios.find()),
        alumnos_riesgo=[],
        ultimos_reportes=[],
        total_asistencias=0,
        total_faltas=0
    )


# ================= REGISTRO COMPLETO =================
@admin_bp.route("/registro_completo_alumno", methods=["POST"])
def registro_completo_alumno():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        foto = request.files.get("foto")
        ruta_foto = ""

        if foto and foto.filename:
            carpeta = "static/fotos"
            os.makedirs(carpeta, exist_ok=True)
            ruta_foto = f"{carpeta}/{foto.filename}"
            foto.save(ruta_foto)

        alumnos.insert_one({
            "nombre": request.form.get("nombre") or "",
            "curp": request.form.get("curp") or "",
            "sexo": request.form.get("sexo") or "",
            "fecha_nacimiento": request.form.get("fecha_nacimiento") or "",
            "telefono": request.form.get("telefono") or "",
            "direccion": request.form.get("direccion") or "",
            "escuela_procedencia": request.form.get("escuela") or "",
            "promedio": request.form.get("promedio") or "",
            "afecciones": request.form.get("afecciones") or "",
            "padre_nombre": request.form.get("padre_nombre") or "",
            "padre_telefono": request.form.get("padre_telefono") or "",
            "padre_correo": request.form.get("padre_correo") or "",
            "grupo": request.form.get("grupo") or "",
            "foto": ruta_foto,
            "calificaciones": [],
            "asistencias": []
        })

        return redirect("/admin")

    except Exception as e:
        return f"ERROR REGISTRO: {str(e)}"


# ================= EXPEDIENTE =================
@admin_bp.route("/expediente/<id>")
def expediente(id):
    alumno = alumnos.find_one({"_id": ObjectId(id)})
    return render_template("expediente.html", alumno=alumno)


# ================= EDITAR =================
@admin_bp.route("/editar_expediente/<id>")
def editar_expediente(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumno = alumnos.find_one({"_id": ObjectId(id)})
    return render_template("editar_expediente.html", alumno=alumno)


@admin_bp.route("/actualizar_expediente/<id>", methods=["POST"])
def actualizar_expediente(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        update_data = {
            "nombre": request.form.get("nombre"),
            "curp": request.form.get("curp"),
            "sexo": request.form.get("sexo"),
            "fecha_nacimiento": request.form.get("fecha_nacimiento"),
            "telefono": request.form.get("telefono"),
            "direccion": request.form.get("direccion"),
            "escuela_procedencia": request.form.get("escuela"),
            "promedio": request.form.get("promedio"),
            "afecciones": request.form.get("afecciones"),
            "padre_nombre": request.form.get("padre_nombre"),
            "padre_telefono": request.form.get("padre_telefono"),
            "padre_correo": request.form.get("padre_correo"),
            "grupo": request.form.get("grupo")
        }

        foto = request.files.get("foto")

        if foto and foto.filename:
            carpeta = "static/fotos"
            os.makedirs(carpeta, exist_ok=True)
            ruta_foto = f"{carpeta}/{foto.filename}"
            foto.save(ruta_foto)
            update_data["foto"] = ruta_foto

        alumnos.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )

        return redirect(f"/admin/expediente/{id}")

    except Exception as e:
        return f"ERROR ACTUALIZAR: {str(e)}"


# ================= PDF EXPEDIENTE =================
@admin_bp.route("/expediente_pdf/<id>")
def expediente_pdf(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from io import BytesIO

    alumno = alumnos.find_one({"_id": ObjectId(id)})

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    contenido = []
    contenido.append(Paragraph("EXPEDIENTE DEL ALUMNO", styles["Title"]))
    contenido.append(Spacer(1, 12))

    for campo in [
        "nombre","curp","sexo","fecha_nacimiento","telefono",
        "direccion","escuela_procedencia","promedio","afecciones",
        "padre_nombre","padre_telefono","padre_correo","grupo"
    ]:
        contenido.append(
            Paragraph(f"<b>{campo}:</b> {alumno.get(campo,'')}", styles["Normal"])
        )

    doc.build(contenido)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="expediente.pdf",
        mimetype="application/pdf"
    )