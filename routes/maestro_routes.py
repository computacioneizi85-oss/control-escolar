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

    lista_horarios = list(horarios.find({"maestro": maestro["nombre"]}))

    if lista_horarios:
        grupos_horario = [h.get("grupo") for h in lista_horarios if h.get("grupo")]
        grupos = list(set(grupos + grupos_horario))

    lista_alumnos = list(alumnos.find({"grupo": {"$in": grupos}}))

    config = configuracion.find_one()

    return render_template(
        "panel_maestro.html",
        alumnos=lista_alumnos,
        grupos=grupos,
        horarios=lista_horarios,
        config=config
    )


# =========================
# GUARDAR CALIFICACIONES
# =========================

@maestro_bp.route("/guardar_calificaciones", methods=["POST"])
def guardar_calificaciones():

    if not verificar_maestro():
        return redirect("/")

    alumno = request.form.get("alumno")

    if not alumno:
        return redirect("/panel_maestro")

    alumnos.update_one(
        {"nombre": alumno},
        {
            "$set": {
                "cal1": request.form.get("cal1"),
                "cal2": request.form.get("cal2"),
                "cal3": request.form.get("cal3")
            }
        }
    )

    return redirect("/panel_maestro")


# =========================
# REGISTRAR ASISTENCIA (RÁPIDA)
# =========================

@maestro_bp.route("/registrar_asistencia", methods=["POST"])
def registrar_asistencia():

    if not verificar_maestro():
        return redirect("/")

    alumno = request.form.get("alumno")
    estado = request.form.get("estado")

    if not alumno or not estado:
        return redirect("/panel_maestro")

    alumnos.update_one(
        {"nombre": alumno},
        {
            "$push": {
                "asistencias": {
                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                    "estado": estado
                }
            }
        }
    )

    return redirect("/panel_maestro")


# =========================
# CREAR REPORTE DISCIPLINARIO
# =========================

@maestro_bp.route("/crear_reporte", methods=["POST"])
def crear_reporte():

    if not verificar_maestro():
        return redirect("/")

    alumno = request.form.get("alumno")
    comentario = request.form.get("comentario")

    if not alumno or not comentario:
        return redirect("/panel_maestro")

    reportes.insert_one({
        "alumno": alumno,
        "maestro": session["usuario"],
        "comentario": comentario,
        "estatus": "pendiente"
    })

    return redirect("/panel_maestro")


# =========================
# DESCARGAR EVALUACIONES
# =========================

@maestro_bp.route("/descargar_trimestre/<numero>")
def descargar_trimestre(numero):

    if not verificar_maestro():
        return redirect("/")

    config = configuracion.find_one()

    if not config:
        return "Evaluaciones no configuradas"

    campo = f"trimestre{numero}"

    if not config.get(campo, False):
        return "Este trimestre no está habilitado por dirección"

    return f"Descarga de evaluación del trimestre {numero} habilitada"


# =========================
# GUARDAR ASISTENCIA CON FECHA
# =========================

@maestro_bp.route("/guardar_asistencia_fecha", methods=["POST"])
def guardar_asistencia_fecha():

    if not verificar_maestro():
        return redirect("/")

    alumno = request.form.get("alumno")
    fecha = request.form.get("fecha")
    estado = request.form.get("estado")

    if not alumno or not fecha or not estado:
        return redirect("/panel_maestro")

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

    return redirect("/panel_maestro")


# =========================
# 🔥 ASISTENCIA AJAX (SEMAFORO)
# =========================

@maestro_bp.route("/guardar_asistencia_ajax", methods=["POST"])
def guardar_asistencia_ajax():

    if not verificar_maestro():
        return jsonify({"status": "error", "msg": "No autorizado"})

    alumno = request.form.get("alumno")
    estado = request.form.get("estado")
    fecha = request.form.get("fecha")

    if not alumno or not estado or not fecha:
        return jsonify({"status": "error", "msg": "Datos incompletos"})

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

    return jsonify({"status": "ok"})