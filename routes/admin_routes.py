# ================= IMPORTS =================
from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId
import os

from database.mongo import (
    alumnos, grupos, materias, maestros,
    reportes, configuracion, horarios,
    citatorios, avisos
)

from pdf.generador import (
    generar_kardex, generar_boleta,
    generar_citatorio_pdf
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def verificar_admin():
    return session.get("rol") == "admin"


# ================= DASHBOARD =================
@admin_bp.route("/")
def admin_dashboard():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "admin.html",
        alumnos=list(alumnos.find()),
        grupos=list(grupos.find()),
        maestros=list(maestros.find()),
        reportes=list(reportes.find()),
        citatorios=list(citatorios.find()),
        alumnos_riesgo=[],
        ultimos_reportes=[],
        total_asistencias=0,
        total_faltas=0
    )


# ================= ALUMNOS =================
@admin_bp.route("/alumnos")
def admin_alumnos():
    return render_template(
        "alumnos.html",
        alumnos=list(alumnos.find()),
        grupos=list(grupos.find())
    )


# ================= MAESTROS =================
@admin_bp.route("/maestros")
def admin_maestros():
    return render_template(
        "maestros.html",
        maestros=list(maestros.find())
    )


# ================= GRUPOS =================
@admin_bp.route("/grupos")
def admin_grupos():
    return render_template(
        "grupos.html",
        grupos=list(grupos.find())
    )


# ================= REPORTES =================
@admin_bp.route("/reportes")
def admin_reportes():
    return render_template(
        "reportes.html",
        reportes=list(reportes.find())
    )


# ================= AVISOS =================
@admin_bp.route("/avisos")
def admin_avisos():
    return render_template(
        "avisos.html",
        avisos=list(avisos.find())
    )


# ================= CONFIG =================
@admin_bp.route("/configuracion")
def admin_configuracion():
    return render_template("configuracion.html")


# ================= REGISTRO COMPLETO =================
@admin_bp.route("/registro_completo_alumno", methods=["POST"])
def registro_completo_alumno():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    foto = request.files.get("foto")
    ruta_foto = ""

    if foto and foto.filename:
        carpeta = "static/fotos"
        os.makedirs(carpeta, exist_ok=True)
        ruta_foto = f"{carpeta}/{foto.filename}"
        foto.save(ruta_foto)

    alumnos.insert_one({
        "nombre": request.form.get("nombre") or "",
        "curp": request.form.get("curp") or "",
        "sexo": request.form.get("sexo") or "",
        "fecha_nacimiento": request.form.get("fecha_nacimiento") or "",
        "telefono": request.form.get("telefono") or "",
        "direccion": request.form.get("direccion") or "",
        "escuela_procedencia": request.form.get("escuela") or "",
        "promedio": request.form.get("promedio") or "",
        "afecciones": request.form.get("afecciones") or "",
        "padre_nombre": request.form.get("padre_nombre") or "",
        "padre_telefono": request.form.get("padre_telefono") or "",
        "padre_correo": request.form.get("padre_correo") or "",
        "grupo": request.form.get("grupo") or "",
        "usuario": str(ObjectId()),
        "foto": ruta_foto,
        "calificaciones": [],
        "asistencias": []
    })

    return redirect("/admin")


# ================= MATERIAS =================
@admin_bp.route("/materias")
def admin_materias():
    return render_template(
        "materias.html",
        materias=list(materias.find()),
        grupos=list(grupos.find())
    )


@admin_bp.route("/crear_materia", methods=["POST"])
def crear_materia():
    materias.insert_one({
        "nombre": request.form.get("nombre"),
        "grupo": request.form.get("grupo")
    })
    return redirect("/admin/materias")


@admin_bp.route("/eliminar_materia/<id>")
def eliminar_materia(id):
    materias.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/materias")


# ================= HORARIOS =================
@admin_bp.route("/horarios")
def admin_horarios():
    return render_template(
        "horarios.html",
        horarios=list(horarios.find()),
        grupos=list(grupos.find()),
        materias=list(materias.find()),
        maestros=list(maestros.find())
    )


@admin_bp.route("/crear_horario", methods=["POST"])
def crear_horario():
    horarios.insert_one({
        "grupo": request.form.get("grupo"),
        "materia": request.form.get("materia"),
        "maestro": request.form.get("maestro"),
        "dia": request.form.get("dia"),
        "hora": request.form.get("hora")
    })
    return redirect("/admin/horarios")


@admin_bp.route("/eliminar_horario/<id>")
def eliminar_horario(id):
    horarios.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/horarios")


# ================= CITATORIOS =================
@admin_bp.route("/citatorios")
def admin_citatorios():
    return render_template(
        "citatorios.html",
        citatorios=list(citatorios.find()),
        alumnos=list(alumnos.find())
    )


@admin_bp.route("/crear_citatorio", methods=["POST"])
def crear_citatorio():
    citatorios.insert_one({
        "alumno": request.form.get("alumno"),
        "grupo": request.form.get("grupo"),
        "motivo": request.form.get("motivo"),
        "fecha_cita": request.form.get("fecha"),
        "hora": request.form.get("hora"),
        "estatus": "pendiente",
        "enterado": False
    })
    return redirect("/admin/citatorios")


@admin_bp.route("/confirmar_asistencia/<id>")
def confirmar_asistencia(id):
    citatorios.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estatus": "asistio", "enterado": True}}
    )
    return redirect("/admin/citatorios")


@admin_bp.route("/citatorio_pdf/<id>")
def citatorio_pdf(id):
    citatorio = citatorios.find_one({"_id": ObjectId(id)})
    pdf = generar_citatorio_pdf(citatorio)
    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name="citatorio.pdf")


# ================= KARDEX =================
@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):
    pdf = generar_kardex(nombre)
    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name="kardex.pdf")


# ================= BOLETA =================
@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):
    pdf = generar_boleta(nombre)
    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name="boleta.pdf")


# ================= EXPEDIENTE =================
@admin_bp.route("/expediente/<id>")
def expediente(id):
    alumno = alumnos.find_one({"_id": ObjectId(id)})
    return render_template("expediente.html", alumno=alumno)


@admin_bp.route("/expediente_pdf/<id>")
def expediente_pdf(id):
    alumno = alumnos.find_one({"_id": ObjectId(id)})
    pdf = generar_boleta(alumno["nombre"])
    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name="expediente.pdf")


# ================= TRIMESTRE =================
@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():
    return redirect("/admin")


@admin_bp.route("/reporte_pdf/<id>")
def reporte_pdf(id):
    reporte = reportes.find_one({"_id": ObjectId(id)})
    pdf = generar_citatorio_pdf(reporte)  # o tu función de reporte
    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name="reporte.pdf")

# ================= CREAR ALUMNO =================
@admin_bp.route("/crear_alumno", methods=["POST"])
def crear_alumno():
    alumnos.insert_one({
        "nombre": request.form.get("nombre"),
        "grupo": request.form.get("grupo"),
        "calificaciones": [],
        "asistencias": []
    })
    return redirect("/admin/alumnos")


# ================= ELIMINAR ALUMNO =================
@admin_bp.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    alumnos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/alumnos")


# ================= CREAR MAESTRO =================
@admin_bp.route("/crear_maestro", methods=["POST"])
def crear_maestro():
    maestros.insert_one({
        "nombre": request.form.get("nombre"),
        "usuario": request.form.get("usuario"),
        "password": request.form.get("password"),
        "grupos": [],
        "materias": []
    })
    return redirect("/admin/maestros")


# ================= ELIMINAR MAESTRO =================
@admin_bp.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):
    maestros.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/maestros")


# ================= CREAR GRUPO =================
@admin_bp.route("/crear_grupo", methods=["POST"])
def crear_grupo():
    grupos.insert_one({
        "nombre": request.form.get("nombre")
    })
    return redirect("/admin/grupos")


# ================= ELIMINAR GRUPO =================
@admin_bp.route("/eliminar_grupo/<id>")
def eliminar_grupo(id):
    grupos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/grupos")


# ================= CREAR AVISO =================
@admin_bp.route("/crear_aviso", methods=["POST"])
def crear_aviso():
    avisos.insert_one({
        "titulo": request.form.get("titulo"),
        "mensaje": request.form.get("mensaje"),
        "tipo": request.form.get("tipo")
    })
    return redirect("/admin/avisos")


# ================= EDITAR AVISO =================
@admin_bp.route("/editar_aviso/<id>", methods=["POST"])
def editar_aviso(id):
    avisos.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "titulo": request.form.get("titulo"),
            "mensaje": request.form.get("mensaje")
        }}
    )
    return redirect("/admin/avisos")


# ================= ELIMINAR AVISO =================
@admin_bp.route("/eliminar_aviso/<id>")
def eliminar_aviso(id):
    avisos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/avisos")