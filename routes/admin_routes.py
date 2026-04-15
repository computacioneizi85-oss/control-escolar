from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
import base64

from database.mongo import (
    alumnos, grupos, materias, maestros,
    reportes, configuracion, horarios,
    citatorios, padres
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

    try:
        lista_alumnos = list(alumnos.find())
        lista_grupos = list(grupos.find())
        lista_maestros = list(maestros.find())
        lista_reportes = list(reportes.find())
        lista_citatorios = list(citatorios.find())

        alumnos_riesgo = [a for a in lista_alumnos if not a.get("calificaciones")]
        ultimos_reportes = lista_reportes[-5:] if lista_reportes else []

        total_asistencias = sum(
            len(a.get("asistencias", []))
            for a in lista_alumnos
            if isinstance(a.get("asistencias", []), list)
        )

        total_faltas = 0

        return render_template(
            "admin.html",
            alumnos=lista_alumnos,
            grupos=lista_grupos,
            maestros=lista_maestros,
            reportes=lista_reportes,
            citatorios=lista_citatorios,
            alumnos_riesgo=alumnos_riesgo,
            ultimos_reportes=ultimos_reportes,
            total_asistencias=total_asistencias,
            total_faltas=total_faltas
        )

    except Exception as e:
        return f"ERROR DASHBOARD: {str(e)}"


# ================= HORARIOS =================
@admin_bp.route("/horarios")
def admin_horarios():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "horarios_admin.html",
        horarios=list(horarios.find()),
        maestros=list(maestros.find()),
        materias=list(materias.find()),
        grupos=list(grupos.find())
    )


@admin_bp.route("/crear_horario", methods=["POST"])
def crear_horario():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestro = request.form.get("maestro")
    materia = request.form.get("materia")
    grupo = request.form.get("grupo")
    dia = request.form.get("dia")
    hora = request.form.get("hora")

    if horarios.find_one({"grupo": grupo, "dia": dia, "hora": hora}):
        return "Ese grupo ya tiene clase en ese horario"

    if horarios.find_one({"maestro": maestro, "dia": dia, "hora": hora}):
        return "El maestro ya tiene clase en ese horario"

    horarios.insert_one({
        "maestro": maestro,
        "materia": materia,
        "grupo": grupo,
        "dia": dia,
        "hora": hora
    })

    return redirect("/admin/horarios")


@admin_bp.route("/eliminar_horario/<id>")
def eliminar_horario(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    horarios.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/horarios")


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

    usuario = request.form.get("usuario")
    password = request.form.get("password")

    if not usuario or not password:
        return "Faltan usuario o contraseña"

    password_hash = generate_password_hash(password)

    alumnos.insert_one({
        "nombre": request.form.get("nombre"),
        "grupo": request.form.get("grupo"),
        "usuario": usuario,
        "password": password_hash,
        "calificaciones": [],
        "asistencias": []
    })

    padres.insert_one({
        "nombre": f"Padre de {request.form.get('nombre')}",
        "usuario": f"padre_{usuario}",
        "password": generate_password_hash(password),
        "alumno": request.form.get("nombre")
    })

    return redirect(url_for("admin.ver_alumnos"))


# ================= CITATORIOS =================
@admin_bp.route("/citatorios")
def ver_citatorios():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "citatorios.html",
        citatorios=list(citatorios.find()),
        alumnos=list(alumnos.find())
    )


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
        "estatus": "pendiente",
        "enterado": False  # 🔥 NUEVO
    })

    return redirect(url_for("admin.ver_citatorios"))


@admin_bp.route("/generar_citatorio/<string:id>")
def generar_citatorio(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    citatorio = citatorios.find_one({"_id": ObjectId(id)})

    if not citatorio:
        return "Citatorio no encontrado"

    pdf = generar_citatorio_pdf(citatorio)
    pdf.seek(0)

    return send_file(
        pdf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name="citatorio.pdf"
    )


@admin_bp.route("/confirmar_asistencia/<id>")
def confirmar_asistencia(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    citatorios.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estatus": "asistio"}}
    )

    return redirect(url_for("admin.ver_citatorios"))