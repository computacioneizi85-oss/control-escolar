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

    lista_alumnos = list(alumnos.find())
    lista_maestros = list(maestros.find())
    lista_reportes = list(reportes.find())
    lista_grupos = list(grupos.find())

    return render_template(
        "admin.html",
        alumnos=lista_alumnos,
        grupos=lista_grupos,
        maestros=lista_maestros,
        reportes=lista_reportes,
        total_alumnos=len(lista_alumnos),
        total_maestros=len(lista_maestros),
        total_reportes=len(lista_reportes)
    )


# =========================
# ACTIVAR TRIMESTRE
# =========================

@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    trimestre = request.form.get("trimestre")
    estado = request.form.get("estado")

    configuracion.update_one(
        {"tipo": "trimestre"},
        {"$set": {"trimestre": trimestre, "estado": estado}},
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

    return redirect(url_for("admin.ver_alumnos"))


# =========================
# KARDEX
# =========================

@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    pdf = generar_kardex(nombre)
    pdf.seek(0)

    return send_file(
        pdf,
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
        return redirect(url_for("auth.login"))

    pdf = generar_boleta(nombre)
    pdf.seek(0)

    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"boleta_{nombre}.pdf"
    )