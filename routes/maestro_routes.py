from flask import Blueprint, render_template, request, redirect, session, jsonify
from database.mongo import alumnos, maestros, reportes, horarios, configuracion
from datetime import datetime

maestro_bp = Blueprint("maestro", __name__)


# =========================
# VERIFICAR MAESTRO
# =========================

def verificar_maestro():
    return "rol" in session and session["rol"] == "maestro"


# =========================
# PANEL DEL MAESTRO
# =========================

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

    # 🔥 CONFIGURACIÓN CORRECTA
    config = configuracion.find_one({"tipo": "trimestre"}) or {}

    # =========================
    # ANALYTICS (NO SE TOCA)
    # =========================

    promedios = []

    for a in lista_alumnos:

        calificaciones = a.get("calificaciones", [])

        if calificaciones:
            try:
                suma = sum([float(c.get("calificacion", 0)) for c in calificaciones])
                promedio = round(suma / len(calificaciones), 2)
            except:
                promedio = 0
        else:
            promedio = 0

        a["promedio"] = promedio

        if promedio >= 8:
            a["estado"] = "excelente"
        elif promedio >= 6:
            a["estado"] = "riesgo"
        else:
            a["estado"] = "reprobado"

        promedios.append({
            "nombre": a.get("nombre", ""),
            "promedio": promedio
        })

    promedio_grupo = round(
        sum([p["promedio"] for p in promedios]) / len(promedios), 2
    ) if promedios else 0

    top_alumnos = sorted(promedios, key=lambda x: x["promedio"], reverse=True)[:5]

    riesgo = [a for a in lista_alumnos if a.get("estado") != "excelente"]

    return render_template(
        "panel_maestro.html",
        alumnos=lista_alumnos,
        grupos=grupos,
        horarios=lista_horarios,
        config=config,
        promedio_grupo=promedio_grupo,
        top_alumnos=top_alumnos,
        riesgo=riesgo
    )


# =========================
# 🔥 GUARDAR CALIFICACIONES (ESTABLE)
# =========================

@maestro_bp.route("/guardar_calificaciones", methods=["POST"])
def guardar_calificaciones():

    if not verificar_maestro():
        return redirect("/")

    alumno_nombre = request.form.get("alumno")
    materia = request.form.get("materia")
    trimestre = request.form.get("trimestre")
    cal1 = request.form.get("cal1")

    if not alumno_nombre or not materia or not cal1:
        return redirect("/panel_maestro")

    # 🔒 VALIDAR SI EL TRIMESTRE ESTÁ ABIERTO
    config = configuracion.find_one({"tipo": "trimestre"}) or {}

    if config.get("estado") != "true":
        return "Evaluaciones cerradas"

    try:
        calificacion = float(cal1)
    except:
        calificacion = 0

    alumno = alumnos.find_one({"nombre": alumno_nombre})

    if not alumno:
        return redirect("/panel_maestro")

    calificaciones = alumno.get("calificaciones", [])

    encontrada = False

    for c in calificaciones:
        if c.get("materia") == materia and c.get("trimestre") == trimestre:
            c["calificacion"] = calificacion
            encontrada = True

    if not encontrada:
        calificaciones.append({
            "materia": materia,
            "calificacion": calificacion,
            "trimestre": trimestre
        })

    alumnos.update_one(
        {"nombre": alumno_nombre},
        {"$set": {"calificaciones": calificaciones}}
    )

    return redirect("/panel_maestro")


# =========================
# ASISTENCIA
# =========================

@maestro_bp.route("/registrar_asistencia", methods=["POST"])
def registrar_asistencia():

    if not verificar_maestro():
        return redirect("/")

    alumnos.update_one(
        {"nombre": request.form.get("alumno")},
        {"$push": {"asistencias": {
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "estado": request.form.get("estado")
        }}}
    )

    return redirect("/panel_maestro")


# =========================
# REPORTE
# =========================

@maestro_bp.route("/crear_reporte", methods=["POST"])
def crear_reporte():

    if not verificar_maestro():
        return redirect("/")

    reportes.insert_one({
        "alumno": request.form.get("alumno"),
        "maestro": session["usuario"],
        "comentario": request.form.get("comentario"),
        "estatus": "pendiente"
    })

    return redirect("/panel_maestro")


# =========================
# AJAX ASISTENCIA
# =========================

@maestro_bp.route("/guardar_asistencia_ajax", methods=["POST"])
def guardar_asistencia_ajax():

    if not verificar_maestro():
        return jsonify({"status": "error"})

    alumnos.update_one(
        {"nombre": request.form.get("alumno")},
        {"$push": {"asistencias": {
            "fecha": request.form.get("fecha"),
            "estado": request.form.get("estado")
        }}}
    )

    return jsonify({"status": "ok"})