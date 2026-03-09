from flask import Blueprint, render_template, request, redirect, session
from database.mongo import alumnos, maestros, reportes
from datetime import datetime

maestro_bp = Blueprint("maestro", __name__)


# =========================
# VERIFICAR MAESTRO
# =========================

def verificar_maestro():

    if "rol" not in session:
        return False

    if session["rol"] != "maestro":
        return False

    return True


# =========================
# PANEL DEL MAESTRO
# =========================

@maestro_bp.route("/panel_maestro")
def panel_maestro():

    if not verificar_maestro():
        return redirect("/")

    maestro = maestros.find_one({"usuario": session["usuario"]})

    grupos = maestro.get("grupos", [])

    lista_alumnos = list(alumnos.find({"grupo": {"$in": grupos}}))

    return render_template(
        "panel_maestro.html",
        alumnos=lista_alumnos,
        grupos=grupos
    )


# =========================
# GUARDAR CALIFICACIONES
# =========================

@maestro_bp.route("/guardar_calificaciones", methods=["POST"])
def guardar_calificaciones():

    if not verificar_maestro():
        return redirect("/")

    alumno = request.form.get("alumno")

    cal1 = request.form.get("cal1")
    cal2 = request.form.get("cal2")
    cal3 = request.form.get("cal3")

    alumnos.update_one(
        {"nombre": alumno},
        {
            "$set": {
                "cal1": cal1,
                "cal2": cal2,
                "cal3": cal3
            }
        }
    )

    return redirect("/panel_maestro")


# =========================
# REGISTRAR ASISTENCIA
# =========================

@maestro_bp.route("/registrar_asistencia", methods=["POST"])
def registrar_asistencia():

    if not verificar_maestro():
        return redirect("/")

    alumno = request.form.get("alumno")
    estado = request.form.get("estado")

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

    reportes.insert_one({

        "alumno": alumno,
        "maestro": session["usuario"],
        "comentario": comentario,
        "estatus": "pendiente"

    })

    return redirect("/panel_maestro")