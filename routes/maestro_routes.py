from flask import Blueprint, render_template, request, redirect, session, url_for, send_file
from bson.objectid import ObjectId
from datetime import datetime
from io import BytesIO

from reportlab.pdfgen import canvas

from database.mongo import (
    alumnos,
    maestros,
    horarios,
    configuracion,
    citatorios,
    avisos,
    reportes,
    grupos
)

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

    maestro = maestros.find_one({
        "usuario": session.get("usuario")
    }) or {}

grupos = maestro.get("grupos", [])
materias_maestro = maestro.get("materias", [])

    # 🔥 SI NO TIENE MATERIAS
    # TOMARLAS DEL HORARIO
    if not materias_maestro:

        materias_maestro = list(
            set(
                h.get("materia", "")
                for h in horarios.find({
                    "grupo": {
                        "$in": grupos
                    }
                })
                if h.get("materia")
            )
        )

    materias_maestro = list(
        set(
            h.get("materia", "")
            for h in horarios.find({
                "grupo": {
                    "$in": grupos
                }
            })
            if h.get("materia")
        )
    )

    lista_alumnos = list(
        alumnos.find({
            "grupo": {
                "$in": grupos
            }
        })
    )

    nombre_maestro = maestro.get("nombre", "")
    usuario_maestro = maestro.get("usuario", "")

    lista_horarios = list(
        horarios.find({
            "$or": [
                {
                    "maestro": {
                        "$regex": f"^{nombre_maestro}$",
                        "$options": "i"
                    }
                },
                {
                    "maestro": {
                        "$regex": f"^{usuario_maestro}$",
                        "$options": "i"
                    }
                },
                {
                    "grupo": {
                        "$in": grupos
                    }
                }
            ]
        })
    )

    config = configuracion.find_one(
    sort=[("_id", -1)]
) or {
        "captura_evaluaciones": True,
        "trimestre_1": True,
        "trimestre_2": False,
        "trimestre_3": False
    }

    return render_template(
        "panel_maestro.html",
        alumnos=lista_alumnos,
        grupos=grupos,
        materias=materias_maestro,
        horarios=lista_horarios,
        config=config,
        fecha_actual=datetime.now().strftime("%d/%m/%Y")
    )


# ================= GUARDAR CALIFICACIONES =================
@maestro_bp.route("/guardar_calificaciones_ajax", methods=["POST"])
def guardar_calificaciones_ajax():

    if not verificar_maestro():
        return {"status": "error"}

    config = configuracion.find_one() or {}

    if not config.get("captura_evaluaciones", True):
        return {
            "status": "error",
            "msg": "Captura deshabilitada"
        }

    alumno = request.form.get("alumno")
    materia = request.form.get("materia")
    trimestre = request.form.get("trimestre")

    if not config.get(f"trimestre_{trimestre}", False):
        return {
            "status": "error",
            "msg": "Trimestre deshabilitado"
        }

    try:
        cal = float(request.form.get("cal1") or 0)
    except:
        cal = 0

    maestro_actual = maestros.find_one({
        "usuario": session.get("usuario")
    }) or {}

    nombre_maestro = maestro_actual.get("nombre", "")

    alumno_db = alumnos.find_one({
        "nombre": {
            "$regex": f"^{alumno}$",
            "$options": "i"
        }
    })

    if not alumno_db:
        return {
            "status": "error",
            "msg": "Alumno no encontrado"
        }

    grupo = alumno_db.get("grupo", "")

    alumnos.update_one(
        {"_id": alumno_db["_id"]},
        {
            "$pull": {
                "calificaciones": {
                    "materia": materia,
                    "trimestre": trimestre
                }
            }
        }
    )

    alumnos.update_one(
        {"_id": alumno_db["_id"]},
        {
            "$push": {
                "calificaciones": {
                    "materia": materia,
                    "calificacion": cal,
                    "trimestre": trimestre,
                    "grupo": grupo,
                    "maestro": nombre_maestro,
                    "fecha": datetime.now()
                }
            }
        }
    )

    return {"status": "ok"}


# ================= HORARIO =================
@maestro_bp.route("/horario")
def horario_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro_actual = maestros.find_one({
        "usuario": session.get("usuario")
    }) or {}

    nombre_maestro = maestro_actual.get("nombre", "")
    usuario_maestro = maestro_actual.get("usuario", "")
    grupos = maestro_actual.get("grupos", [])

    lista_horarios = list(
        horarios.find({
            "$or": [
                {
                    "maestro": {
                        "$regex": f"^{nombre_maestro}$",
                        "$options": "i"
                    }
                },
                {
                    "maestro": {
                        "$regex": f"^{usuario_maestro}$",
                        "$options": "i"
                    }
                },
                {
                    "grupo": {
                        "$in": grupos
                    }
                }
            ]
        })
    )

    return render_template(
        "horario_maestro.html",
        horarios=lista_horarios
    )


# ================= PDF HORARIO =================
@maestro_bp.route("/horario/pdf")
def horario_pdf():
    return redirect("/descargar_horario")


# ================= DESCARGAR HORARIO =================
@maestro_bp.route("/descargar_horario")
def descargar_horario():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro_actual = maestros.find_one({
        "usuario": session.get("usuario")
    }) or {}

    nombre_maestro = maestro_actual.get("nombre", "")
    usuario_maestro = maestro_actual.get("usuario", "")
    grupos = maestro_actual.get("grupos", [])

    lista_horarios = list(
        horarios.find({
            "$or": [
                {
                    "maestro": {
                        "$regex": f"^{nombre_maestro}$",
                        "$options": "i"
                    }
                },
                {
                    "maestro": {
                        "$regex": f"^{usuario_maestro}$",
                        "$options": "i"
                    }
                },
                {
                    "grupo": {
                        "$in": grupos
                    }
                }
            ]
        })
    )

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.setTitle("Horario Maestro")

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(180, 800, "HORARIO DEL MAESTRO")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 770, f"Maestro: {nombre_maestro}")

    y = 730

    for h in lista_horarios:

        texto = (
            f"{h.get('dia', '')} | "
            f"{h.get('hora', '')} | "
            f"{h.get('grupo', '')} | "
            f"{h.get('materia', '')}"
        )

        pdf.drawString(50, y, texto)

        y -= 25

        if y < 50:
            pdf.showPage()
            y = 750

    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="horario_maestro.pdf",
        mimetype="application/pdf"
    )


# ================= CITATORIOS =================
@maestro_bp.route("/citatorios")
def citatorios_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({
        "usuario": session.get("usuario")
    }) or {}

    grupos = maestro.get("grupos", [])

    lista_alumnos = list(
        alumnos.find({
            "grupo": {
                "$in": grupos
            }
        })
    )

    lista_citatorios = list(citatorios.find())

    return render_template(
        "citatorios_maestro.html",
        citatorios=lista_citatorios,
        alumnos=lista_alumnos
    )


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
        "enterado": False
    })

    return redirect("/citatorios")


# ================= PDF CITATORIO =================
@maestro_bp.route("/generar_citatorio/<id>")
def generar_citatorio(id):

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    citatorio = citatorios.find_one({
        "_id": ObjectId(id)
    })

    pdf = generar_citatorio_pdf(citatorio)

    pdf.seek(0)

    return send_file(
        pdf,
        as_attachment=True,
        download_name="citatorio.pdf"
    )


# ================= CONFIRMAR ASISTENCIA =================
@maestro_bp.route("/confirmar_asistencia/<id>")
def confirmar_asistencia_maestro(id):

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    citatorios.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "estatus": "asistio",
                "enterado": True
            }
        }
    )

    return redirect("/citatorios")


# ================= AVISOS =================
@maestro_bp.route("/avisos_maestro")
def avisos_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({
        "usuario": session.get("usuario")
    }) or {}

    return render_template(
        "avisos_maestro.html",
        grupos=maestro.get("grupos", [])
    )


# ================= CREAR AVISO =================
@maestro_bp.route("/crear_aviso_maestro", methods=["POST"])
def crear_aviso_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    avisos.insert_one({
        "grupo": request.form.get("grupo"),
        "mensaje": request.form.get("mensaje"),
        "autor": session.get("usuario"),
        "fecha": datetime.now()
    })

    return redirect("/avisos_maestro")


# ================= ASISTENCIAS =================
@maestro_bp.route("/asistencias")
def asistencias_maestro():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({
        "usuario": session.get("usuario")
    }) or {}

    grupos_maestro = maestro.get("grupos", [])

    lista_alumnos = list(
        alumnos.find({
            "grupo": {
                "$in": grupos_maestro
            }
        })
    )

    fecha = datetime.now().strftime("%d/%m/%Y")

    return render_template(
        "asistencias.html",
        alumnos=lista_alumnos,
        fecha=fecha
    )


# ================= GUARDAR ASISTENCIA =================
@maestro_bp.route("/guardar_asistencia", methods=["POST"])
def guardar_asistencia():

    if not verificar_maestro():
        return redirect(url_for("auth.login"))

    alumno_id = request.form.get("alumno")

    fecha = request.form.get("fecha")

    estado = request.form.get("estado")

    alumno = alumnos.find_one({
        "_id": ObjectId(alumno_id)
    })

    if not alumno:
        return redirect("/panel_maestro")

    alumnos.update_one(
        {
            "_id": ObjectId(alumno_id)
        },
        {
            "$pull": {
                "asistencias": {
                    "fecha": fecha
                }
            }
        }
    )

    alumnos.update_one(
        {
            "_id": ObjectId(alumno_id)
        },
        {
            "$push": {
                "asistencias": {
                    "fecha": fecha,
                    "estado": estado,
                    "maestro": session.get("usuario")
                }
            }
        }
    )

    return redirect("/asistencias")