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
            "usuario": str(ObjectId()),
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

    alumnos.update_one({"_id": ObjectId(id)}, {"$set": update_data})

    return redirect(f"/admin/expediente/{id}")


# ================= CREAR MATERIA =================
@admin_bp.route("/crear_materia", methods=["POST"])
def crear_materia():
    nombre = request.form.get("nombre")
    grupo = request.form.get("grupo")

    if not nombre or not grupo:
        return "Faltan datos"

    materias.insert_one({
        "nombre": nombre,
        "grupo": grupo
    })

    return redirect("/admin/materias")

# ================= ELIMINAR MATERIA =================
@admin_bp.route("/eliminar_materia/<id>")
def eliminar_materia(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    materias.delete_one({"_id": ObjectId(id)})

    return redirect("/admin/materias")


# ================= MENÚS =================
@admin_bp.route("/materias")
def admin_materias():
    return render_template(
        "materias.html",
        materias=list(materias.find()),
        grupos=list(grupos.find())
    )


@admin_bp.route("/horarios")
def admin_horarios():
    return render_template(
        "horarios.html",
        horarios=list(horarios.find()),
        grupos=list(grupos.find()),
        materias=list(materias.find()),
        maestros=list(maestros.find())
    )


@admin_bp.route("/citatorios")
def admin_citatorios():
    return render_template(
        "citatorios.html",
        citatorios=list(citatorios.find()),
        alumnos=list(alumnos.find())
    )


# ================= HORARIOS =================
@admin_bp.route("/crear_horario", methods=["POST"])
def crear_horario():
    horarios.insert_one({
        "grupo": request.form.get("grupo"),
        "materia": request.form.get("materia"),
        "maestro": request.form.get("maestro"),
        "dia": request.form.get("dia"),
        "hora": request.form.get("hora")
    })
    return redirect("/admin/horarios")


# ================= CITATORIOS =================
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


@admin_bp.route("/citatorio_pdf/<id>")
def citatorio_pdf(id):
    citatorio = citatorios.find_one({"_id": ObjectId(id)})
    pdf = generar_citatorio_pdf(citatorio)
    pdf.seek(0)

    return send_file(
        pdf,
        as_attachment=True,
        download_name="citatorio.pdf",
        mimetype="application/pdf"
    )
