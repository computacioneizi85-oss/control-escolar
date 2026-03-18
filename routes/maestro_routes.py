from flask import Blueprint, render_template, request, redirect, session, jsonify
from bson.objectid import ObjectId
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

    # =========================
    # 🔥 ANALYTICS PRO (SEGURO)
    # =========================

    promedios = []

    for a in lista_alumnos:

        calificaciones = a.get("calificaciones", [])

        if calificaciones:
            suma = sum([c.get("calificacion", 0) for c in calificaciones])
            promedio = round(suma / len(calificaciones), 2)
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
            "nombre": a["nombre"],
            "promedio": promedio
        })

    # 🔥 PROMEDIO DEL GRUPO
    if promedios:
        promedio_grupo = round(
            sum([p["promedio"] for p in promedios]) / len(promedios), 2
        )
    else:
        promedio_grupo = 0

    # 🔥 TOP 5
    top_alumnos = sorted(
        promedios,
        key=lambda x: x["promedio"],
        reverse=True
    )[:5]

    # 🔥 ALUMNOS EN RIESGO
    riesgo = [a for a in lista_alumnos if a["estado"] != "excelente"]

    config = configuracion.find_one()

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
# 🔥 GUARDAR CALIFICACIONES (DOBLE SISTEMA)
# =========================

@maestro_bp.route("/guardar_calificaciones", methods=["POST"])
def guardar_calificaciones():

    if not verificar_maestro():
        return redirect("/")

    alumno_nombre = request.form.get("alumno")

    if not alumno_nombre:
        return redirect("/panel_maestro")

    cal1 = request.form.get("cal1")
    cal2 = request.form.get("cal2")
    cal3 = request.form.get("cal3")

    materia = request.form.get("materia")

    alumno = alumnos.find_one({"nombre": alumno_nombre})

    if not alumno:
        return redirect("/panel_maestro")

    # SISTEMA ANTIGUO
    alumnos.update_one(
        {"nombre": alumno_nombre},
        {
            "$set": {
                "cal1": cal1,
                "cal2": cal2,
                "cal3": cal3
            }
        }
    )

    # SISTEMA NUEVO
    if materia and cal1:

        try:
            calificacion = float(cal1)
        except:
            calificacion = 0

        calificaciones = alumno.get("calificaciones", [])

        encontrada = False

        for c in calificaciones:
            if c["materia"] == materia:
                c["calificacion"] = calificacion
                encontrada = True

        if not encontrada:
            calificaciones.append({
                "materia": materia,
                "calificacion": calificacion
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
# REPORTE
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
# TRIMESTRE
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
# ASISTENCIA CON FECHA
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
# AJAX
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