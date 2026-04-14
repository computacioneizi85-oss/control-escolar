from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from io import BytesIO
import base64
import os
from datetime import datetime
import uuid

from database.mongo import configuracion, alumnos


# ================= CONFIG =================
def obtener_config():
    config = configuracion.find_one() or {}

    return (
        config.get("escuela", "Nombre de la escuela"),
        config.get("ciclo", "Ciclo escolar"),
        config.get("director", "Director"),
        config.get("direccion", ""),
        config.get("escudo", None)
    )


def generar_folio():
    return str(uuid.uuid4())[:8].upper()


def fecha_actual():
    return datetime.now().strftime("%d/%m/%Y")


# ================= BASE PDF =================
def crear_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    return c, buffer


# ================= ESCUDO =================
def dibujar_escudo(c, escudo):

    if not escudo:
        return

    try:
        if isinstance(escudo, str) and len(escudo) > 100:
            img = ImageReader(BytesIO(base64.b64decode(escudo)))
        elif isinstance(escudo, str) and os.path.exists(escudo):
            img = ImageReader(escudo)
        else:
            return

        c.drawImage(img, 40, 730, width=60, height=60)

    except:
        pass


# ================= ENCABEZADO =================
def encabezado(c, escuela, ciclo, direccion, escudo, titulo):

    dibujar_escudo(c, escudo)

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(300, 770, escuela)

    c.setFont("Helvetica", 10)
    c.drawCentredString(300, 755, f"Ciclo Escolar: {ciclo}")
    c.drawCentredString(300, 740, direccion)

    c.line(40, 730, 550, 730)

    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(300, 705, titulo)

    c.setFont("Helvetica", 9)
    c.drawString(40, 715, f"Folio: {generar_folio()}")
    c.drawRightString(550, 715, f"Fecha: {fecha_actual()}")


# ================= FIRMA =================
def firma(c, director):
    c.line(200, 140, 400, 140)
    c.drawCentredString(300, 120, director)
    c.drawCentredString(300, 105, "Director")


# ================= FOTO =================
def dibujar_foto(c, foto):
    try:
        if foto and isinstance(foto, str) and len(foto) > 100:
            img = ImageReader(BytesIO(base64.b64decode(foto)))
            c.drawImage(img, 450, 630, width=80, height=80)
    except:
        pass


# ================= KARDEX =================
def generar_kardex(nombre):

    escuela, ciclo, director, direccion, escudo = obtener_config()
    c, buffer = crear_pdf()

    encabezado(c, escuela, ciclo, direccion, escudo, "KARDEX ACADÉMICO")

    alumno = alumnos.find_one({"nombre": nombre}) or {}

    c.setFont("Helvetica", 11)
    c.drawString(50, 670, f"Alumno: {nombre}")
    c.drawString(50, 650, f"Grupo: {alumno.get('grupo','')}")

    dibujar_foto(c, alumno.get("foto"))

    c.line(50, 630, 550, 630)

    y = 590
    suma = 0
    total = 0

    calificaciones = alumno.get("calificaciones", [])

    if calificaciones:
        for cal in calificaciones:
            materia = cal.get("materia", "")
            valor = float(cal.get("calificacion", 0))

            c.drawString(50, y, materia)
            c.drawString(320, y, str(valor))

            suma += valor
            total += 1
            y -= 25
    else:
        c.drawString(50, y, "Sin calificaciones registradas")

    promedio = round(suma / total, 2) if total else 0

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 20, f"Promedio general: {promedio}")

    firma(c, director)

    c.save()
    buffer.seek(0)
    return buffer


# ================= BOLETA =================
def generar_boleta(nombre):

    escuela, ciclo, director, direccion, escudo = obtener_config()
    c, buffer = crear_pdf()

    encabezado(c, escuela, ciclo, direccion, escudo, "BOLETA DE CALIFICACIONES")

    alumno = alumnos.find_one({"nombre": nombre}) or {}

    c.setFont("Helvetica", 11)
    c.drawString(50, 670, f"Alumno: {nombre}")
    c.drawString(50, 650, f"Grupo: {alumno.get('grupo','')}")

    dibujar_foto(c, alumno.get("foto"))

    c.line(50, 630, 550, 630)

    y = 590
    suma = 0
    total = 0

    for cal in alumno.get("calificaciones", []):
        materia = cal.get("materia", "")
        valor = float(cal.get("calificacion", 0))

        c.drawString(50, y, materia)
        c.drawString(320, y, str(valor))

        suma += valor
        total += 1
        y -= 25

    if total == 0:
        c.drawString(50, y, "Sin calificaciones")

    promedio = round(suma / total, 2) if total else 0

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 20, f"Promedio: {promedio}")

    firma(c, director)

    c.save()
    buffer.seek(0)
    return buffer


# ================= REPORTE =================
def generar_reporte_pdf(reporte):

    escuela, ciclo, director, direccion, escudo = obtener_config()
    c, buffer = crear_pdf()

    encabezado(c, escuela, ciclo, direccion, escudo, "REPORTE DISCIPLINARIO")

    c.setFont("Helvetica", 11)

    c.drawString(50, 660, f"Alumno: {reporte.get('alumno','')}")
    c.drawString(50, 640, f"Grupo: {reporte.get('grupo','')}")
    c.drawString(50, 620, f"Maestro: {reporte.get('maestro','')}")

    texto = reporte.get("comentario", "")

    y = 580
    for linea in texto.split("\n"):
        c.drawString(50, y, linea[:90])
        y -= 15

    firma(c, director)

    c.save()
    buffer.seek(0)
    return buffer


# ================= CITATORIO =================
def generar_citatorio_pdf(citatorio):

    escuela, ciclo, director, direccion, escudo = obtener_config()
    c, buffer = crear_pdf()

    encabezado(c, escuela, ciclo, direccion, escudo, "CITATORIO")

    c.setFont("Helvetica", 11)

    c.drawString(50, 660, f"Alumno: {citatorio.get('alumno','')}")
    c.drawString(50, 640, f"Grupo: {citatorio.get('grupo','')}")

    c.drawString(50, 600, "Se solicita su presencia por el siguiente motivo:")

    texto = citatorio.get("motivo", "")

    y = 580
    for linea in texto.split("\n"):
        c.drawString(50, y, linea[:90])
        y -= 15

    firma(c, director)

    c.save()
    buffer.seek(0)
    return buffer