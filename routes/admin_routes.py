# ================= IMPORTS =================
from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId
import os

from database.mongo import (
    alumnos, grupos, materias, maestros,
    reportes, configuracion, horarios,
    citatorios, avisos
)

from pdf.generador import (
    generar_kardex, generar_boleta,
    generar_citatorio_pdf
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


# ================= ALUMNOS =================
@admin_bp.route("/alumnos")
def admin_alumnos():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "alumnos.html",
        alumnos=list(alumnos.find()),
        grupos=list(grupos.find())
    )


@admin_bp.route("/crear_alumno", methods=["POST"])
def crear_alumno():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumnos.insert_one({
        "nombre": request.form.get("nombre"),
        "grupo": request.form.get("grupo"),
        "calificaciones": [],
        "asistencias": []
    })
    return redirect("/admin/alumnos")


@admin_bp.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumnos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/alumnos")


# ================= MAESTROS =================
@admin_bp.route("/maestros")
def admin_maestros():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "maestros.html",
        maestros=list(maestros.find())
    )


@admin_bp.route("/crear_maestro", methods=["POST"])
def crear_maestro():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

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
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestros.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/maestros")


# ================= GRUPOS =================
@admin_bp.route("/grupos")
def admin_grupos():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "grupos.html",
        grupos=list(grupos.find())
    )


@admin_bp.route("/crear_grupo", methods=["POST"])
def crear_grupo():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    grupos.insert_one({
        "nombre": request.form.get("nombre")
    })
    return redirect("/admin/grupos")


@admin_bp.route("/eliminar_grupo/<id>")
def eliminar_grupo(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    grupos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/grupos")


# ================= MATERIAS =================
@admin_bp.route("/materias")
def admin_materias():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "materias.html",
        materias=list(materias.find()),
        grupos=list(grupos.find())
    )


@admin_bp.route("/crear_materia", methods=["POST"])
def crear_materia():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    materias.insert_one({
        "nombre": request.form.get("nombre"),
        "grupo": request.form.get("grupo")
    })
    return redirect("/admin/materias")


@admin_bp.route("/eliminar_materia/<id>")
def eliminar_materia(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    materias.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/materias")


# ================= HORARIOS =================
@admin_bp.route("/horarios")
def admin_horarios():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "horarios.html",
        horarios=list(horarios.find()),
        grupos=list(grupos.find()),
        materias=list(materias.find()),
        maestros=list(maestros.find())
    )


@admin_bp.route("/crear_horario", methods=["POST"])
def crear_horario():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    horarios.insert_one({
        "grupo": request.form.get("grupo"),
        "materia": request.form.get("materia"),
        "maestro": request.form.get("maestro"),
        "dia": request.form.get("dia"),
        "hora": request.form.get("hora")
    })
    return redirect("/admin/horarios")


@admin_bp.route("/eliminar_horario/<id>")
def eliminar_horario(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    horarios.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/horarios")


# ================= REPORTES =================
@admin_bp.route("/reportes")
def admin_reportes():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "reportes.html",
        reportes=list(reportes.find())
    )


@admin_bp.route("/reporte_pdf/<id>")
def reporte_pdf(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    reporte = reportes.find_one({"_id": ObjectId(id)})
    pdf = generar_citatorio_pdf(reporte)
    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name="reporte.pdf")


# ================= CITATORIOS =================
@admin_bp.route("/citatorios")
def admin_citatorios():
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
        "enterado": False
    })
    return redirect("/admin/citatorios")


@admin_bp.route("/confirmar_asistencia/<id>")
def confirmar_asistencia(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    citatorios.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estatus": "asistio", "enterado": True}}
    )
    return redirect("/admin/citatorios")


@admin_bp.route("/citatorio_pdf/<id>")
def citatorio_pdf(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    citatorio = citatorios.find_one({"_id": ObjectId(id)})
    pdf = generar_citatorio_pdf(citatorio)
    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name="citatorio.pdf")


# ================= KARDEX =================
@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    pdf = generar_kardex(nombre)
    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name="kardex.pdf")


# ================= BOLETA =================
@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    pdf = generar_boleta(nombre)
    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name="boleta.pdf")


# ================= EXPEDIENTE =================
@admin_bp.route("/expediente/<id>")
def expediente(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumno = alumnos.find_one({"_id": ObjectId(id)})
    return render_template("expediente.html", alumno=alumno)


@admin_bp.route("/expediente_pdf/<id>")
def expediente_pdf(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumno = alumnos.find_one({"_id": ObjectId(id)})
    pdf = generar_boleta(alumno["nombre"])
    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name="expediente.pdf")


# ================= AVISOS =================
@admin_bp.route("/avisos")
def admin_avisos():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "avisos.html",
        avisos=list(avisos.find())
    )


@admin_bp.route("/crear_aviso", methods=["POST"])
def crear_aviso():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    avisos.insert_one({
        "titulo": request.form.get("titulo"),
        "mensaje": request.form.get("mensaje"),
        "tipo": request.form.get("tipo")
    })
    return redirect("/admin/avisos")


@admin_bp.route("/editar_aviso/<id>", methods=["POST"])
def editar_aviso(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    avisos.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "titulo": request.form.get("titulo"),
            "mensaje": request.form.get("mensaje")
        }}
    )
    return redirect("/admin/avisos")


@admin_bp.route("/eliminar_aviso/<id>")
def eliminar_aviso(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    avisos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/avisos")


# ================= CONFIGURACION =================
@admin_bp.route("/configuracion")
def admin_configuracion():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    config = configuracion.find_one()
    return render_template("configuracion.html", config=config)


@admin_bp.route("/guardar_configuracion", methods=["POST"])
def guardar_configuracion():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        import base64

        escudo_file = request.files.get("escudo")
        escudo_base64 = None

        if escudo_file and escudo_file.filename:
            escudo_base64 = base64.b64encode(escudo_file.read()).decode("utf-8")

        config_actual = configuracion.find_one()

        if not escudo_base64 and config_actual:
            escudo_base64 = config_actual.get("escudo")

        configuracion.update_one(
            {},
            {
                "$set": {
                    "escuela": request.form.get("escuela"),
                    "ciclo": request.form.get("ciclo"),
                    "director": request.form.get("director"),
                    "direccion": request.form.get("direccion"),
                    "escudo": escudo_base64
                }
            },
            upsert=True
        )

        return redirect("/admin/configuracion")

    except Exception as e:
        return f"ERROR CONFIG: {str(e)}"


# ================= TRIMESTRE =================
@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():
    return redirect("/admin")