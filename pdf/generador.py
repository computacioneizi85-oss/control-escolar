from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

from database.mongo import configuracion, materias


# ==============================
# OBTENER CONFIGURACION ESCUELA
# ==============================

def obtener_config():

    config = configuracion.find_one()

    if config:

        escuela = config.get("escuela", "Nombre de la Escuela")
        ciclo = config.get("ciclo", "Ciclo Escolar")
        director = config.get("director", "Director")
        direccion = config.get("direccion", "")

    else:

        escuela = "Nombre de la Escuela"
        ciclo = "Ciclo Escolar"
        director = "Director"
        direccion = ""

    return escuela, ciclo, director, direccion


# ==============================
# GENERAR KARDEX
# ==============================

def generar_kardex(nombre):

    escuela, ciclo, director, direccion = obtener_config()

    carpeta = "pdf_generados"

    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

    ruta = f"{carpeta}/kardex_{nombre}.pdf"

    c = canvas.Canvas(ruta, pagesize=letter)

    # ENCABEZADO

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, escuela)

    c.setFont("Helvetica", 12)
    c.drawString(200, 730, f"Ciclo Escolar: {ciclo}")
    c.drawString(200, 710, direccion)

    # TITULO

    c.setFont("Helvetica-Bold", 14)
    c.drawString(250, 680, "KARDEX ACADÉMICO")

    # ALUMNO

    c.setFont("Helvetica", 12)
    c.drawString(80, 640, f"Alumno: {nombre}")

    # TABLA DE MATERIAS

    c.drawString(80, 600, "Materia")
    c.drawString(350, 600, "Calificación")

    lista_materias = list(materias.find())

    y = 570

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

    escuela, ciclo, director, direccion = obtener_config()

    carpeta = "pdf_generados"

    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

    ruta = f"{carpeta}/boleta_{nombre}.pdf"

    c = canvas.Canvas(ruta, pagesize=letter)

    # ENCABEZADO

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 750, escuela)

    c.setFont("Helvetica", 12)
    c.drawString(200, 730, f"Ciclo Escolar: {ciclo}")
    c.drawString(200, 710, direccion)

    # TITULO

    c.setFont("Helvetica-Bold", 14)
    c.drawString(250, 680, "BOLETA DE CALIFICACIONES")

    # ALUMNO

    c.setFont("Helvetica", 12)
    c.drawString(80, 640, f"Alumno: {nombre}")

    # TABLA

    c.drawString(80, 600, "Materia")
    c.drawString(350, 600, "Calificación")

    lista_materias = list(materias.find())

    y = 570

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