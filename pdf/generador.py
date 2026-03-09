from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

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
# GENERAR KARDEX
# ==============================

def generar_kardex(nombre):

    escuela, ciclo, director, direccion, escudo = obtener_config()

    carpeta = "pdf_generados"

    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

    ruta = f"{carpeta}/kardex_{nombre}.pdf"

    c = canvas.Canvas(ruta, pagesize=letter)

    # ESCUDO

    if escudo and os.path.exists(escudo):

        logo = ImageReader(escudo)

        c.drawImage(
            logo,
            40,
            700,
            width=80,
            height=80
        )

    # ENCABEZADO

    c.setFont("Helvetica-Bold", 16)
    c.drawString(140, 750, escuela)

    c.setFont("Helvetica", 12)
    c.drawString(140, 730, f"Ciclo Escolar: {ciclo}")
    c.drawString(140, 710, direccion)

    # TITULO

    c.setFont("Helvetica-Bold", 14)
    c.drawString(230, 670, "KARDEX ACADÉMICO")

    # ALUMNO

    c.setFont("Helvetica", 12)
    c.drawString(80, 630, f"Alumno: {nombre}")

    # TABLA

    c.drawString(80, 590, "Materia")
    c.drawString(350, 590, "Calificación")

    lista_materias = list(materias.find())

    y = 560

    for materia in lista_materias:

        nombre_materia = materia.get("nombre", "")
        calificacion = "—"

        c.drawString(80, y, nombre_materia)
        c.drawString(350, y, calificacion)

        y -= 25

    # FIRMA

    c.drawString(80, 120, f"Director: {director}")

    c.save()

    return ruta


# ==============================
# GENERAR BOLETA
# ==============================

def generar_boleta(nombre):

    escuela, ciclo, director, direccion, escudo = obtener_config()

    carpeta = "pdf_generados"

    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

    ruta = f"{carpeta}/boleta_{nombre}.pdf"

    c = canvas.Canvas(ruta, pagesize=letter)

    # ESCUDO

    if escudo and os.path.exists(escudo):

        logo = ImageReader(escudo)

        c.drawImage(
            logo,
            40,
            700,
            width=80,
            height=80
        )

    # ENCABEZADO

    c.setFont("Helvetica-Bold", 16)
    c.drawString(140, 750, escuela)

    c.setFont("Helvetica", 12)
    c.drawString(140, 730, f"Ciclo Escolar: {ciclo}")
    c.drawString(140, 710, direccion)

    # TITULO

    c.setFont("Helvetica-Bold", 14)
    c.drawString(220, 670, "BOLETA DE CALIFICACIONES")

    # ALUMNO

    c.setFont("Helvetica", 12)
    c.drawString(80, 630, f"Alumno: {nombre}")

    # TABLA

    c.drawString(80, 590, "Materia")
    c.drawString(350, 590, "Calificación")

    lista_materias = list(materias.find())

    y = 560

    for materia in lista_materias:

        nombre_materia = materia.get("nombre", "")
        calificacion = "—"

        c.drawString(80, y, nombre_materia)
        c.drawString(350, y, calificacion)

        y -= 25

    # FIRMA

    c.drawString(80, 120, f"Director: {director}")

    c.save()

    return ruta