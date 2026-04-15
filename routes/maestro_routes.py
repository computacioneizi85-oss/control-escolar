from flask import Blueprint, render_template, request, redirect, session, jsonify, url_for, send_file

from bson.objectid import ObjectId
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from database.mongo import alumnos, maestros, horarios, configuracion, reportes, citatorios
from pdf.generador import generar_citatorio_pdf

maestro_bp = Blueprint("maestro", __name__)


def verificar_maestro():
    return session.get("rol") == "maestro"


# ================= PANEL =================
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


# ================= HORARIO =================
@maestro_bp.route("/horario")
def ver_horario_maestro():

    if not verificar_maestro():
        return redirect("/")

    usuario = session.get("usuario")
    maestro = maestros.find_one({"usuario": usuario}) or {}

    nombre = maestro.get("nombre")

    lista_horarios = list(
        horarios.find({
            "$or": [
                {"maestro": usuario},
                {"maestro": nombre}
            ]
        })
    )

    return render_template("horario_maestro.html", horarios=lista_horarios)


# ================= PDF HORARIO PRO MAX 🔥 =================
@maestro_bp.route("/horario/pdf")
def generar_pdf_horario():

    if not verificar_maestro():
        return redirect("/")

    usuario = session.get("usuario")
    maestro = maestros.find_one({"usuario": usuario}) or {}

    nombre = maestro.get("nombre", "").upper()

    lista_horarios = list(
        horarios.find({
            "$or": [
                {"maestro": usuario},
                {"maestro": maestro.get("nombre")}
            ]
        })
    )

    if not lista_horarios:
        return "No tienes horario asignado"

    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    horas = sorted(list(set([h["hora"] for h in lista_horarios])))

    data = [["HORA"] + dias]

    for hora in horas:
        fila = [hora]

        for dia in dias:
            celda = ""

            for h in lista_horarios:
                if h["hora"] == hora and h["dia"] == dia:
                    celda = f"{h['materia']}\n{h['grupo']}"

            fila.append(celda)

        data.append(fila)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    elementos = []

    # 🔥 TITULO
    elementos.append(Paragraph("<b>HORARIO 2025 - 2026</b>", styles["Title"]))
    elementos.append(Spacer(1, 10))

    # 🔥 MAESTRO
    elementos.append(Paragraph(f"<b>MAESTRO:</b> {nombre}", styles["Normal"]))
    elementos.append(Spacer(1, 20))

    # 🔥 TABLA
    tabla = Table(data, repeatRows=1)

    tabla.setStyle(TableStyle([

        # ENCABEZADO
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

        # CENTRADO
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        # GRID
        ("GRID", (0, 0), (-1, -1), 1, colors.black),

        # FILAS
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),

        # ALTURA
        ("ROWHEIGHT", (0, 0), (-1, -1), 28),

        # ESPACIADO
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))

    elementos.append(tabla)

    doc.build(elementos)

    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name="horario_oficial.pdf"
    )


# ================= CITATORIOS =================
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