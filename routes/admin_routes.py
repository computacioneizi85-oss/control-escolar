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
# DASHBOARD 🔥 CORREGIDO
# =========================

@admin_bp.route("/")
def admin_dashboard():

    try:
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

    except Exception as e:
        return f"<h1>ERROR DASHBOARD:</h1><pre>{str(e)}</pre>"


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

    alumnos.update_many({}, {"$set": {"enviado": False}})

    return redirect(url_for("admin.admin_dashboard"))


# =========================
# EVALUACIONES
# =========================

@admin_bp.route("/evaluaciones")
def ver_evaluaciones():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    lista = list(alumnos.find())
    datos = []

    for a in lista:
        for c in a.get("calificaciones", []):
            datos.append({
                "alumno": a.get("nombre"),
                "grupo": a.get("grupo"),
                "materia": c.get("materia"),
                "calificacion": c.get("calificacion"),
                "trimestre": c.get("trimestre"),
                "enviado": a.get("enviado", False)
            })

    config = configuracion.find_one({"tipo": "trimestre"}) or {}

    return render_template(
        "evaluaciones_admin.html",
        datos=datos,
        config=config
    )


# =========================
# CERRAR TRIMESTRE
# =========================

@admin_bp.route("/cerrar_trimestre")
def cerrar_trimestre():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    configuracion.update_one(
        {"tipo": "trimestre"},
        {"$set": {"estado": "false"}}
    )

    return redirect(url_for("admin.ver_evaluaciones"))


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
        "asistencias": [],
        "enviado": False
    })

    return redirect(url_for("admin.ver_alumnos"))


# =========================
# PDFS
# =========================

@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    pdf = generar_kardex(nombre)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf")


@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    pdf = generar_boleta(nombre)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf")


@admin_bp.route("/aprobar_reporte/<string:id>")
def aprobar_reporte(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    reporte = reportes.find_one({"_id": ObjectId(id)})
    if not reporte:
        return "Reporte no encontrado"

    pdf = generar_reporte_pdf(reporte)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf")


@admin_bp.route("/generar_citatorio/<string:id>")
def generar_citatorio(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    citatorio = citatorios.find_one({"_id": ObjectId(id)})
    if not citatorio:
        return "Citatorio no encontrado"

    pdf = generar_citatorio_pdf(citatorio)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf")


# =========================
# RESET GRUPO
# =========================

@admin_bp.route("/reset_grupo", methods=["POST"])
def reset_grupo():

    try:
        if not verificar_admin():
            return redirect(url_for("auth.login"))

        grupo = request.form.get("grupo")
        trimestre = request.form.get("trimestre")

        if not grupo or not trimestre:
            return "Error: datos incompletos"

        lista = list(alumnos.find({"grupo": grupo}))

        for alumno in lista:

            calificaciones = alumno.get("calificaciones", [])

            nuevas = [
                c for c in calificaciones
                if c.get("trimestre") != trimestre
            ]

            alumnos.update_one(
                {"_id": alumno["_id"]},
                {
                    "$set": {
                        "calificaciones": nuevas,
                        "enviado": False
                    }
                }
            )

        return redirect(url_for("admin.ver_evaluaciones"))

    except Exception as e:
        return f"<h1>ERROR RESET:</h1><pre>{str(e)}</pre>"