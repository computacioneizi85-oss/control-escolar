from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

from database.mongo import (
    alumnos, grupos, materias, maestros,
    reportes, configuracion, horarios,
    citatorios, padres, avisos
)

from pdf.generador import (
    generar_kardex, generar_boleta,
    generar_reporte_pdf, generar_citatorio_pdf
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


# ================= REGISTRO COMPLETO =================
@admin_bp.route("/registro_completo_alumno", methods=["POST"])
def registro_completo_alumno():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
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

            # 🔥 SOLUCIÓN CLAVE (NO ROMPE NADA)
            "usuario": str(ObjectId()),

            "foto": ruta_foto,
            "calificaciones": [],
            "asistencias": []
        })

        return redirect("/admin")

    except Exception as e:
        return f"ERROR REGISTRO: {str(e)}"


# ================= EXPEDIENTE =================
@admin_bp.route("/expediente/<id>")
def expediente(id):
    alumno = alumnos.find_one({"_id": ObjectId(id)})
    return render_template("expediente.html", alumno=alumno)


# ================= EDITAR =================
@admin_bp.route("/editar_expediente/<id>")
def editar_expediente(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumno = alumnos.find_one({"_id": ObjectId(id)})
    return render_template("editar_expediente.html", alumno=alumno)


@admin_bp.route("/actualizar_expediente/<id>", methods=["POST"])
def actualizar_expediente(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        update_data = {
            "nombre": request.form.get("nombre"),
            "curp": request.form.get("curp"),
            "sexo": request.form.get("sexo"),
            "fecha_nacimiento": request.form.get("fecha_nacimiento"),
            "telefono": request.form.get("telefono"),
            "direccion": request.form.get("direccion"),
            "escuela_procedencia": request.form.get("escuela"),
            "promedio": request.form.get("promedio"),
            "afecciones": request.form.get("afecciones"),
            "padre_nombre": request.form.get("padre_nombre"),
            "padre_telefono": request.form.get("padre_telefono"),
            "padre_correo": request.form.get("padre_correo"),
            "grupo": request.form.get("grupo")
        }

        foto = request.files.get("foto")

        if foto and foto.filename:
            carpeta = "static/fotos"
            os.makedirs(carpeta, exist_ok=True)
            ruta_foto = f"{carpeta}/{foto.filename}"
            foto.save(ruta_foto)
            update_data["foto"] = ruta_foto

        alumnos.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )

        return redirect(f"/admin/expediente/{id}")

    except Exception as e:
        return f"ERROR ACTUALIZAR: {str(e)}"


# ================= PDF EXPEDIENTE =================
@admin_bp.route("/expediente_pdf/<id>")
def expediente_pdf(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from io import BytesIO

    alumno = alumnos.find_one({"_id": ObjectId(id)})

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    contenido = []
    contenido.append(Paragraph("EXPEDIENTE DEL ALUMNO", styles["Title"]))
    contenido.append(Spacer(1, 12))

    for campo in [
        "nombre","curp","sexo","fecha_nacimiento","telefono",
        "direccion","escuela_procedencia","promedio","afecciones",
        "padre_nombre","padre_telefono","padre_correo","grupo"
    ]:
        contenido.append(
            Paragraph(f"<b>{campo}:</b> {alumno.get(campo,'')}", styles["Normal"])
        )

    doc.build(contenido)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="expediente.pdf",
        mimetype="application/pdf"
    )


# ================= ACTIVAR TRIMESTRE =================
@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        trimestre = request.form.get("trimestre")
        estado = request.form.get("estado")

        configuracion.update_one(
            {},
            {"$set": {
                "trimestre_activo": trimestre,
                "evaluaciones_activas": estado == "true"
            }},
            upsert=True
        )

        return redirect("/admin")

    except Exception as e:
        return f"ERROR TRIMESTRE: {str(e)}"


# ================= KARDEX =================
@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    pdf = generar_kardex(nombre)

    return send_file(
        pdf,
        as_attachment=True,
        download_name=f"kardex_{nombre}.pdf",
        mimetype="application/pdf"
    )


# ================= BOLETA =================
@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    pdf = generar_boleta(nombre)

    return send_file(
        pdf,
        as_attachment=True,
        download_name=f"boleta_{nombre}.pdf",
        mimetype="application/pdf"
    )

# ================= MENÚS ADMIN (RESTAURAR) =================

@admin_bp.route("/alumnos")
def admin_alumnos():
    return render_template(
        "alumnos.html",
        alumnos=list(alumnos.find()),
        grupos=list(grupos.find())
    )


@admin_bp.route("/maestros")
def admin_maestros():
    return render_template(
        "maestros.html",
        maestros=list(maestros.find()),
        grupos=list(grupos.find()),
        materias=list(materias.find())
    )


@admin_bp.route("/grupos")
def admin_grupos():
    return render_template("grupos.html", grupos=list(grupos.find()))


@admin_bp.route("/materias")
def admin_materias():
    return render_template("materias.html", materias=list(materias.find()))


@admin_bp.route("/horarios")
def admin_horarios():
    return render_template(
        "horarios.html",
        horarios=list(horarios.find()),
        grupos=list(grupos.find()),
        materias=list(materias.find()),
        maestros=list(maestros.find())
    )


@admin_bp.route("/reportes")
def admin_reportes():
    return render_template("reportes.html", reportes=list(reportes.find()))


@admin_bp.route("/citatorios")
def admin_citatorios():
    return render_template("citatorios.html", citatorios=list(citatorios.find()))


@admin_bp.route("/avisos")
def admin_avisos():
    return render_template("avisos_admin.html", avisos=list(avisos.find()))


@admin_bp.route("/configuracion")
def admin_configuracion():
    return render_template(
    "configuracion.html",
    config=configuracion.find_one()
)

# ================= ALUMNOS CRUD =================
@admin_bp.route("/crear_alumno", methods=["POST"])
def crear_alumno():
    alumnos.insert_one({
        "nombre": request.form.get("nombre"),
        "grupo": request.form.get("grupo"),
        "usuario": request.form.get("usuario"),
        "password": generate_password_hash(request.form.get("password")),
        "foto": ""
    })
    return redirect("/admin/alumnos")


@admin_bp.route("/editar_grupo", methods=["POST"])
def editar_grupo():
    alumnos.update_one(
        {"_id": ObjectId(request.form.get("id"))},
        {"$set": {"grupo": request.form.get("grupo")}}
    )
    return redirect("/admin/alumnos")


@admin_bp.route("/subir_foto_alumno/<id>", methods=["POST"])
def subir_foto_alumno(id):
    foto = request.files.get("foto")
    if foto:
        ruta = f"static/fotos/{foto.filename}"
        os.makedirs("static/fotos", exist_ok=True)
        foto.save(ruta)

        alumnos.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"foto": ruta}}
        )

    return redirect("/admin/alumnos")


@admin_bp.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    alumnos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/alumnos")


# ================= MAESTROS =================
@admin_bp.route("/crear_maestro", methods=["POST"])
def crear_maestro():
    maestros.insert_one({
        "nombre": request.form.get("nombre"),
        "usuario": request.form.get("usuario"),
        "password": generate_password_hash(request.form.get("password")),
        "grupos": [],
        "materias": []
    })
    return redirect("/admin/maestros")


@admin_bp.route("/asignar_grupo_maestro", methods=["POST"])
def asignar_grupo_maestro():
    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro"))},
        {"$addToSet": {"grupos": request.form.get("grupo")}}
    )
    return redirect("/admin/maestros")


@admin_bp.route("/asignar_materias", methods=["POST"])
def asignar_materias():
    materias_lista = request.form.getlist("materias")
    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$set": {"materias": materias_lista}}
    )
    return redirect("/admin/maestros")


@admin_bp.route("/quitar_materia", methods=["POST"])
def quitar_materia():
    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$pull": {"materias": request.form.get("materia")}}
    )
    return redirect("/admin/maestros")


@admin_bp.route("/editar_grupos_maestro", methods=["POST"])
def editar_grupos_maestro():
    grupos_lista = request.form.getlist("grupos")
    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$set": {"grupos": grupos_lista}}
    )
    return redirect("/admin/maestros")


@admin_bp.route("/editar_materias_maestro", methods=["POST"])
def editar_materias_maestro():
    materias_lista = request.form.getlist("materias")
    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$set": {"materias": materias_lista}}
    )
    return redirect("/admin/maestros")


@admin_bp.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):
    maestros.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/maestros")


# ================= GRUPOS =================
@admin_bp.route("/crear_grupo", methods=["POST"])
def crear_grupo():
    grupos.insert_one({"nombre": request.form.get("nombre")})
    return redirect("/admin/grupos")


@admin_bp.route("/eliminar_grupo/<id>")
def eliminar_grupo(id):
    grupos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/grupos")


# ================= HORARIOS =================
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


# ================= REPORTES =================
@admin_bp.route("/generar_reporte/<id>")
def generar_reporte(id):
    reporte = reportes.find_one({"_id": ObjectId(id)})
    pdf = generar_reporte_pdf(reporte)
    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name="reporte.pdf")


# ================= AVISOS =================
@admin_bp.route("/crear_aviso", methods=["POST"])
def crear_aviso():
    avisos.insert_one({
        "mensaje": request.form.get("mensaje"),
        "tipo": request.form.get("tipo"),
        "grupo": request.form.get("grupo"),
        "fecha": datetime.now()
    })
    return redirect("/admin/avisos")


@admin_bp.route("/eliminar_aviso/<id>")
def eliminar_aviso(id):
    avisos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/avisos")


# ================= CONFIG =================
@admin_bp.route("/guardar_configuracion", methods=["POST"])
def guardar_configuracion():

    archivo = request.files.get("escudo")
    escudo_base64 = None

    if archivo:
        import base64
        escudo_base64 = base64.b64encode(archivo.read()).decode("utf-8")

    configuracion.update_one(
        {},
        {"$set": {
            "escuela": request.form.get("escuela"),
            "ciclo": request.form.get("ciclo"),
            "director": request.form.get("director"),
            "direccion": request.form.get("direccion"),
            "escudo": escudo_base64
        }},
        upsert=True
    )

    return redirect("/admin/configuracion")


# ================= IMPORTAR BD =================
@admin_bp.route("/importar_bd", methods=["POST"])
def importar_bd():
    return redirect("/admin")