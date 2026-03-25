from flask import Blueprint, render_template, request, redirect, session, jsonify
from database.mongo import alumnos, maestros, reportes, horarios, configuracion
from datetime import datetime

maestro_bp = Blueprint("maestro", __name__)


def verificar_maestro():
    return "rol" in session and session["rol"] == "maestro"


# =========================
# PANEL MAESTRO 🔥 CORREGIDO
# =========================
@maestro_bp.route("/panel_maestro")
def panel_maestro():

    if not verificar_maestro():
        return redirect("/")

    maestro = maestros.find_one({"usuario": session["usuario"]})

    if not maestro:
        return redirect("/")

    # 🔥 materias asignadas
    materias_maestro = maestro.get("materias", [])

    # 🔥 horarios SOLO de sus materias
    lista_horarios = list(horarios.find({
        "materia": {"$in": materias_maestro}
    }))

    # 🔥 grupos derivados de horarios
    grupos = list(set([h.get("grupo") for h in lista_horarios if h.get("grupo")]))

    # 🔥 alumnos SOLO de sus grupos
    lista_alumnos = list(alumnos.find({"grupo": {"$in": grupos}}))

    config = configuracion.find_one({"tipo": "trimestre"}) or {}

    return render_template(
        "panel_maestro.html",
        alumnos=lista_alumnos,
        grupos=grupos,
        horarios=lista_horarios,
        materias=materias_maestro,  # 🔥 CLAVE
        config=config
    )


# =========================
# GUARDAR CALIFICACIONES 🔒
# =========================
@maestro_bp.route("/guardar_calificaciones", methods=["POST"])
def guardar_calificaciones():

    if not verificar_maestro():
        return redirect("/")

    maestro = maestros.find_one({"usuario": session["usuario"]})
    materias_maestro = maestro.get("materias", [])

    alumno_nombre = request.form.get("alumno")
    materia = request.form.get("materia")
    trimestre = request.form.get("trimestre")
    cal1 = request.form.get("cal1")

    config = configuracion.find_one({"tipo": "trimestre"}) or {}

    # 🔒 trimestre cerrado
    if config.get("estado") != "true":
        return "Evaluaciones cerradas"

    # 🔒 bloqueo por materia
    if materia not in materias_maestro:
        return "❌ No puedes modificar esta materia"

    alumno = alumnos.find_one({"nombre": alumno_nombre})

    if alumno.get("enviado"):
        return "Ya enviadas"

    calificaciones = alumno.get("calificaciones", [])

    encontrada = False

    for c in calificaciones:
        if c.get("materia") == materia and str(c.get("trimestre")) == str(trimestre):
            c["calificacion"] = float(cal1)
            encontrada = True

    if not encontrada:
        calificaciones.append({
            "materia": materia,
            "calificacion": float(cal1),
            "trimestre": str(trimestre)
        })

    alumnos.update_one(
        {"nombre": alumno_nombre},
        {"$set": {"calificaciones": calificaciones}}
    )

    return redirect("/panel_maestro")


# =========================
# ENVIAR CALIFICACIONES
# =========================
@maestro_bp.route("/enviar_calificaciones")
def enviar_calificaciones():

    if not verificar_maestro():
        return redirect("/")

    maestro = maestros.find_one({"usuario": session["usuario"]})
    grupos = maestro.get("grupos", [])

    alumnos.update_many(
        {"grupo": {"$in": grupos}},
        {"$set": {"enviado": True}}
    )

    return redirect("/panel_maestro")


# =========================
# AJAX 🔥 PROTEGIDO
# =========================
@maestro_bp.route("/guardar_calificaciones_ajax", methods=["POST"])
def guardar_calificaciones_ajax():

    if not verificar_maestro():
        return jsonify({"status": "error"})

    maestro = maestros.find_one({"usuario": session["usuario"]})
    materias_maestro = maestro.get("materias", [])

    alumno_nombre = request.form.get("alumno")
    materia = request.form.get("materia")
    trimestre = request.form.get("trimestre")
    cal1 = request.form.get("cal1")

    config = configuracion.find_one({"tipo": "trimestre"}) or {}

    if config.get("estado") != "true":
        return jsonify({"status": "cerrado"})

    # 🔒 bloqueo por materia
    if materia not in materias_maestro:
        return jsonify({"status": "prohibido"})

    alumno = alumnos.find_one({"nombre": alumno_nombre})

    if alumno.get("enviado"):
        return jsonify({"status": "bloqueado"})

    calificaciones = alumno.get("calificaciones", [])

    encontrada = False

    for c in calificaciones:
        if c.get("materia") == materia and str(c.get("trimestre")) == str(trimestre):
            c["calificacion"] = float(cal1)
            encontrada = True

    if not encontrada:
        calificaciones.append({
            "materia": materia,
            "calificacion": float(cal1),
            "trimestre": str(trimestre)
        })

    alumnos.update_one(
        {"nombre": alumno_nombre},
        {"$set": {"calificaciones": calificaciones}}
    )

    return jsonify({
        "status": "ok",
        "calificacion": cal1
    })


# =========================
# RESET POR ALUMNO 🔥 MEJORADO
# =========================
@maestro_bp.route("/reset_alumno", methods=["POST"])
def reset_alumno():

    if not verificar_maestro():
        return jsonify({"status": "error"})

    nombre = request.form.get("alumno")
    trimestre = str(request.form.get("trimestre"))

    alumno = alumnos.find_one({"nombre": nombre})

    nuevas = []

    for c in alumno.get("calificaciones", []):
        if str(c.get("trimestre")) != trimestre:
            nuevas.append(c)

    alumnos.update_one(
        {"_id": alumno["_id"]},
        {
            "$set": {
                "calificaciones": nuevas,
                "enviado": False
            }
        }
    )

    return jsonify({"status": "ok"})