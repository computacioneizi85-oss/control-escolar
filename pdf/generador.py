from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from io import BytesIO
import base64
import os

from database.mongo import configuracion, materias


# ==============================
# CONFIGURACIÓN
# ==============================

def obtener_config():

    config = configuracion.find_one()

    if config:
        escuela = config.get("escuela", "Nombre de la escuela")
        ciclo = config.get("ciclo", "Ciclo escolar")
        director = config.get("director", "Director")
        direccion = config.get("direccion", "")
        escudo = config.get("escudo", None)
    else:
        escuela = "Nombre de la escuela"
        ciclo = "Ciclo escolar"
        director = "Director"
        direccion = ""
        escudo = None

    return escuela, ciclo, director, direccion, escudo


# ==============================
# ESCUDO (BASE64 o RUTA)
# ==============================

def dibujar_escudo(c, escudo):

    if not escudo:
        return

    try:
        # 🔥 BASE64
        if len(escudo) > 100:
            imagen_bytes = base64.b64decode(escudo)
            imagen_stream = BytesIO(imagen_bytes)
            logo = ImageReader(imagen_stream)

        # 🔥 RUTA (por compatibilidad)
        elif os.path.exists(escudo):
            logo = ImageReader(escudo)

        else:
            return

        c.drawImage(logo, 40, 730, width=60, height=60)

    except:
        pass


# ==============================
# ENCABEZADO PROFESIONAL
# ==============================

def encabezado(c, escuela, ciclo, direccion, escudo):

    dibujar_escudo(c, escudo)

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(300, 770, escuela)

    c.setFont("Helvetica", 10)
    c.drawCentredString(300, 755, f"Ciclo Escolar: {ciclo}")
    c.drawCentredString(300, 740, direccion)

    c.line(40, 730, 550, 730)


# ==============================
# CREAR PDF EN MEMORIA
# ==============================

def crear_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    return c, buffer


# ==============================
# KARDEX
# ==============================

def generar_kardex(nombre):

    escuela, ciclo, director, direccion, escudo = obtener_config()
    c, buffer = crear_pdf()

    encabezado(c, escuela, ciclo, direccion, escudo)

    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(300, 700, "KARDEX ACADÉMICO")

    c.setFont("Helvetica", 11)
    c.drawString(50, 670, f"Alumno: {nombre}")

    c.line(50, 660, 550, 660)

    c.drawString(50, 640, "Materia")
    c.drawString(400, 640, "Calificación")

    y = 620

    for materia in list(materias.find()):
        c.drawString(50, y, materia.get("nombre", ""))
        c.drawString(420, y, "—")
        y -= 25

    c.line(50, 140, 250, 140)
    c.drawString(50, 120, f"Director: {director}")

    c.save()
    buffer.seek(0)

    return buffer


# ==============================
# BOLETA
# ==============================

def generar_boleta(nombre):

    escuela, ciclo, director, direccion, escudo = obtener_config()
    c, buffer = crear_pdf()

    encabezado(c, escuela, ciclo, direccion, escudo)

    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(300, 700, "BOLETA DE CALIFICACIONES")

    c.setFont("Helvetica", 11)
    c.drawString(50, 670, f"Alumno: {nombre}")

    c.line(50, 660, 550, 660)

    c.drawString(50, 640, "Materia")
    c.drawString(400, 640, "Calificación")

    y = 620

    for materia in list(materias.find()):
        c.drawString(50, y, materia.get("nombre", ""))
        c.drawString(420, y, "—")
        y -= 25

    c.line(50, 140, 250, 140)
    c.drawString(50, 120, f"Director: {director}")

    c.save()
    buffer.seek(0)

    return buffer


# ==============================
# REPORTE DISCIPLINARIO
# ==============================

def generar_reporte_pdf(reporte):

    escuela, ciclo, director, direccion, escudo = obtener_config()
    c, buffer = crear_pdf()

    encabezado(c, escuela, ciclo, direccion, escudo)

    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(300, 700, "REPORTE DISCIPLINARIO")

    c.setFont("Helvetica", 11)

    c.drawString(50, 660, f"Alumno: {reporte.get('alumno','')}")
    c.drawString(50, 640, f"Maestro: {reporte.get('maestro','')}")

    c.drawString(50, 610, "Comentario:")
    c.drawString(50, 590, reporte.get("comentario",""))

    c.drawString(50, 550, "Estado: Autorizado")

    c.line(50, 140, 250, 140)
    c.drawString(50, 120, f"Director: {director}")

    c.save()
    buffer.seek(0)

    return buffer


# ==============================
# CITATORIO
# ==============================

def generar_citatorio_pdf(citatorio):

    escuela, ciclo, director, direccion, escudo = obtener_config()
    c, buffer = crear_pdf()

    encabezado(c, escuela, ciclo, direccion, escudo)

    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(300, 700, "CITATORIO A PADRES DE FAMILIA")

    c.setFont("Helvetica", 11)

    c.drawString(50, 660, f"Alumno: {citatorio.get('alumno','')}")
    c.drawString(50, 640, f"Grupo: {citatorio.get('grupo','')}")

    c.drawString(50, 610, "Motivo:")
    c.drawString(50, 590, citatorio.get("motivo",""))

    c.drawString(50, 550, f"Fecha: {citatorio.get('fecha_cita','')}")
    c.drawString(50, 530, f"Hora: {citatorio.get('hora','')}")

    c.drawString(50, 500, "Se solicita la presencia del padre, madre o tutor.")

    c.line(50, 140, 250, 140)
    c.drawString(50, 120, f"Dirección - {director}")

    c.save()
    buffer.seek(0)

    return buffer