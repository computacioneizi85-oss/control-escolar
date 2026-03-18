from flask import Blueprint, render_template, request, redirect, session, send_file
from bson.objectid import ObjectId
import base64

from werkzeug.security import generate_password_hash

from database.mongo import alumnos, grupos, materias, maestros, reportes, configuracion, horarios, citatorios
from pdf.generador import generar_kardex, generar_boleta, generar_reporte_pdf, generar_citatorio_pdf

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# =========================
# VERIFICAR ADMIN
# =========================

def verificar_admin():
    return "rol" in session and session["rol"] == "admin"


# =========================
# DASHBOARD PRO
# =========================

@admin_bp.route("/")
def admin_dashboard():

    if not verificar_admin():
        return redirect("/")

    lista_alumnos = list(alumnos.find())
    lista_maestros = list(maestros.find())
    lista_reportes = list(reportes.find())

    return render_template(
        "admin.html",
        alumnos=lista_alumnos,
        grupos=list(grupos.find()),
        maestros=lista_maestros,
        reportes=lista_reportes,
        total_alumnos=len(lista_alumnos),
        total_maestros=len(lista_maestros),
        total_reportes=len(lista_reportes)
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

    foto = request.files.get("foto")
    foto_base64 = ""

    if foto and foto.filename != "":
        try:
            imagen_bytes = foto.read()
            if len(imagen_bytes) > 0:
                foto_base64 = base64.b64encode(imagen_bytes).decode("utf-8")
        except:
            pass

    alumnos.insert_one({
        "nombre": nombre,
        "grupo": grupo,
        "foto": foto_base64,
        "calificaciones": [],
        "asistencias": []
    })

    return redirect("/admin/alumnos")


# =========================
# KARDEX (DEBUG)
# =========================

@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):

    if not verificar_admin():
        return redirect("/")

    try:
        pdf = generar_kardex(nombre)
        pdf.seek(0)

        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"kardex_{nombre}.pdf"
        )

    except Exception as e:
        return f"ERROR REAL KARDEX: {str(e)}"


# =========================
# BOLETA (DEBUG)
# =========================

@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):

    if not verificar_admin():
        return redirect("/")

    try:
        pdf = generar_boleta(nombre)
        pdf.seek(0)

        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"boleta_{nombre}.pdf"
        )

    except Exception as e:
        return f"ERROR REAL BOLETA: {str(e)}"


# =========================
# REPORTE (DEBUG)
# =========================

@admin_bp.route("/aprobar_reporte/<string:id>")
def aprobar_reporte(id):

    if not verificar_admin():
        return redirect("/")

    try:
        reporte = reportes.find_one({"_id": ObjectId(id)})

        if not reporte:
            return "Reporte no encontrado"

        pdf = generar_reporte_pdf(reporte)
        pdf.seek(0)

        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="reporte.pdf"
        )

    except Exception as e:
        return f"ERROR REAL REPORTE: {str(e)}"


# =========================
# CITATORIO (DEBUG)
# =========================

@admin_bp.route("/generar_citatorio/<string:id>")
def generar_citatorio(id):

    if not verificar_admin():
        return redirect("/")

    try:
        citatorio = citatorios.find_one({"_id": ObjectId(id)})

        if not citatorio:
            return "Citatorio no encontrado"

        pdf = generar_citatorio_pdf(citatorio)
        pdf.seek(0)

        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="citatorio.pdf"
        )

    except Exception as e:
        return f"ERROR REAL CITATORIO: {str(e)}"


# =========================
# TEST
# =========================

@admin_bp.route("/test_pdf")
def test_pdf():
    return "RUTA ACTIVA"