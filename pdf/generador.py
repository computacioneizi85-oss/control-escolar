from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from io import BytesIO
import os

from database.mongo import configuracion, materias


# ==============================
# OBTENER CONFIGURACION ESCUELA
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
# DIBUJAR ESCUDO
# ==============================

def dibujar_escudo(c, escudo):

    if escudo and os.path.exists(escudo):

        try:
            logo = ImageReader(escudo)

            c.drawImage(
                logo,
                40,
                700,
                width=80,
                height=80
            )

        except:
            pass


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

    dibujar_escudo(c, escudo)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(140, 750, escuela)

    c.setFont("Helvetica", 12)
    c.drawString(140, 730, f"Ciclo Escolar: {ciclo}")
    c.drawString(140, 710, direccion)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(230, 670, "KARDEX ACADÉMICO")

    c.setFont("Helvetica", 12)
    c.drawString(80, 630, f"Alumno: {nombre}")

    c.drawString(80, 590, "Materia")
    c.drawString(350, 590, "Calificación")

    lista_materias = list(materias.find())

    y = 560

    for materia in lista_materias:
        c.drawString(80, y, materia.get("nombre", ""))
        c.drawString(350, y, "—")
        y -= 25

    c.drawString(80, 120, f"Director: {director}")

    c.save()
    buffer.seek(0)

    return buffer


# ==============================
# BOLETA
# ==============================

def generar_boleta(nombre):

    escuela, ciclo, director, direccion, escudo = obtener_config()

    c, buffer = crear_pdf()

    dibujar_escudo(c, escudo)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(140, 750, escuela)

    c.setFont("Helvetica", 12)
    c.drawString(140, 730, f"Ciclo Escolar: {ciclo}")
    c.drawString(140, 710, direccion)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(220, 670, "BOLETA DE CALIFICACIONES")

    c.setFont("Helvetica", 12)
    c.drawString(80, 630, f"Alumno: {nombre}")

    c.drawString(80, 590, "Materia")
    c.drawString(350, 590, "Calificación")

    lista_materias = list(materias.find())

    y = 560

    for materia in lista_materias:
        c.drawString(80, y, materia.get("nombre", ""))
        c.drawString(350, y, "—")
        y -= 25

    c.drawString(80, 120, f"Director: {director}")

    c.save()
    buffer.seek(0)

    return buffer


# ==============================
# REPORTE
# ==============================

def generar_reporte_pdf(reporte):

    escuela, ciclo, director, direccion, escudo = obtener_config()

    c, buffer = crear_pdf()

    dibujar_escudo(c, escudo)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(140, 750, escuela)

    c.setFont("Helvetica", 12)
    c.drawString(140, 730, f"Ciclo Escolar: {ciclo}")
    c.drawString(140, 710, direccion)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, 670, "REPORTE DISCIPLINARIO")

    c.setFont("Helvetica", 12)

    c.drawString(80, 620, f"Alumno: {reporte.get('alumno','')}")
    c.drawString(80, 600, f"Maestro: {reporte.get('maestro','')}")
    c.drawString(80, 580, f"Comentario: {reporte.get('comentario','')}")

    c.drawString(80, 540, "Estado: Autorizado")

    c.drawString(80, 120, f"Director: {director}")

    c.save()
    buffer.seek(0)

    return buffer


# ==============================
# CITATORIO
# ==============================

def generar_citatorio_pdf(citatorio):

    escuela, ciclo, director, direccion, escudo = obtener_config()

    c, buffer = crear_pdf()

    dibujar_escudo(c, escudo)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(140, 750, escuela)

    c.setFont("Helvetica", 12)
    c.drawString(140, 730, f"Ciclo Escolar: {ciclo}")
    c.drawString(140, 710, direccion)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, 670, "CITATORIO A PADRES DE FAMILIA")

    c.setFont("Helvetica", 12)

    c.drawString(80, 620, f"Alumno: {citatorio.get('alumno','')}")
    c.drawString(80, 600, f"Grupo: {citatorio.get('grupo','')}")

    c.drawString(80, 560, "Motivo:")
    c.drawString(80, 540, citatorio.get("motivo",""))

    c.drawString(80, 500, f"Fecha: {citatorio.get('fecha_cita','')}")
    c.drawString(80, 480, f"Hora: {citatorio.get('hora','')}")

    c.drawString(80, 420, "Se solicita la presencia del padre, madre o tutor.")

    c.drawString(80, 200, "____________________________")
    c.drawString(80, 180, f"Dirección - {director}")

    c.save()
    buffer.seek(0)

    return buffer