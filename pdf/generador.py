from reportlab.pdfgen import canvas


def generar_kardex(nombre):

    archivo = f"{nombre}_kardex.pdf"

    c = canvas.Canvas(archivo)

    c.setFont("Helvetica", 16)
    c.drawString(100, 750, "KARDEX ACADÉMICO")

    c.setFont("Helvetica", 12)
    c.drawString(100, 700, f"Alumno: {nombre}")

    c.drawString(100, 650, "Historial académico del alumno")

    c.save()

    return archivo


def generar_boleta(nombre):

    archivo = f"{nombre}_boleta.pdf"

    c = canvas.Canvas(archivo)

    c.setFont("Helvetica", 16)
    c.drawString(100, 750, "BOLETA DE CALIFICACIONES")

    c.setFont("Helvetica", 12)
    c.drawString(100, 700, f"Alumno: {nombre}")

    c.drawString(100, 650, "Calificaciones del periodo")

    c.save()

    return archivo