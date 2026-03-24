from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId
import base64

from database.mongo import alumnos, grupos, materias, maestros, reportes, configuracion, horarios, citatorios
from pdf.generador import generar_kardex, generar_boleta, generar_reporte_pdf, generar_citatorio_pdf

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def verificar_admin():
    return "rol" in session and session["rol"] == "admin"


# ================= DASHBOARD =================
@admin_bp.route("/")
def admin_dashboard():
    try:
        if not verificar_admin():
            return redirect(url_for("auth.login"))

        return render_template(
            "admin.html",
            alumnos=list(alumnos.find()),
            grupos=list(grupos.find()),
            maestros=list(maestros.find()),
            reportes=list(reportes.find())
        )

    except Exception as e:
        return f"<h1>ERROR DASHBOARD:</h1><pre>{str(e)}</pre>"


# ================= TRIMESTRE =================
@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    configuracion.update_one(
        {"tipo": "trimestre"},
        {"$set": {
            "trimestre": str(request.form.get("trimestre")),
            "estado": request.form.get("estado")
        }},
        upsert=True
    )

    alumnos.update_many({}, {"$set": {"enviado": False}})

    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/cerrar_trimestre")
def cerrar_trimestre():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    configuracion.update_one(
        {"tipo": "trimestre"},
        {"$set": {"estado": "false"}}
    )

    return redirect(url_for("admin.ver_evaluaciones"))


# ================= EVALUACIONES =================
@admin_bp.route("/evaluaciones")
def ver_evaluaciones():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    datos = []

    for a in alumnos.find():
        for c in a.get("calificaciones", []):
            datos.append({
                "alumno": a.get("nombre"),
                "grupo": a.get("grupo"),
                "materia": c.get("materia"),
                "calificacion": c.get("calificacion"),
                "trimestre": str(c.get("trimestre")),
                "enviado": a.get("enviado", False)
            })

    config = configuracion.find_one({"tipo": "trimestre"}) or {}

    return render_template("evaluaciones_admin.html", datos=datos, config=config)


# ================= RESET GRUPO =================
@admin_bp.route("/reset_grupo", methods=["POST"])
def reset_grupo():

    try:
        if not verificar_admin():
            return redirect(url_for("auth.login"))

        grupo = request.form.get("grupo")
        trimestre = str(request.form.get("trimestre"))

        for alumno in alumnos.find({"grupo": grupo}):

            nuevas = []

            for c in alumno.get("calificaciones", []):

                if str(c.get("trimestre")) == trimestre or c.get("trimestre") is None:
                    continue

                nuevas.append(c)

            alumnos.update_one(
                {"_id": alumno["_id"]},
                {"$set": {"calificaciones": nuevas, "enviado": False}}
            )

        return redirect(url_for("admin.ver_evaluaciones"))

    except Exception as e:
        return f"<h1>ERROR RESET:</h1><pre>{str(e)}</pre>"


# ================= ALUMNOS =================
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


# ================= PDFS =================
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

    try:
        if not verificar_admin():
            return redirect(url_for("auth.login"))

        citatorio_doc = citatorios.find_one({"_id": ObjectId(id)})

        if not citatorio_doc:
            return "Citatorio no encontrado"

        pdf = generar_citatorio_pdf(citatorio_doc)
        pdf.seek(0)

        return send_file(pdf, mimetype="application/pdf")

    except Exception as e:
        return f"<h1>ERROR CITATORIO PDF:</h1><pre>{str(e)}</pre>"


# ================= MENÚS =================
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


@admin_bp.route("/reportes")
def ver_reportes():
    if not verificar_admin():
        return redirect(url_for("auth.login"))
    return render_template("reportes_admin.html", reportes=list(reportes.find()))


# 🔥 CITATORIOS CORREGIDO
@admin_bp.route("/citatorios")
def ver_citatorios():

    try:
        if not verificar_admin():
            return redirect(url_for("auth.login"))

        lista = list(citatorios.find())

        return render_template("citatorios.html", citatorios=lista)

    except Exception as e:
        return f"<h1>ERROR CITATORIOS:</h1><pre>{str(e)}</pre>"


# ================= CONFIG =================
@admin_bp.route("/configuracion")
def configuracion_admin():
    if not verificar_admin():
        return redirect(url_for("auth.login"))
    return render_template("configuracion.html")