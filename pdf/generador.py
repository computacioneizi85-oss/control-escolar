from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from io import BytesIO
import base64
import os
from datetime import datetime
import uuid

from database.mongo import configuracion, materias, alumnos


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
# UTILIDADES
# ==============================

def generar_folio():
    return str(uuid.uuid4())[:8].upper()

def fecha_actual():
    return datetime.now().strftime("%d/%m/%Y")


# ==============================
# ESCUDO
# ==============================

def dibujar_escudo(c, escudo):

    if not escudo:
        return

    try:
        if len(escudo) > 100:
            imagen_bytes = base64.b64decode(escudo)
            imagen_stream = BytesIO(imagen_bytes)
            logo = ImageReader(imagen_stream)
        elif os.path.exists(escudo):
            logo = ImageReader(escudo)
        else:
            return

        c.drawImage(logo, 40, 730, width=60, height=60)

    except:
        pass


# ==============================
# ENCABEZADO
# ==============================

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


# ==============================
# FIRMA
# ==============================

def firma(c, director):

    c.line(200, 140, 400, 140)
    c.drawCentredString(300, 120, director)
    c.drawCentredString(300, 105, "Director")


# ==============================
# CREAR PDF
# ==============================

def crear_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    return c, buffer


# ==============================
# 🔥 KARDEX PRO (MEJORADO)
# ==============================

def generar_kardex(nombre):

    escuela, ciclo, director, direccion, escudo = obtener_config()
    c, buffer = crear_pdf()

    encabezado(c, escuela, ciclo, direccion, escudo, "KARDEX ACADÉMICO")

    alumno = alumnos.find_one({"nombre": nombre})

    c.setFont("Helvetica", 11)
    c.drawString(50, 670, f"Alumno: {nombre}")
    c.drawString(50, 650, f"Grupo: {alumno.get('grupo','')}")

    # FOTO DEL ALUMNO
    try:
        if alumno.get("foto"):
            foto_bytes = base64.b64decode(alumno["foto"])
            foto_stream = BytesIO(foto_bytes)
            img = ImageReader(foto_stream)

            c.drawImage(img, 450, 630, width=80, height=80)
    except:
        pass

    c.line(50, 630, 550, 630)

    c.drawString(50, 610, "Materia")
    c.drawString(300, 610, "Calificación")

    y = 590
    suma = 0
    total = 0

    for cal in alumno.get("calificaciones", []):
        materia = cal.get("materia", "")
        valor = cal.get("calificacion", 0)

        c.drawString(50, y, materia)
        c.drawString(320, y, str(valor))

        suma += valor
        total += 1

        y -= 25

    # PROMEDIO
    promedio = round(suma / total, 2) if total > 0 else 0

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 20, f"Promedio general: {promedio}")

    firma(c, director)

    c.save()
    buffer.seek(0)

    return buffer


# ==============================
# BOLETA
# ==============================

def generar_boleta(nombre):

    escuela, ciclo, director, direccion, escudo = obtener_config()
    c, buffer = crear_pdf()

    encabezado(c, escuela, ciclo, direccion, escudo, "BOLETA DE CALIFICACIONES")

    alumno = alumnos.find_one({"nombre": nombre})

    c.setFont("Helvetica", 11)
    c.drawString(50, 670, f"Alumno: {nombre}")
    c.drawString(50, 650, f"Grupo: {alumno.get('grupo','')}")

    # FOTO
    try:
        if alumno.get("foto"):
            foto_bytes = base64.b64decode(alumno["foto"])
            foto_stream = BytesIO(foto_bytes)
            img = ImageReader(foto_stream)

            c.drawImage(img, 450, 630, width=80, height=80)
    except:
        pass

    c.line(50, 630, 550, 630)

    c.drawString(50, 610, "Materia")
    c.drawString(300, 610, "Calificación")

    y = 590
    suma = 0
    total = 0

    calificaciones = alumno.get("calificaciones", [])

    if calificaciones:
        for cal in calificaciones:
            materia = cal.get("materia", "")
            valor = cal.get("calificacion", 0)

            c.drawString(50, y, materia)
            c.drawString(320, y, str(valor))

            suma += valor
            total += 1

            y -= 25
    else:
        c.drawString(50, y, "Sin calificaciones registradas")

    promedio = round(suma / total, 2) if total > 0 else 0

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 20, f"Promedio: {promedio}")

    firma(c, director)

    c.save()
    buffer.seek(0)

    return buffer


# ==============================
# REPORTE
# ==============================

def generar_reporte_pdf(reporte):

    escuela, ciclo, director, direccion, escudo = obtener_config()
    c, buffer = crear_pdf()

    encabezado(c, escuela, ciclo, direccion, escudo, "REPORTE DISCIPLINARIO")

    c.setFont("Helvetica", 11)

    c.drawString(50, 660, f"Alumno: {reporte.get('alumno','')}")
    c.drawString(50, 640, f"Maestro: {reporte.get('maestro','')}")

    c.drawString(50, 610, "Comentario:")
    c.drawString(50, 590, reporte.get("comentario",""))

    c.drawString(50, 550, "Estado: Autorizado")

    firma(c, director)

    c.save()
    buffer.seek(0)

    return buffer


# ==============================
# CITATORIO
# ==============================

def generar_citatorio_pdf(citatorio):

    escuela, ciclo, director, direccion, escudo = obtener_config()
    c, buffer = crear_pdf()

    encabezado(c, escuela, ciclo, direccion, escudo, "CITATORIO A PADRES DE FAMILIA")

    c.setFont("Helvetica", 11)

    c.drawString(50, 660, f"Alumno: {citatorio.get('alumno','')}")
    c.drawString(50, 640, f"Grupo: {citatorio.get('grupo','')}")

    c.drawString(50, 610, "Motivo:")
    c.drawString(50, 590, citatorio.get("motivo",""))

    c.drawString(50, 550, f"Fecha: {citatorio.get('fecha_cita','')}")
    c.drawString(50, 530, f"Hora: {citatorio.get('hora','')}")

    c.drawString(50, 500, "Se solicita la presencia del padre, madre o tutor.")

    firma(c, director)

    c.save()
    buffer.seek(0)

    return buffer