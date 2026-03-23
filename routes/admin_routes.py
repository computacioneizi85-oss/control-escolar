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

    try:
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
    except Exception as e:
        return f"<h1>ERROR DASHBOARD</h1><pre>{str(e)}</pre>"


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
# 🔥 PDF KARDEX
# =========================

@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        pdf = generar_kardex(nombre)
        pdf.seek(0)
        return send_file(pdf, mimetype="application/pdf")
    except Exception as e:
        return f"Error kardex: {str(e)}"


# =========================
# 🔥 PDF BOLETA
# =========================

@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        pdf = generar_boleta(nombre)
        pdf.seek(0)
        return send_file(pdf, mimetype="application/pdf")
    except Exception as e:
        return f"Error boleta: {str(e)}"


# =========================
# 🔥 PDF REPORTE
# =========================

@admin_bp.route("/aprobar_reporte/<string:id>")
def aprobar_reporte(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        reporte = reportes.find_one({"_id": ObjectId(id)})

        if not reporte:
            return "Reporte no encontrado"

        pdf = generar_reporte_pdf(reporte)
        pdf.seek(0)

        return send_file(pdf, mimetype="application/pdf")

    except Exception as e:
        return f"Error reporte: {str(e)}"


# =========================
# 🔥 PDF CITATORIO
# =========================

@admin_bp.route("/generar_citatorio/<string:id>")
def generar_citatorio(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        citatorio = citatorios.find_one({"_id": ObjectId(id)})

        if not citatorio:
            return "Citatorio no encontrado"

        pdf = generar_citatorio_pdf(citatorio)
        pdf.seek(0)

        return send_file(pdf, mimetype="application/pdf")

    except Exception as e:
        return f"Error citatorio: {str(e)}"


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
    if not verificar_admin():
        return redirect(url_for("auth.login"))
    return render_template("reportes_admin.html", reportes=list(reportes.find()))


@admin_bp.route("/citatorios")
def ver_citatorios():
    if not verificar_admin():
        return redirect(url_for("auth.login"))
    return render_template("citatorios.html",
        citatorios=list(citatorios.find()),
        alumnos=list(alumnos.find())
    )


@admin_bp.route("/maestros")
def ver_maestros():
    if not verificar_admin():
        return redirect(url_for("auth.login"))
    return render_template("maestros.html", maestros=list(maestros.find()))


@admin_bp.route("/grupos")
def ver_grupos():
    if not verificar_admin():
        return redirect(url_for("auth.login"))
    return render_template("grupos.html", grupos=list(grupos.find()))


@admin_bp.route("/materias")
def ver_materias():
    if not verificar_admin():
        return redirect(url_for("auth.login"))
    return render_template("materias.html", materias=list(materias.find()))


@admin_bp.route("/horarios")
def ver_horarios():
    if not verificar_admin():
        return redirect(url_for("auth.login"))
    return render_template("horarios.html", horarios=list(horarios.find()))


@admin_bp.route("/asistencias")
def ver_asistencias():
    if not verificar_admin():
        return redirect(url_for("auth.login"))
    return render_template("asistencias_admin.html", alumnos=list(alumnos.find()))


@admin_bp.route("/configuracion")
def configuracion_admin():
    if not verificar_admin():
        return redirect(url_for("auth.login"))
    return render_template("configuracion.html")