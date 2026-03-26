from flask import Blueprint, render_template, request, redirect, session, jsonify, url_for
from database.mongo import alumnos, maestros, horarios, configuracion, reportes

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

    materias_maestro = maestro.get("materias", []) or []
    grupos_maestro = maestro.get("grupos", []) or []

    lista_horarios = list(horarios.find({
        "materia": {"$in": materias_maestro}
    }))

    grupos = list(set([
        h.get("grupo") for h in lista_horarios if h.get("grupo")
    ]))

    if not grupos:
        grupos = grupos_maestro

    if not grupos:
        grupos = list(set([a.get("grupo") for a in alumnos.find()]))

    lista_alumnos = list(alumnos.find({
        "grupo": {"$in": grupos}
    }))

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

    if not alumno_nombre or not materia or not trimestre or cal1 is None:
        return jsonify({"status": "error"})

    config = configuracion.find_one({"tipo": "trimestre"}) or {}
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
# ASISTENCIAS
# =========================
@maestro_bp.route("/guardar_asistencia_ajax", methods=["POST"])
def guardar_asistencia_ajax():

    if not verificar_maestro():
        return jsonify({"status": "error"})

    alumno_nombre = request.form.get("alumno")
    estado = request.form.get("estado")
    fecha = request.form.get("fecha")

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


# =========================
# 🔥 VER REPORTES (NUEVO)
# =========================
@maestro_bp.route("/reportes")
def ver_reportes_maestro():

    if not verificar_maestro():
        return redirect("/")

    maestro = maestros.find_one({"usuario": session.get("usuario")})

    lista_reportes = list(reportes.find({
        "maestro": session.get("usuario")
    }))

    lista_alumnos = list(alumnos.find())

    return render_template(
        "reportes_maestro.html",
        reportes=lista_reportes,
        alumnos=lista_alumnos
    )


# =========================
# 🔥 CREAR REPORTE (NUEVO)
# =========================
from datetime import datetime

@maestro_bp.route("/crear_reporte", methods=["POST"])
def crear_reporte():

    if not verificar_maestro():
        return redirect("/")

    reportes.insert_one({
        "alumno": request.form.get("alumno"),
        "grupo": request.form.get("grupo"),
        "comentario": request.form.get("comentario"),
        "maestro": session.get("usuario"),
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "estado": "pendiente",
        "firma_direccion": None
    })

    return redirect(url_for("maestro.ver_reportes_maestro"))


# =========================
# 🔥 ENVIAR A DIRECCIÓN
# =========================
@maestro_bp.route("/enviar_reportes_maestro", methods=["POST"])
def enviar_reportes_maestro():

    if not verificar_maestro():
        return redirect("/")

    reportes.update_many(
        {"maestro": session.get("usuario")},
        {"$set": {"estado": "enviado"}}
    )

    return redirect(url_for("maestro.ver_reportes_maestro"))