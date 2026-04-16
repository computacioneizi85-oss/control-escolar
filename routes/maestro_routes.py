from flask import Blueprint, render_template, request, redirect, session, url_for, send_file
from bson.objectid import ObjectId
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from database.mongo import alumnos, maestros, horarios, configuracion, citatorios, avisos
from pdf.generador import generar_citatorio_pdf

maestro_bp = Blueprint("maestro", __name__)


# ================= SEGURIDAD =================
def verificar_maestro():
    return session.get("rol") == "maestro"


# ================= PANEL =================
@maestro_bp.route("/panel_maestro")
def panel_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}

    materias = maestro.get("materias", [])
    grupos = maestro.get("grupos", [])
    nombre = maestro.get("nombre", "").strip()
    usuario = maestro.get("usuario", "").strip()

    lista_horarios = list(horarios.find({
        "$or": [
            {"maestro": usuario},
            {"maestro": nombre},
            {"maestro": nombre.lower()},
            {"maestro": nombre.upper()}
        ]
    }))

    if not grupos:
        grupos = list(set([h.get("grupo") for h in lista_horarios if h.get("grupo")]))

    if not grupos:
        grupos = list(set([a.get("grupo") for a in alumnos.find()]))

    lista_alumnos = list(alumnos.find({"grupo": {"$in": grupos}}))

    config = configuracion.find_one({"tipo": "trimestre"}) or {
        "estado": "false",
        "trimestre": "1"
    }

    return render_template(
        "panel_maestro.html",
        alumnos=lista_alumnos,
        grupos=grupos,
        horarios=lista_horarios,
        materias=materias,
        config=config
    )


# ================= 🔔 AVISOS MAESTRO =================
@maestro_bp.route("/avisos_maestro")
def avisos_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}

    return render_template(
        "avisos_maestro.html",
        grupos=maestro.get("grupos", [])
    )


@maestro_bp.route("/crear_aviso_maestro", methods=["POST"])
def crear_aviso_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    avisos.insert_one({
        "tipo": "grupo",
        "grupo": request.form.get("grupo"),
        "titulo": request.form.get("titulo"),
        "mensaje": request.form.get("mensaje"),
        "fecha": datetime.now().strftime("%d/%m/%Y"),
        "maestro": session.get("usuario")
    })

    return redirect("/avisos_maestro")


# ================= HORARIO =================
@maestro_bp.route("/horario")
def ver_horario_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}

    nombre = maestro.get("nombre", "").strip()
    usuario = maestro.get("usuario", "").strip()

    lista_horarios = list(horarios.find({
        "$or": [
            {"maestro": usuario},
            {"maestro": nombre},
            {"maestro": nombre.lower()},
            {"maestro": nombre.upper()}
        ]
    }))

    return render_template("horario_maestro.html", horarios=lista_horarios)


# ================= PDF HORARIO =================
@maestro_bp.route("/horario/pdf")
def generar_pdf_horario():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    try:
        maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}

        nombre = maestro.get("nombre", "").upper()
        usuario = maestro.get("usuario", "")

        lista_horarios = list(horarios.find({
            "$or": [
                {"maestro": usuario},
                {"maestro": nombre},
                {"maestro": nombre.lower()}
            ]
        }))

        if not lista_horarios:
            return "No tienes horario asignado"

        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        horas = sorted(list(set([h.get("hora", "") for h in lista_horarios])))

        data = [["HORA"] + dias]

        for hora in horas:
            fila = [hora]

            for dia in dias:
                celda = ""

                for h in lista_horarios:
                    if h.get("hora") == hora and h.get("dia") == dia:
                        celda = f"{h.get('materia','')}\n{h.get('grupo','')}"

                fila.append(celda)

            data.append(fila)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)

        styles = getSampleStyleSheet()
        elementos = []

        elementos.append(Paragraph("<b>HORARIO ESCOLAR</b>", styles["Title"]))
        elementos.append(Spacer(1, 10))
        elementos.append(Paragraph(f"<b>MAESTRO:</b> {nombre}", styles["Normal"]))
        elementos.append(Spacer(1, 20))

        tabla = Table(data, repeatRows=1, rowHeights=28)

        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
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

    except Exception as e:
        return f"ERROR HORARIO PDF: {str(e)}"


# ================= CITATORIOS =================
@maestro_bp.route("/citatorios")
def ver_citatorios_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({"usuario": session.get("usuario")}) or {}
    grupos = maestro.get("grupos", [])

    lista_citatorios = list(citatorios.find({"grupo": {"$in": grupos}}))
    lista_alumnos = list(alumnos.find({"grupo": {"$in": grupos}}))

    return render_template(
        "citatorios_maestro.html",
        citatorios=lista_citatorios,
        alumnos=lista_alumnos
    )


@maestro_bp.route("/confirmar_asistencia/<id>")
def confirmar_asistencia_maestro(id):

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    citatorios.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estatus": "asistio"}}
    )

    return redirect("/citatorios")


@maestro_bp.route("/generar_citatorio/<id>")
def generar_citatorio_maestro(id):

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    try:
        citatorio = citatorios.find_one({"_id": ObjectId(id)})

        if not citatorio:
            return "No encontrado"

        pdf = generar_citatorio_pdf(citatorio)
        pdf.seek(0)

        return send_file(
            pdf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name="citatorio.pdf"
        )

    except Exception as e:
        return f"ERROR PDF MAESTRO: {str(e)}"


# ================= CREAR CITATORIO =================
@maestro_bp.route("/crear_citatorio", methods=["POST"])
def crear_citatorio_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    citatorios.insert_one({
        "alumno": request.form.get("alumno"),
        "grupo": request.form.get("grupo"),
        "motivo": request.form.get("motivo"),
        "fecha_cita": request.form.get("fecha"),
        "hora": request.form.get("hora"),
        "estatus": "pendiente",
        "enterado": False,
        "maestro": session.get("usuario")
    })

    return redirect("/citatorios")