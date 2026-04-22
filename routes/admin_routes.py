from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
import base64
from datetime import datetime
import json

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


# ================= SEGURIDAD =================
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


# ================= ALUMNOS =================
@admin_bp.route("/alumnos")
def ver_alumnos():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("alumnos.html",
        alumnos=list(alumnos.find()),
        grupos=list(grupos.find()),
        maestros=list(maestros.find())
    )


@admin_bp.route("/crear_alumno", methods=["POST"])
def crear_alumno():
    password = request.form.get("password") or "1234"

    alumnos.insert_one({
        "nombre": request.form.get("nombre"),
        "grupo": request.form.get("grupo"),
        "usuario": request.form.get("usuario"),
        "password": generate_password_hash(password),
        "calificaciones": [],
        "asistencias": []
    })

    return redirect("/admin/alumnos")


@admin_bp.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    alumnos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/alumnos")


# ================= MAESTROS =================
@admin_bp.route("/maestros")
def ver_maestros():
    return render_template("maestros.html",
        maestros=list(maestros.find()),
        grupos=list(grupos.find()),
        materias=list(materias.find())
    )


@admin_bp.route("/crear_maestro", methods=["POST"])
def crear_maestro():
    maestros.insert_one({
        "nombre": request.form.get("nombre"),
        "usuario": request.form.get("usuario"),
        "password": request.form.get("password"),
        "grupos": [],
        "materias": []
    })
    return redirect("/admin/maestros")


@admin_bp.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):
    maestros.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/maestros")


# 🔥 ASIGNAR GRUPO
@admin_bp.route("/asignar_grupo_maestro", methods=["POST"])
def asignar_grupo_maestro():
    maestro_id = request.form.get("maestro")
    grupo = request.form.get("grupo")

    maestros.update_one(
        {"_id": ObjectId(maestro_id)},
        {"$addToSet": {"grupos": grupo}}
    )

    return redirect("/admin/maestros")


# 🔥 ASIGNAR MATERIAS
@admin_bp.route("/asignar_materias", methods=["POST"])
def asignar_materias():
    maestro_id = request.form.get("maestro_id")
    materias_seleccionadas = request.form.getlist("materias")

    maestros.update_one(
        {"_id": ObjectId(maestro_id)},
        {"$set": {"materias": materias_seleccionadas}}
    )

    return redirect("/admin/maestros")


# 🔥 EDITAR GRUPOS
@admin_bp.route("/editar_grupos_maestro", methods=["POST"])
def editar_grupos_maestro():
    maestro_id = request.form.get("maestro_id")
    grupos_seleccionados = request.form.getlist("grupos")

    maestros.update_one(
        {"_id": ObjectId(maestro_id)},
        {"$set": {"grupos": grupos_seleccionados}}
    )

    return redirect("/admin/maestros")


# 🔥 EDITAR MATERIAS
@admin_bp.route("/editar_materias_maestro", methods=["POST"])
def editar_materias_maestro():
    maestro_id = request.form.get("maestro_id")
    materias_seleccionadas = request.form.getlist("materias")

    maestros.update_one(
        {"_id": ObjectId(maestro_id)},
        {"$set": {"materias": materias_seleccionadas}}
    )

    return redirect("/admin/maestros")


# 🔥 QUITAR MATERIA
@admin_bp.route("/quitar_materia", methods=["POST"])
def quitar_materia():
    maestro_id = request.form.get("maestro_id")
    materia = request.form.get("materia")

    maestros.update_one(
        {"_id": ObjectId(maestro_id)},
        {"$pull": {"materias": materia}}
    )

    return redirect("/admin/maestros")


# ================= GRUPOS =================
@admin_bp.route("/grupos")
def ver_grupos():
    return render_template("grupos.html", grupos=list(grupos.find()))


@admin_bp.route("/crear_grupo", methods=["POST"])
def crear_grupo():
    grupos.insert_one({"nombre": request.form.get("nombre")})
    return redirect("/admin/grupos")


@admin_bp.route("/eliminar_grupo/<id>")
def eliminar_grupo(id):
    grupos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/grupos")


# ================= MATERIAS =================
@admin_bp.route("/materias")
def ver_materias():
    return render_template("materias.html",
        materias=list(materias.find()),
        grupos=list(grupos.find())
    )


@admin_bp.route("/crear_materia", methods=["POST"])
def crear_materia():
    materias.insert_one({
        "nombre": request.form.get("nombre"),
        "grupo": request.form.get("grupo")
    })
    return redirect("/admin/materias")


@admin_bp.route("/eliminar_materia/<id>")
def eliminar_materia(id):
    materias.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/materias")


# ================= HORARIOS =================
@admin_bp.route("/horarios")
def ver_horarios():
    return render_template("horarios_admin.html",
        horarios=list(horarios.find()),
        maestros=list(maestros.find()),
        materias=list(materias.find()),
        grupos=list(grupos.find())
    )


@admin_bp.route("/crear_horario", methods=["POST"])
def crear_horario():
    horarios.insert_one({
        "maestro": request.form.get("maestro"),
        "materia": request.form.get("materia"),
        "grupo": request.form.get("grupo"),
        "dia": request.form.get("dia"),
        "hora": request.form.get("hora")
    })
    return redirect("/admin/horarios")


@admin_bp.route("/eliminar_horario/<id>")
def eliminar_horario(id):
    horarios.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/horarios")


# ================= REPORTES =================
@admin_bp.route("/reportes")
def ver_reportes():
    return render_template("reportes.html", reportes=list(reportes.find()))


@admin_bp.route("/generar_reporte/<id>")
def generar_reporte(id):
    reporte = reportes.find_one({"_id": ObjectId(id)})
    pdf = generar_reporte_pdf(reporte)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf", as_attachment=True)


# ================= CITATORIOS =================
@admin_bp.route("/citatorios")
def ver_citatorios():
    return render_template("citatorios.html",
        citatorios=list(citatorios.find()),
        alumnos=list(alumnos.find())
    )


@admin_bp.route("/crear_citatorio", methods=["POST"])
def crear_citatorio():
    citatorios.insert_one({
        "alumno": request.form.get("alumno"),
        "grupo": request.form.get("grupo"),
        "motivo": request.form.get("motivo"),
        "fecha_cita": request.form.get("fecha"),
        "hora": request.form.get("hora"),
        "estatus": "pendiente",
        "enterado": False
    })
    return redirect("/admin/citatorios")


@admin_bp.route("/confirmar_asistencia/<id>")
def confirmar_asistencia(id):
    citatorios.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estatus": "asistio", "enterado": True}}
    )
    return redirect("/admin/citatorios")


@admin_bp.route("/generar_citatorio/<id>")
def generar_citatorio(id):
    citatorio = citatorios.find_one({"_id": ObjectId(id)})
    pdf = generar_citatorio_pdf(citatorio)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf", as_attachment=True)


# ================= PDFS =================
@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):
    pdf = generar_kardex(nombre)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf", as_attachment=True)


@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):
    pdf = generar_boleta(nombre)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf", as_attachment=True)


@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    trimestre = request.form.get("trimestre")
    estado = request.form.get("estado") == "true"

    configuracion.update_one(
        {},
        {
            "$set": {
                "trimestre_activo": trimestre,
                "trimestre_habilitado": estado
            }
        },
        upsert=True
    )

    return redirect("/admin")

@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    trimestre = request.form.get("trimestre")
    estado = request.form.get("estado") == "true"

    configuracion.update_one(
        {},
        {
            "$set": {
                "trimestre_activo": trimestre,
                "trimestre_habilitado": estado
            }
        },
        upsert=True
    )

    return redirect("/admin")