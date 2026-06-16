from reportlab.lib.pagesizes import (
    letter,
    landscape
)
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from bson.objectid import ObjectId


from io import BytesIO
import base64
import os
from datetime import datetime
import uuid
import qrcode

from database.mongo import (
    configuracion,
    alumnos,
    movimientos_pagos,
    pagos
)

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

    c = canvas.Canvas(
        buffer,
        pagesize=letter
    )

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

    # Fondo encabezado
    c.setFillColorRGB(0.12, 0.24, 0.45)
    c.rect(0, 735, 612, 60, fill=1)

    # Escudo
    dibujar_escudo(c, escudo)

    # Texto principal
    c.setFillColor(colors.white)

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(300, 775, escuela)

    c.setFont("Helvetica", 10)
    c.drawCentredString(
        300,
        758,
        f"Ciclo Escolar: {ciclo}"
    )

    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(300, 710, titulo)

    # Línea elegante
    c.setStrokeColor(colors.HexColor("#1f4e79"))
    c.setLineWidth(2)
    c.line(40, 700, 550, 700)

    # Folio y fecha
    c.setFillColor(colors.black)

    c.setFont("Helvetica", 9)

    c.drawString(
        45,
        685,
        f"Folio: {generar_folio()}"
    )

    c.drawRightString(
        550,
        685,
        f"Fecha: {fecha_actual()}"
    )


# ================= FIRMA =================
def firma(c, director):

    c.setStrokeColor(colors.HexColor("#2c3e50"))

    c.line(180, 120, 420, 120)

    c.setFont("Helvetica-Bold", 11)

    c.drawCentredString(
        300,
        100,
        director
    )

    c.setFont("Helvetica", 9)

    c.drawCentredString(
        300,
        85,
        "Dirección Escolar"
    )

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

    alumno = alumnos.find_one({
    "nombre": {"$regex": f"^{nombre}$", "$options": "i"}
}) or {}

    c.setFont("Helvetica", 11)
    c.drawString(50, 670, f"Alumno: {nombre}")
    c.drawString(50, 650, f"Grupo: {alumno.get('grupo','')}")

    dibujar_foto(c, alumno.get("foto"))

    c.line(50, 630, 550, 630)

    data = [["Materia", "Calificación"]]

    suma = 0
    total = 0

    calificaciones = alumno.get("calificaciones", [])

    if calificaciones:

        for cal in calificaciones:

            materia = cal.get("materia", "")

            try:
                valor = float(cal.get("calificacion", 0) or 0)

            except:
                valor = 0

            data.append([
                materia,
                str(valor)
            ])

            suma += valor
            total += 1

    else:

        data.append([
            "Sin registros",
            "-"
        ])

    tabla = Table(
        data,
        colWidths=[350, 120]
    )

    tabla.setStyle(TableStyle([

        (
            'BACKGROUND',
            (0,0),
            (-1,0),
            colors.HexColor("#1F4E79")
         ),

        ("TEXTCOLOR", (0,0), (-1,0),
            colors.white),

        ("FONTNAME", (0,0), (-1,0),
            "Helvetica-Bold"),

        ("FONTSIZE", (0,0), (-1,-1),
            10),

        ("GRID", (0,0), (-1,-1),
            1,
            colors.HexColor("#1F4E79")),

        ("ROWBACKGROUNDS", (0,1), (-1,-1),
            [colors.whitesmoke, colors.beige]),

        ("BOTTOMPADDING", (0,0), (-1,0),
            10),

    ]))

    tabla.wrapOn(c, 50, 400)

    tabla.drawOn(c, 50, 430)

    promedio = round(suma / total, 2) if total else 0

    c.setFillColor(colors.HexColor("#1f4e79"))

    c.setFont("Helvetica-Bold", 14)

    c.drawString(
        50,
        390,
        f"Promedio general: {promedio}"
    )

    firma(c, director)

    c.save()
    buffer.seek(0)
    return buffer


# ================= BOLETA =================
def generar_boleta(nombre):

    escuela, ciclo, director, direccion, escudo = obtener_config()
    c, buffer = crear_pdf()

    encabezado(c, escuela, ciclo, direccion, escudo, "BOLETA DE CALIFICACIONES")

    alumno = alumnos.find_one({
    "nombre": {"$regex": f"^{nombre}$", "$options": "i"}
}) or {}

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

            try:
                valor = float(cal.get("calificacion", 0) or 0)
            except:
                valor = 0

            c.drawString(50, y, materia)
            c.drawString(320, y, str(valor))

            suma += valor
            total += 1
            y -= 25
    else:
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

    c.setFillColor(colors.HexColor("#2c3e50"))

    c.roundRect(
        45,
        420,
        500,
        140,
        10,
        stroke=1,
        fill=0
    )

    # TEXTO DENTRO DEL RECUADRO
    y = 530

    c.setFont("Helvetica", 11)

    c.setFillColor(colors.HexColor("#2c3e50"))

    for linea in texto.split("\n"):

        c.drawString(
            65,
            y,
            linea[:80]
        )

        y -= 18

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

    c.drawString(
        50,
        660,
        f"Alumno: {citatorio.get('alumno','')}"
    )

    c.drawString(
        50,
        640,
        f"Grupo: {citatorio.get('grupo','')}"
    )

    c.drawString(
        50,
        620,
        f"Fecha del citatorio: {citatorio.get('fecha_cita') or citatorio.get('fecha') or ''}"
    )

    c.drawString(
        320,
        620,
        f"Hora: {citatorio.get('hora') or ''}"
    )

    c.drawString(
        50,
        590,
        "Se solicita su presencia por el siguiente motivo:"
    )

    texto = str(citatorio.get("motivo", ""))

    c.roundRect(
        45,
        420,
        500,
        140,
        10,
        stroke=1,
        fill=0
    )

    # TEXTO DENTRO DEL RECUADRO
    y = 530

    c.setFont("Helvetica", 11)

    c.setFillColor(colors.HexColor("#2c3e50"))

    for linea in texto.split("\n"):

        c.drawString(
            65,
            y,
            linea[:80]
        )

        y -= 18

    firma(c, director)

    c.save()

    buffer.seek(0)

    return buffer

# ================= EXPEDIENTE PDF =================
def generar_expediente_pdf(alumno):

    escuela, ciclo, director, direccion, escudo = obtener_config()

    c, buffer = crear_pdf()

    encabezado(
        c,
        escuela,
        ciclo,
        direccion,
        escudo,
        "EXPEDIENTE DEL ALUMNO"
    )

    c.setFont("Helvetica", 11)

    c.drawString(50, 660, f"Nombre: {alumno.get('nombre', '')}")
    c.drawString(50, 640, f"Grupo: {alumno.get('grupo', '')}")
    c.drawString(50, 620, f"CURP: {alumno.get('curp', '')}")
    c.drawString(50, 600, f"Teléfono: {alumno.get('telefono', '')}")
    c.drawString(50, 580, f"Tutor: {alumno.get('tutor', '')}")

    dibujar_foto(c, alumno.get("foto"))

    firma(c, director)

    c.save()

    buffer.seek(0)

    return buffer

# ================= AUDITORIA PDF =================
def generar_auditoria_pdf(registros):

    escuela, ciclo, director, direccion, escudo = obtener_config()

    c, buffer = crear_pdf()

    encabezado(
        c,
        escuela,
        ciclo,
        direccion,
        escudo,
        "AUDITORÍA DEL SISTEMA"
    )

    c.setFont("Helvetica", 9)

    y = 660

    for item in registros:

        texto = (
            f"{item.get('fecha','')} | "
            f"{item.get('usuario','')} | "
            f"{item.get('rol','')} | "
            f"{item.get('evento','')} | "
            f"{item.get('ip','')}"
        )

        c.drawString(40, y, texto[:110])

        y -= 18

        if y <= 120:
            c.showPage()
            y = 760

    firma(c, director)

    c.save()

    buffer.seek(0)

    return buffer


# ================= BITACORA PDF =================
def generar_bitacora_pdf(registros):

    escuela, ciclo, director, direccion, escudo = obtener_config()

    c, buffer = crear_pdf()

    encabezado(
        c,
        escuela,
        ciclo,
        direccion,
        escudo,
        "BITÁCORA DEL SISTEMA"
    )

    c.setFont("Helvetica", 9)

    y = 660

    for item in registros:

        texto = (
            f"{item.get('fecha','')} | "
            f"{item.get('usuario','')} | "
            f"{item.get('accion','')} | "
            f"{item.get('detalle','')}"
        )

        c.drawString(40, y, texto[:110])

        y -= 18

        if y <= 120:
            c.showPage()
            y = 760

    firma(c, director)

    c.save()

    buffer.seek(0)

    return buffer

# ================= RECIBO DE PAGO =================
def generar_recibo_pago_pdf(movimiento):

    escuela, ciclo, director, direccion, escudo = obtener_config()

    c, buffer = crear_pdf()

    encabezado(
        c,
        escuela,
        ciclo,
        direccion,
        escudo,
        "RECIBO OFICIAL DE PAGO"
    )

    pago = pagos.find_one({
        "_id": ObjectId(
            movimiento["pago_id"]
        )
    })

    c.setFont("Helvetica", 11)

    y = 650

    c.drawString(
        50,
        y,
        f"Folio: {movimiento.get('folio','')}"
    )

    y -= 30

    c.drawString(
        50,
        y,
        f"Alumno: {movimiento.get('alumno','')}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Grupo: {movimiento.get('grupo','')}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Concepto: {movimiento.get('concepto','Colegiatura')}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Mes cubierto: {movimiento.get('mes_cubierto','')}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Monto recibido: ${movimiento.get('monto',0)}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Método: {movimiento.get('metodo','')}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Fecha: {movimiento.get('fecha_pago','')}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Hora: {movimiento.get('hora_pago','')}"
    )

    y -= 25

    c.drawString(
        50,
        y,
        f"Capturado por: {movimiento.get('capturado_por','')}"
    )

    y -= 50

    datos_qr = (

    "https://control-escolar-i0yw.onrender.com/validar/"

    + str(

        movimiento.get(
            "folio",
            ""
        )

    )

)

    datos_qr = (

        "https://control-escolar-i0yw.onrender.com/validar/"

        + str(

            movimiento.get(
                "folio",
                ""
            )

        )

    )

    qr = qrcode.make(
        datos_qr
    )

    qr_buffer = BytesIO()

    qr.save(
        qr_buffer,
        format="PNG"
    )

    qr_buffer.seek(0)

    qr_img = ImageReader(
        qr_buffer
    )

    c.drawImage(
        qr_img,
        420,
        420,
        width=100,
        height=100
    )
    y -= 40

    c.setFont(
        "Helvetica-Bold",
        12
    )

    c.drawString(
        50,
        y,
        f"Saldo pendiente: ${pago.get('saldo_restante',0)}"
    )

    try:

        sello = ImageReader(
            "static/img/director.png"
        )

        c.drawImage(
            sello,
            380,
            140,
            width=120,
            height=120,
            mask="auto"
        )

    except:
        pass

    firma(
        c,
        director
    )

    c.save()

    buffer.seek(0)

    return buffer

# =========================
# CORTE DE CAJA PDF
# =========================
def generar_corte_caja_pdf(
    movimientos,
    fecha,
    total
):

    escuela, ciclo, director, direccion, escudo = obtener_config()

    c, buffer = crear_pdf()

    encabezado(
        c,
        escuela,
        ciclo,
        direccion,
        escudo,
        "CORTE DE CAJA"
    )

    c.setFont(
        "Helvetica",
        11
    )

    c.drawString(
        50,
        670,
        f"Fecha: {fecha}"
    )

    y = 630

    c.setFont(
        "Helvetica-Bold",
        10
    )

    c.drawString(50, y, "Alumno")
    c.drawString(250, y, "Monto")
    c.drawString(350, y, "Metodo")
    c.drawString(450, y, "Hora")

    y -= 20

    c.setFont(
        "Helvetica",
        10
    )

    for m in movimientos:

        if y < 120:

            c.showPage()

            y = 700

        c.drawString(
            50,
            y,
            str(m.get("alumno", ""))
        )

        c.drawString(
            250,
            y,
            f"${m.get('monto',0)}"
        )

        c.drawString(
            350,
            y,
            str(m.get("metodo", ""))
        )

        c.drawString(
            450,
            y,
            str(m.get("hora_pago", ""))
        )

        y -= 20

    y -= 20

    c.setFont(
        "Helvetica-Bold",
        12
    )

    c.drawString(
        50,
        y,
        f"TOTAL DEL DIA: ${total}"
    )

    firma(
        c,
        director
    )

    c.save()

    buffer.seek(0)

    return buffer

# =========================
# MOROSOS PDF
# =========================
def generar_morosos_pdf(lista):

    escuela, ciclo, director, direccion, escudo = obtener_config()

    c, buffer = crear_pdf()

    encabezado(
        c,
        escuela,
        ciclo,
        direccion,
        escudo,
        "REPORTE DE MOROSOS"
    )

    y = 680

    c.setFont(
        "Helvetica-Bold",
        10
    )

    c.drawString(50, y, "Alumno")
    c.drawString(220, y, "Grupo")
    c.drawString(320, y, "Adeudo")

    y -= 25

    c.setFont(
        "Helvetica",
        10
    )

    for p in lista:

        if y < 120:

            c.showPage()

            y = 700

        c.drawString(
            50,
            y,
            str(p.get("alumno", ""))
        )

        c.drawString(
            220,
            y,
            str(p.get("grupo", ""))
        )

        c.drawString(
            320,
            y,
            f"${p.get('saldo_restante',0)}"
        )

        y -= 20

    firma(
        c,
        director
    )

    c.save()

    buffer.seek(0)

    return buffer

# =========================
# ESTADO DE CUENTA PDF
# =========================
def generar_estado_cuenta_pdf(
    pago,
    mensualidades_db
):

    escuela, ciclo, director, direccion, escudo = obtener_config()

    c, buffer = crear_pdf()

    encabezado(

        c,
        escuela,
        ciclo,
        direccion,
        escudo,
        "ESTADO DE CUENTA"

    )

    c.setFont(
        "Helvetica",
        11
    )

    y = 660

    c.drawString(
        50,
        y,
        f"Alumno: {pago.get('alumno','')}"
    )

    y -= 20

    c.drawString(
        50,
        y,
        f"Grupo: {pago.get('grupo','')}"
    )

    y -= 20

    c.drawString(
        50,
        y,
        f"Tipo de cobro: {pago.get('tipo_cobro','global')}"
    )

    y -= 20

    c.drawString(
        50,
        y,
        f"Total contratado: ${pago.get('total_debe',0)}"
    )

    y -= 20

    c.drawString(
        50,
        y,
        f"Total pagado: ${pago.get('total_pagado',0)}"
    )

    y -= 20

    c.drawString(
        50,
        y,
        f"Saldo pendiente: ${pago.get('saldo_restante',0)}"
    )

    y -= 40

    c.setFont(
        "Helvetica-Bold",
        10
    )

    c.drawString(
        40,
        y,
        "Mes"
    )

    c.drawString(
        100,
        y,
        "Monto"
    )

    c.drawString(
        170,
        y,
        "Pagado"
    )

    c.drawString(
        250,
        y,
        "Recargo"
    )

    c.drawString(
        320,
        y,
        "Estado"
    )

    c.drawString(
        390,
        y,
        "Fecha"
    )

    c.drawString(
        470,
        y,
        "Hora"
    )

    c.drawString(
        530,
        y,
        "Método"
    )

    y -= 25

    c.setFont(
        "Helvetica",
        10
    )

    for m in mensualidades_db:

        if y < 120:

            c.showPage()

            y = 700

        estado = (

            "Pagado"

            if m.get(
                "pagado"
            )

            else "Pendiente"

        )

        fecha_pago = m.get(
            "fecha_pago"
        )

        fecha_texto = "-"

        hora_texto = m.get(
            "hora_pago",
            "-"
        )

        if fecha_pago:

            try:

                fecha_texto = fecha_pago.strftime(
                    "%d/%m/%Y"
                )

            except:

                fecha_texto = str(
                    fecha_pago
                )[:10]

        c.drawString(
            40,
            y,
            str(
                m.get(
                    "mes",
                    ""
                )
            )
        )

        c.drawString(
            100,
            y,
            f"${m.get('monto',0):,.2f}"
        )

        c.drawString(
            170,
            y,
            f"${m.get('monto_pagado',0):,.2f}"
        )

        c.drawString(
            250,
            y,
            f"${m.get('recargo',0):,.2f}"
        )

        c.drawString(
            320,
            y,
            estado
        )

        c.drawString(
            390,
            y,
            fecha_texto
        )

        c.drawString(
            470,
            y,
            str(
                hora_texto
            )
        )

        c.drawString(
            530,
            y,
            str(
                m.get(
                    "metodo_pago",
                    "-"
                )
            )
        )

        y -= 20

    total_recargos = sum(

        m.get(
            "recargo",
            0
        )

        for m in mensualidades_db

    )

    c.setFont(
        "Helvetica-Bold",
        11
    )

    c.drawString(

        50,
        y,

        f"Total Recargos: ${total_recargos}"

    )

    y -= 20

    c.drawString(

        50,
        y,

        f"Saldo Pendiente: ${pago.get('saldo_restante',0)}"

    )

    firma(
        c,
        director
    )

    c.save()

    buffer.seek(0)

    return buffer

from io import BytesIO
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet


def generar_deudores_grupo_pdf(grupos):

    buffer = BytesIO()

    from reportlab.lib.pagesizes import landscape, letter

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    elementos = []

    estilos = getSampleStyleSheet()

    elementos.append(
        Paragraph(
            "Reporte de Deudores por Grupo",
            estilos["Title"]
        )
    )

    elementos.append(
        Spacer(1, 20)
    )

    for grupo, datos in grupos.items():

        elementos.append(
            Paragraph(
                f"Grupo {grupo}",
                estilos["Heading2"]
            )
        )

        elementos.append(
            Paragraph(
                f"Total adeudado: ${datos['total']:,.2f}",
                estilos["Normal"]
            )
        )

        tabla = [

            [
                "Alumno",
                "Saldo",
                "Cantidad",
                "Meses Adeudados",
                "Recargos"
            ]

        ]

        for alumno in datos["alumnos"]:

            tabla.append(

                [

                    alumno.get(
                        "alumno",
                        ""
                    ),

                    f"${alumno.get('saldo_restante',0):,.2f}",

                    len(
                        alumno.get(
                            "meses_debe",
                            []
                        )
                    ),

                    "\n".join(
                        alumno.get(
                            "meses_debe",
                            []
                        )
                    ),

                    f"${alumno.get('recargos',0):,.2f}"

                ]

            )

        t = Table(

            tabla,

            repeatRows=1,

            colWidths=[
                90,
                70,
                50,
                230,
                70
            ]

        )

        t.setStyle(

            TableStyle([

                ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#1F4E79")),

                ('TEXTCOLOR',(0,0),(-1,0),colors.white),

                ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),

                ('FONTSIZE',(0,0),(-1,-1),9),

                ('GRID',(0,0),(-1,-1),1,colors.black),

                ('ROWBACKGROUNDS',(0,1),(-1,-1),
                 [colors.whitesmoke, colors.beige]),

                ('VALIGN',(0,0),(-1,-1),'MIDDLE')

            ])

        )

        elementos.append(t)
    doc.build(elementos)

    buffer.seek(0)

    return buffer

def generar_bitacora_pagos_pdf(registros):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=20,
        rightMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    elementos = []

    estilos = getSampleStyleSheet()

    elementos.append(
        Paragraph(
            "BITÁCORA FINANCIERA",
            estilos["Title"]
        )
    )

    elementos.append(
        Spacer(1, 20)
    )

    tabla = [
        [
            "Fecha",
            "Usuario",
            "Acción",
            "Alumno",
            "Folio",
            "Monto"
        ]
    ]

    for r in registros:

        fecha = ""

        if r.get("fecha"):
            try:
                fecha = r["fecha"].strftime("%d/%m/%Y %H:%M")
            except:
                fecha = str(r["fecha"])

        tabla.append(
            [
                fecha,
                str(r.get("usuario", "")),
                str(r.get("accion", "")),
                str(r.get("alumno", "")),
                str(r.get("folio", "")),
                f"${float(r.get('monto', 0)):,.2f}"
            ]
        )

    t = Table(
        tabla,
        repeatRows=1,
        colWidths=[
            80,   # Fecha
            110,  # Usuario
            150,  # Acción
            180,  # Alumno
            90,   # Folio
            80    # Monto
        ]
    )

    t.setStyle(

        TableStyle([

            (
                'BACKGROUND',
                (0, 0),
                (-1, 0),
                colors.HexColor("#1F4E79")
            ),

            (
                'TEXTCOLOR',
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                'FONTNAME',
                (0, 0),
                (-1, 0),
                'Helvetica-Bold'
            ),

            (
                'FONTSIZE',
                (0, 0),
                (-1, -1),
                9
            ),

            (
           (
                'ALIGN',
                (0,0),
                (0,-1),
                'CENTER'
            ),

            (
                'ALIGN',
                (4,0),
                (5,-1),
                'CENTER'
            ),

           (
               'ALIGN',
               (1,1),
               (3,-1),
               'LEFT'
            ),

            (
                'VALIGN',
                (0, 0),
                (-1, -1),
                'MIDDLE'
            ),

            (
                'GRID',
                (0, 0),
                (-1, -1),
                1,
                colors.black
            ),

            (
                'ROWBACKGROUNDS',
                (0, 1),
                (-1, -1),
                [
                    colors.whitesmoke,
                    colors.beige
                ]
            )

        ])

    )

    elementos.append(t)

    doc.build(elementos)

    buffer.seek(0)

    return buffer