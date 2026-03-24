from flask import Blueprint, render_template, request, redirect, session, jsonify
from database.mongo import alumnos, maestros, reportes, horarios, configuracion
from datetime import datetime

maestro_bp = Blueprint("maestro", __name__)


def verificar_maestro():
    return "rol" in session and session["rol"] == "maestro"


@maestro_bp.route("/panel_maestro")
def panel_maestro():

    if not verificar_maestro():
        return redirect("/")

    maestro = maestros.find_one({"usuario": session["usuario"]})

    if not maestro:
        return redirect("/")

    grupos = maestro.get("grupos", [])

    lista_horarios = list(horarios.find({
        "$or": [
            {"maestro": maestro.get("nombre")},
            {"maestro": maestro.get("usuario")}
        ]
    }))

    if lista_horarios:
        grupos_horario = [h.get("grupo") for h in lista_horarios if h.get("grupo")]
        grupos = list(set(grupos + grupos_horario))

    lista_alumnos = list(alumnos.find({"grupo": {"$in": grupos}}))

    config = configuracion.find_one({"tipo": "trimestre"}) or {}

    return render_template(
        "panel_maestro.html",
        alumnos=lista_alumnos,
        grupos=grupos,
        horarios=lista_horarios,
        config=config
    )


@maestro_bp.route("/guardar_calificaciones", methods=["POST"])
def guardar_calificaciones():

    if not verificar_maestro():
        return redirect("/")

    alumno_nombre = request.form.get("alumno")
    materia = request.form.get("materia")
    trimestre = request.form.get("trimestre")
    cal1 = request.form.get("cal1")

    config = configuracion.find_one({"tipo": "trimestre"}) or {}

    if config.get("estado") != "true":
        return "Evaluaciones cerradas"

    alumno = alumnos.find_one({"nombre": alumno_nombre})

    if alumno.get("enviado"):
        return "Ya enviadas"

    calificaciones = alumno.get("calificaciones", [])

    encontrada = False

    for c in calificaciones:
        if c.get("materia") == materia and c.get("trimestre") == trimestre:
            c["calificacion"] = float(cal1)
            encontrada = True

    if not encontrada:
        calificaciones.append({
            "materia": materia,
            "calificacion": float(cal1),
            "trimestre": trimestre
        })

    alumnos.update_one(
        {"nombre": alumno_nombre},
        {"$set": {"calificaciones": calificaciones}}
    )

    return redirect("/panel_maestro")


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

@maestro_bp.route("/guardar_calificaciones_ajax", methods=["POST"])
def guardar_calificaciones_ajax():

    if not verificar_maestro():
        return jsonify({"status": "error"})

    alumno_nombre = request.form.get("alumno")
    materia = request.form.get("materia")
    trimestre = request.form.get("trimestre")
    cal1 = request.form.get("cal1")

    config = configuracion.find_one({"tipo": "trimestre"}) or {}

    if config.get("estado") != "true":
        return jsonify({"status": "cerrado"})

    alumno = alumnos.find_one({"nombre": alumno_nombre})

    if alumno.get("enviado"):
        return jsonify({"status": "bloqueado"})

    calificaciones = alumno.get("calificaciones", [])

    encontrada = False

    for c in calificaciones:
        if c.get("materia") == materia and c.get("trimestre") == trimestre:
            c["calificacion"] = float(cal1)
            encontrada = True

    if not encontrada:
        calificaciones.append({
            "materia": materia,
            "calificacion": float(cal1),
            "trimestre": trimestre
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
# RESET POR ALUMNO
# =========================

@maestro_bp.route("/reset_alumno", methods=["POST"])
def reset_alumno():

    if not verificar_maestro():
        return jsonify({"status": "error"})

    nombre = request.form.get("alumno")
    trimestre = request.form.get("trimestre")

    alumno = alumnos.find_one({"nombre": nombre})

    nuevas = []

    for c in alumno.get("calificaciones", []):
        if c.get("trimestre") != trimestre:
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