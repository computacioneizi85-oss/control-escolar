from flask import Blueprint, render_template, request, redirect, session, url_for, send_file
from bson.objectid import ObjectId
from datetime import datetime

from database.mongo import alumnos, maestros, horarios, configuracion, citatorios, avisos, reportes
from pdf.generador import generar_citatorio_pdf

maestro_bp = Blueprint("maestro", __name__)


# ================= SEGURIDAD =================
def verificar_maestro():
    return session.get("rol") == "maestro"


# ================= PANEL =================
@maestro_bp.route("/panel_maestro")
def panel_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}

    materias = maestro.get("materias", [])
    grupos = maestro.get("grupos", [])

    lista_alumnos = list(alumnos.find({"grupo": {"$in": grupos}}))
    lista_horarios = list(horarios.find({"grupo": {"$in": grupos}}))
    config = configuracion.find_one() or {"trimestre": "1", "estado": True}

    return render_template(
        "panel_maestro.html",
        alumnos=lista_alumnos,
        grupos=grupos,
        materias=materias,
        horarios=lista_horarios,
        config=config
    )


# ================= AVISOS =================
@maestro_bp.route("/avisos_maestro")
def avisos_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}

    return render_template(
        "avisos_maestro.html",
        grupos=maestro.get("grupos", [])
    )


@maestro_bp.route("/crear_aviso_maestro", methods=["POST"])
def crear_aviso_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    avisos.insert_one({
        "tipo": "grupo",
        "grupo": request.form.get("grupo"),
        "mensaje": request.form.get("mensaje"),
        "fecha": datetime.now()
    })

    return redirect("/avisos_maestro")


# ================= CITATORIOS =================
@maestro_bp.route("/citatorios")
def ver_citatorios_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}
    grupos = maestro.get("grupos", [])

    return render_template(
        "citatorios_maestro.html",
        citatorios=list(citatorios.find({"grupo": {"$in": grupos}})),
        alumnos=list(alumnos.find({"grupo": {"$in": grupos}}))
    )


@maestro_bp.route("/crear_citatorio", methods=["POST"])
def crear_citatorio_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    citatorios.insert_one({
        "alumno": request.form.get("alumno"),
        "grupo": request.form.get("grupo"),
        "motivo": request.form.get("motivo"),
        "fecha_cita": request.form.get("fecha"),
        "hora": request.form.get("hora"),
        "estatus": "pendiente",
        "maestro": session.get("usuario")
    })

    return redirect("/citatorios")


@maestro_bp.route("/generar_citatorio/<id>")
def generar_citatorio_maestro(id):

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    citatorio = citatorios.find_one({"_id": ObjectId(id)})

    pdf = generar_citatorio_pdf(citatorio)
    pdf.seek(0)

    return send_file(pdf, as_attachment=True, download_name="citatorio.pdf")


# ================= EVALUACIONES (SIN DUPLICADOS) =================
@maestro_bp.route("/guardar_calificaciones_ajax", methods=["POST"])
def guardar_calificaciones_ajax():

    if not verificar_maestro():
        return {"status": "error"}

    alumno = request.form.get("alumno")
    materia = request.form.get("materia")
    trimestre = request.form.get("trimestre")

    try:
        cal = float(request.form.get("cal1") or 0)
    except:
        cal = 0

    # 🔥 evitar duplicados → eliminar previa
    alumnos.update_one(
        {"nombre": alumno},
        {
            "$pull": {
                "calificaciones": {
                    "materia": materia,
                    "trimestre": trimestre
                }
            }
        }
    )

    # 🔥 insertar nueva
    alumnos.update_one(
        {"nombre": alumno},
        {
            "$push": {
                "calificaciones": {
                    "materia": materia,
                    "calificacion": cal,
                    "trimestre": trimestre
                }
            }
        }
    )

    return {"status": "ok"}


# ================= ASISTENCIA (VALIDADA) =================
@maestro_bp.route("/guardar_asistencia_ajax", methods=["POST"])
def guardar_asistencia_ajax():

    if not verificar_maestro():
        return {"status": "error"}

    alumno = request.form.get("alumno")
    estado = request.form.get("estado")
    fecha = request.form.get("fecha")

    # 🔴 VALIDACIÓN
    if not fecha or not estado:
        return {"status": "error"}

    # 🔥 evitar duplicado mismo día
    alumnos.update_one(
        {"nombre": alumno},
        {
            "$pull": {
                "asistencias": {
                    "fecha": fecha
                }
            }
        }
    )

    alumnos.update_one(
        {"nombre": alumno},
        {
            "$push": {
                "asistencias": {
                    "fecha": fecha,
                    "estado": estado
                }
            }
        }
    )

    return {"status": "ok"}


# ================= REPORTES =================
@maestro_bp.route("/crear_reporte", methods=["POST"])
def crear_reporte():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    reportes.insert_one({
        "alumno": request.form.get("alumno"),
        "grupo": request.form.get("grupo"),
        "comentario": request.form.get("comentario"),
        "fecha": request.form.get("fecha"),
        "maestro": session.get("usuario"),
        "estatus": "pendiente"
    })

    return redirect("/panel_maestro")


@maestro_bp.route("/enviar_reportes_maestro", methods=["POST"])
def enviar_reportes_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    reportes.update_many(
        {"maestro": session.get("usuario")},
        {"$set": {"estatus": "enviado"}}
    )

    return redirect("/panel_maestro")


# ================= CONFIRMAR CITATORIO =================
@maestro_bp.route("/confirmar_asistencia/<id>")
def confirmar_asistencia_maestro(id):

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    citatorios.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estatus": "asistio"}}
    )

    return redirect("/citatorios")

# ================= HORARIO =================
@maestro_bp.route("/horario")
def horario_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}
    grupos = maestro.get("grupos", [])

    lista_horarios = list(horarios.find({"grupo": {"$in": grupos}}))

    return render_template(
        "horario_maestro.html",
        horarios=lista_horarios
    )