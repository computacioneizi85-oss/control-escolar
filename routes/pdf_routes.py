from flask import Blueprint, send_file
from database.mongo import alumnos, calificaciones
from reportlab.pdfgen import canvas
from io import BytesIO

pdf_bp = Blueprint("pdf", __name__)

# =========================
# KARDEX PDF
# =========================

@pdf_bp.route("/kardex/<nombre>")
def kardex(nombre):

    alumno = alumnos.find_one({"nombre": nombre})
    califs = calificaciones.find({"alumno": nombre})

    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 800, "KARDEX ESCOLAR")

    p.setFont("Helvetica", 12)
    p.drawString(100, 760, f"Alumno: {nombre}")

    y = 720

    for c in califs:

        materia = c.get("materia", "")
        calificacion = c.get("calificacion", "")

        p.drawString(100, y, f"{materia} : {calificacion}")

        y -= 20

    p.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"kardex_{nombre}.pdf",
        mimetype="application/pdf"
    )


# =========================
# BOLETA PDF
# =========================

@pdf_bp.route("/boleta/<nombre>")
def boleta(nombre):

    califs = calificaciones.find({"alumno": nombre})

    buffer = BytesIO()
    p = canvas.Canvas(buffer)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 800, "BOLETA DE CALIFICACIONES")

    p.setFont("Helvetica", 12)
    p.drawString(100, 760, f"Alumno: {nombre}")

    y = 720

    for c in califs:

        materia = c.get("materia", "")
        calificacion = c.get("calificacion", "")

        p.drawString(100, y, f"{materia} : {calificacion}")

        y -= 20

    p.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"boleta_{nombre}.pdf",
        mimetype="application/pdf"
    )