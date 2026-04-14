from flask import Blueprint, render_template, request, redirect, session, jsonify, url_for, send_file

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

from bson.objectid import ObjectId
from datetime import datetime

from database.mongo import alumnos, maestros, horarios, configuracion, reportes, citatorios
from pdf.generador import generar_citatorio_pdf

maestro_bp = Blueprint("maestro", __name__)


def verificar_maestro():
    return session.get("rol") == "maestro"


# =========================
# PANEL MAESTRO
# =========================
@maestro_bp.route("/panel_maestro")
def panel_maestro():

    if not verificar_maestro():
        return redirect("/")

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}

    materias_maestro = maestro.get("materias", [])
    grupos_maestro = maestro.get("grupos", [])

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

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}
    materias_maestro = maestro.get("materias", [])

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

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}
    grupos = maestro.get("grupos", [])

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
        {"$push": {"asistencias": {"fecha": fecha, "estado": estado}}}
    )

    return jsonify({"status": "ok"})


# =========================
# REPORTES
# =========================
@maestro_bp.route("/reportes")
def ver_reportes_maestro():

    if not verificar_maestro():
        return redirect("/")

    lista_reportes = list(reportes.find({
        "maestro": session.get("usuario")
    }))

    lista_alumnos = list(alumnos.find())

    return render_template(
        "reportes_maestro.html",
        reportes=lista_reportes,
        alumnos=lista_alumnos
    )


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
        "estado": "pendiente"
    })

    return redirect(url_for("maestro.ver_reportes_maestro"))


@maestro_bp.route("/enviar_reportes_maestro", methods=["POST"])
def enviar_reportes_maestro():

    if not verificar_maestro():
        return redirect("/")

    reportes.update_many(
        {"maestro": session.get("usuario")},
        {"$set": {"estado": "enviado"}}
    )

    return redirect(url_for("maestro.ver_reportes_maestro"))


# =========================
# CITATORIOS
# =========================
@maestro_bp.route("/citatorios")
def ver_citatorios_maestro():

    if not verificar_maestro():
        return redirect("/")

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}
    grupos_maestro = maestro.get("grupos", [])

    lista_citatorios = list(citatorios.find({"grupo": {"$in": grupos_maestro}}))
    lista_alumnos = list(alumnos.find({"grupo": {"$in": grupos_maestro}}))

    return render_template(
        "citatorios_maestro.html",
        citatorios=lista_citatorios,
        alumnos=lista_alumnos
    )


@maestro_bp.route("/confirmar_asistencia/<id>")
def confirmar_asistencia_maestro(id):

    if not verificar_maestro():
        return redirect("/")

    citatorios.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estatus": "asistio"}}
    )

    return redirect("/citatorios")


@maestro_bp.route("/generar_citatorio/<id>")
def generar_citatorio_maestro(id):

    if not verificar_maestro():
        return redirect("/")

    citatorio = citatorios.find_one({"_id": ObjectId(id)})
    if not citatorio:
        return "No encontrado"

    pdf = generar_citatorio_pdf(citatorio)

    return send_file(pdf, mimetype='application/pdf', as_attachment=True)


@maestro_bp.route("/crear_citatorio", methods=["POST"])
def crear_citatorio_maestro():

    if not verificar_maestro():
        return redirect("/")

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


# =========================
# HORARIO
# =========================
@maestro_bp.route("/horario")
def ver_horario_maestro():

    if not verificar_maestro():
        return redirect("/")

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}
    materias_maestro = maestro.get("materias", [])

    lista_horarios = list(horarios.find({"materia": {"$in": materias_maestro}}))

    return render_template(
        "horario_maestro.html",
        horarios=lista_horarios
    )


@maestro_bp.route("/horario/pdf")
def generar_pdf_horario():

    if not verificar_maestro():
        return redirect("/")

    maestro = maestros.find_one({"usuario": session.get("usuario")})

    if not maestro:
        return redirect("/")

    materias_maestro = maestro.get("materias", [])

    # 🔥 si no tiene materias, evitar crash
    if not materias_maestro:
        return "El maestro no tiene materias asignadas"

    lista_horarios = list(
        horarios.find({"materia": {"$in": materias_maestro}})
    )

    # 🔥 si no hay horarios
    if not lista_horarios:
        return "No hay horario registrado"

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(180, 750, "HORARIO DEL MAESTRO")

    y = 700

    for h in lista_horarios:

        dia = str(h.get("dia", "N/A"))
        hora = str(h.get("hora", "N/A"))
        materia = str(h.get("materia", "N/A"))
        grupo = str(h.get("grupo", "N/A"))

        texto = f"{dia} | {hora} | {materia} | {grupo}"

        c.setFont("Helvetica", 10)
        c.drawString(50, y, texto)

        y -= 20

        # 🔥 evitar que se salga de la hoja
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = 750

    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name="horario_maestro.pdf"
    )