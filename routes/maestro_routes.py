from flask import Blueprint, render_template, request, redirect, session, jsonify
from database.mongo import alumnos, maestros, horarios, configuracion

maestro_bp = Blueprint("maestro", __name__)


def verificar_maestro():
    return "rol" in session and session["rol"] == "maestro"


# =========================
# PANEL MAESTRO
# =========================
@maestro_bp.route("/panel_maestro")
def panel_maestro():

    if not verificar_maestro():
        return redirect("/")

    maestro = maestros.find_one({"usuario": session.get("usuario")})

    if not maestro:
        return redirect("/")

    # 🔥 asegurar listas
    materias_maestro = maestro.get("materias", []) or []
    grupos_maestro = maestro.get("grupos", []) or []

    # 🔥 buscar horarios por materias
    lista_horarios = list(horarios.find({
        "materia": {"$in": materias_maestro}
    }))

    # 🔥 obtener grupos desde horarios
    grupos = list(set([
        h.get("grupo") for h in lista_horarios if h.get("grupo")
    ]))

    # 🔥 fallback SI NO HAY HORARIOS
    if not grupos:
        grupos = grupos_maestro

    # 🔥 SI AUN NO HAY GRUPOS → evitar pantalla vacía
    if not grupos:
        grupos = list(set([a.get("grupo") for a in alumnos.find()]))

    # 🔥 obtener alumnos
    lista_alumnos = list(alumnos.find({
        "grupo": {"$in": grupos}
    }))

    # 🔥 configuración segura
    config = configuracion.find_one({"tipo": "trimestre"}) or {
        "estado": "false",
        "trimestre": "1"
    }

    return render_template(
        "panel_maestro.html",
        alumnos=lista_alumnos,
        grupos=grupos,
        horarios=lista_horarios,
        materias=materias_maestro,
        config=config
    )


# =========================
# GUARDAR CALIFICACIONES
# =========================
@maestro_bp.route("/guardar_calificaciones_ajax", methods=["POST"])
def guardar_calificaciones_ajax():

    if not verificar_maestro():
        return jsonify({"status": "error"})

    maestro = maestros.find_one({"usuario": session.get("usuario")})
    materias_maestro = maestro.get("materias", []) or []

    alumno_nombre = request.form.get("alumno")
    materia = request.form.get("materia")
    trimestre = str(request.form.get("trimestre"))
    cal1 = request.form.get("cal1")

    # 🔥 validación básica
    if not alumno_nombre or not materia or not trimestre or cal1 is None:
        return jsonify({"status": "error"})

    config = configuracion.find_one({"tipo": "trimestre"}) or {}

    # 🔥 aceptar boolean o string
    estado = str(config.get("estado")).lower()

    if estado != "true":
        return jsonify({"status": "cerrado"})

    if materia not in materias_maestro:
        return jsonify({"status": "prohibido"})

    alumno = alumnos.find_one({"nombre": alumno_nombre})

    if not alumno:
        return jsonify({"status": "error"})

    if alumno.get("enviado"):
        return jsonify({"status": "bloqueado"})

    try:
        cal1 = float(cal1)
    except:
        return jsonify({"status": "error"})

    calificaciones = alumno.get("calificaciones", [])

    encontrada = False

    for c in calificaciones:
        if c.get("materia") == materia and str(c.get("trimestre")) == trimestre:
            c["calificacion"] = cal1
            encontrada = True

    if not encontrada:
        calificaciones.append({
            "materia": materia,
            "calificacion": cal1,
            "trimestre": trimestre
        })

    alumnos.update_one(
        {"_id": alumno["_id"]},
        {"$set": {"calificaciones": calificaciones}}
    )

    return jsonify({"status": "ok"})


# =========================
# ENVIAR CALIFICACIONES
# =========================
@maestro_bp.route("/enviar_calificaciones")
def enviar_calificaciones():

    if not verificar_maestro():
        return redirect("/")

    maestro = maestros.find_one({"usuario": session.get("usuario")})
    grupos = maestro.get("grupos", []) or []

    alumnos.update_many(
        {"grupo": {"$in": grupos}},
        {"$set": {"enviado": True}}
    )

    return redirect("/panel_maestro")


# =========================
# RESET POR ALUMNO
# =========================
@maestro_bp.route("/reset_alumno", methods=["POST"])
def reset_alumno():

    if not verificar_maestro():
        return jsonify({"status": "error"})

    nombre = request.form.get("alumno")
    trimestre = str(request.form.get("trimestre"))

    alumno = alumnos.find_one({"nombre": nombre})

    if not alumno:
        return jsonify({"status": "error"})

    nuevas = [
        c for c in alumno.get("calificaciones", [])
        if str(c.get("trimestre")) != trimestre
    ]

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


# =========================
# ASISTENCIAS
# =========================
@maestro_bp.route("/guardar_asistencia_ajax", methods=["POST"])
def guardar_asistencia_ajax():

    if not verificar_maestro():
        return jsonify({"status": "error"})

    alumno_nombre = request.form.get("alumno")
    estado = request.form.get("estado")
    fecha = request.form.get("fecha")

    if not alumno_nombre or not fecha:
        return jsonify({"status": "error"})

    alumno = alumnos.find_one({"nombre": alumno_nombre})

    if not alumno:
        return jsonify({"status": "error"})

    alumnos.update_one(
        {"_id": alumno["_id"]},
        {
            "$push": {
                "asistencias": {
                    "fecha": fecha,
                    "estado": estado
                }
            }
        }
    )

    return jsonify({"status": "ok"})