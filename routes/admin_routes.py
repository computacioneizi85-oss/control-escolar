from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
import base64
from datetime import datetime

from database.mongo import (
    alumnos, grupos, materias, maestros,
    reportes, configuracion, horarios,
    citatorios, padres, avisos  # 🔥 NUEVO
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

    lista_alumnos = list(alumnos.find())
    lista_grupos = list(grupos.find())
    lista_maestros = list(maestros.find())
    lista_reportes = list(reportes.find())
    lista_citatorios = list(citatorios.find())

    return render_template(
        "admin.html",
        alumnos=lista_alumnos,
        grupos=lista_grupos,
        maestros=lista_maestros,
        reportes=lista_reportes,
        citatorios=lista_citatorios,
        alumnos_riesgo=[a for a in lista_alumnos if not a.get("calificaciones")],
        ultimos_reportes=lista_reportes[-5:],
        total_asistencias=sum(len(a.get("asistencias", [])) for a in lista_alumnos),
        total_faltas=0
    )


# ================= 🔔 AVISOS =================

@admin_bp.route("/avisos")
def ver_avisos():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("avisos.html", avisos=list(avisos.find()))


@admin_bp.route("/crear_aviso", methods=["POST"])
def crear_aviso():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    avisos.insert_one({
        "tipo": request.form.get("tipo"),
        "titulo": request.form.get("titulo"),
        "mensaje": request.form.get("mensaje"),
        "fecha": datetime.now().strftime("%d/%m/%Y")
    })

    return redirect("/admin/avisos")


@admin_bp.route("/eliminar_aviso/<id>")
def eliminar_aviso(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    avisos.delete_one({"_id": ObjectId(id)})
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


# ================= CONFIGURACIÓN =================
@admin_bp.route("/configuracion")
def ver_configuracion():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    config = configuracion.find_one() or {}
    return render_template("configuracion.html", config=config)


# ================= TRIMESTRE =================
@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    configuracion.update_one(
        {},
        {"$set": {f"trimestre_{request.form.get('trimestre')}": request.form.get("estado") == "true"}},
        upsert=True
    )

    return redirect("/admin")


# ================= HORARIOS =================
@admin_bp.route("/horarios")
def ver_horarios():
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
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    horarios.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/horarios")


# ================= GRUPOS =================
@admin_bp.route("/grupos")
def ver_grupos():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("grupos.html", grupos=list(grupos.find()))


# ================= MATERIAS =================
@admin_bp.route("/materias")
def ver_materias():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("materias.html", materias=list(materias.find()))


# ================= REPORTES =================
@admin_bp.route("/reportes")
def ver_reportes():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("reportes.html", reportes=list(reportes.find()))


# ================= CITATORIOS =================
@admin_bp.route("/citatorios")
def ver_citatorios():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("citatorios.html", citatorios=list(citatorios.find()))


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


# ================= PDFS (SIN CAMBIOS) =================
@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):
    pdf = generar_kardex(nombre)
    pdf.seek(0)
    return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name=f"kardex_{nombre}.pdf")


@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):
    pdf = generar_boleta(nombre)
    pdf.seek(0)
    return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name=f"boleta_{nombre}.pdf")