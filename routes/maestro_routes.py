from flask import Blueprint, render_template, request, redirect, session, jsonify, send_file
from bson.objectid import ObjectId
from database.mongo import alumnos, maestros, reportes, horarios, configuracion
from datetime import datetime
from io import BytesIO

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
    # ANALYTICS (SEGURO)
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
# GUARDAR CALIFICACIONES
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
    trimestre = request.form.get("trimestre", "1")

    alumno = alumnos.find_one({"nombre": alumno_nombre})

    if not alumno:
        return redirect("/panel_maestro")

    # Sistema base (no se rompe)
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

    # Sistema nuevo
    if materia and cal1:

        try:
            calificacion = float(cal1)
        except:
            calificacion = 0

        calificaciones = alumno.get("calificaciones", [])

        encontrada = False

        for c in calificaciones:
            if c.get("materia") == materia and c.get("trimestre", "1") == trimestre:
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
# EXPORTAR EXCEL (ULTRA SEGURO)
# =========================

@maestro_bp.route("/exportar_excel")
def exportar_excel():

    if not verificar_maestro():
        return redirect("/")

    # 🔥 IMPORT LOCAL (NO ROMPE EL SISTEMA)
    try:
        from openpyxl import Workbook
    except:
        return "Excel no disponible (falta openpyxl)"

    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte"

    ws.append(["Alumno", "Promedio", "Estado"])

    for a in list(alumnos.find()):

        calificaciones = a.get("calificaciones", [])

        if calificaciones:
            try:
                promedio = sum([float(c.get("calificacion", 0)) for c in calificaciones]) / len(calificaciones)
            except:
                promedio = 0
        else:
            promedio = 0

        estado = "Excelente" if promedio >= 8 else "Riesgo" if promedio >= 6 else "Reprobado"

        ws.append([a.get("nombre",""), round(promedio, 2), estado])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="reporte.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


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
# AJAX
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