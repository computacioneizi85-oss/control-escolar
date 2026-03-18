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
# CREAR ALUMNO (BASE64 SEGURO)
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
# CAMBIAR FOTO (NO BORRA SI FALLA)
# =========================

@admin_bp.route("/subir_foto_alumno/<id>", methods=["POST"])
def subir_foto_alumno(id):

    if not verificar_admin():
        return redirect("/")

    foto = request.files.get("foto")

    if foto and foto.filename != "":
        try:
            imagen_bytes = foto.read()
            if len(imagen_bytes) > 0:
                foto_base64 = base64.b64encode(imagen_bytes).decode("utf-8")

                alumnos.update_one(
                    {"_id": ObjectId(id)},
                    {"$set": {"foto": foto_base64}}
                )
        except:
            pass

    return redirect("/admin/alumnos")


# =========================
# 🔥 ELIMINAR ALUMNO
# =========================

@admin_bp.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):

    if not verificar_admin():
        return redirect("/")

    alumnos.delete_one({"_id": ObjectId(id)})

    return redirect("/admin/alumnos")


# =========================
# 🔥 ESCUDO BASE64 SEGURO
# =========================

@admin_bp.route("/subir_escudo", methods=["POST"])
def subir_escudo():

    if not verificar_admin():
        return redirect("/")

    escudo = request.files.get("escudo")

    if escudo and escudo.filename != "":
        try:
            imagen_bytes = escudo.read()

            if len(imagen_bytes) > 0:
                escudo_base64 = base64.b64encode(imagen_bytes).decode("utf-8")

                configuracion.update_one(
                    {},
                    {"$set": {"escudo": escudo_base64}},
                    upsert=True
                )
        except:
            pass

    return redirect("/admin/configuracion")


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


@admin_bp.route("/aprobar_reporte/<string:id>")
def aprobar_reporte(id):

    if not verificar_admin():
        return redirect("/")

    reporte = reportes.find_one({"_id": ObjectId(id)})

    if not reporte:
        return redirect("/admin/reportes")

    pdf = generar_reporte_pdf(reporte)
    pdf.seek(0)

    return send_file(pdf, mimetype="application/pdf", as_attachment=True)


# =========================
# KARDEX
# =========================

@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):

    if not verificar_admin():
        return redirect("/")

    pdf = generar_kardex(nombre)
    pdf.seek(0)

    return send_file(pdf, mimetype="application/pdf", as_attachment=True)


# =========================
# BOLETA
# =========================

@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):

    if not verificar_admin():
        return redirect("/")

    pdf = generar_boleta(nombre)
    pdf.seek(0)

    return send_file(pdf, mimetype="application/pdf", as_attachment=True)


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


@admin_bp.route("/crear_citatorio", methods=["POST"])
def crear_citatorio():

    if not verificar_admin():
        return redirect("/")

    citatorios.insert_one({
        "alumno": request.form.get("alumno"),
        "grupo": request.form.get("grupo"),
        "motivo": request.form.get("motivo"),
        "fecha_cita": request.form.get("fecha"),
        "hora": request.form.get("hora"),
        "estado": "pendiente"
    })

    return redirect("/admin/citatorios")


@admin_bp.route("/generar_citatorio/<string:id>")
def generar_citatorio(id):

    if not verificar_admin():
        return redirect("/")

    citatorio = citatorios.find_one({"_id": ObjectId(id)})

    if not citatorio:
        return redirect("/admin/citatorios")

    pdf = generar_citatorio_pdf(citatorio)
    pdf.seek(0)

    return send_file(pdf, mimetype="application/pdf", as_attachment=True)


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


# =========================
# TEST
# =========================

@admin_bp.route("/test_pdf")
def test_pdf():
    return "RUTA ACTIVA"