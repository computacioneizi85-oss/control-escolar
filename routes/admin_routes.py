from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
import base64

from database.mongo import (
    alumnos, grupos, materias, maestros,
    reportes, configuracion, horarios,
    citatorios, padres
)

from pdf.generador import (
    generar_kardex, generar_boleta,
    generar_reporte_pdf, generar_citatorio_pdf
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ================= SEGURIDAD =================
def verificar_admin():
    return session.get("rol") == "admin"


def proteger():
    if not verificar_admin():
        return redirect(url_for("auth.login"))


# ================= DASHBOARD =================
@admin_bp.route("/")
def admin_dashboard():

    if proteger(): return proteger()

    lista_alumnos = list(alumnos.find())
    lista_grupos = list(grupos.find())
    lista_maestros = list(maestros.find())
    lista_reportes = list(reportes.find())
    lista_citatorios = list(citatorios.find())

    return render_template(
        "admin.html",
        alumnos=lista_alumnos,
        grupos=lista_grupos,
        maestros=lista_maestros,
        reportes=lista_reportes,
        citatorios=lista_citatorios,
        alumnos_riesgo=[a for a in lista_alumnos if not a.get("calificaciones")],
        ultimos_reportes=lista_reportes[-5:],
        total_asistencias=sum(len(a.get("asistencias", [])) for a in lista_alumnos),
        total_faltas=0
    )


# ================= CONFIGURACIÓN =================
@admin_bp.route("/configuracion")
def ver_configuracion():
    if proteger(): return proteger()

    config = configuracion.find_one() or {}
    return render_template("configuracion.html", config=config)


# ================= TRIMESTRE =================
@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():
    if proteger(): return proteger()

    configuracion.update_one(
        {},
        {"$set": {f"trimestre_{request.form.get('trimestre')}": request.form.get("estado") == "true"}},
        upsert=True
    )

    return redirect("/admin")


# ================= HORARIOS =================
@admin_bp.route("/horarios")
def ver_horarios():
    if proteger(): return proteger()

    return render_template(
        "horarios_admin.html",
        horarios=list(horarios.find()),
        maestros=list(maestros.find()),
        materias=list(materias.find()),
        grupos=list(grupos.find())
    )


@admin_bp.route("/crear_horario", methods=["POST"])
def crear_horario():
    if proteger(): return proteger()

    horarios.insert_one({
        "maestro": request.form.get("maestro"),
        "materia": request.form.get("materia"),
        "grupo": request.form.get("grupo"),
        "dia": request.form.get("dia"),
        "hora": request.form.get("hora")
    })

    return redirect("/admin/horarios")


@admin_bp.route("/eliminar_horario/<id>")
def eliminar_horario(id):
    if proteger(): return proteger()

    horarios.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/horarios")


# ================= ALUMNOS =================
@admin_bp.route("/alumnos")
def ver_alumnos():
    if proteger(): return proteger()

    return render_template(
        "alumnos.html",
        alumnos=list(alumnos.find()),
        grupos=list(grupos.find()),
        maestros=list(maestros.find())
    )


@admin_bp.route("/crear_alumno", methods=["POST"])
def crear_alumno():
    if proteger(): return proteger()

    try:
        password = request.form.get("password")
        if not password:
            return "Contraseña requerida"

        usuario = request.form.get("usuario")

        alumnos.insert_one({
            "nombre": request.form.get("nombre"),
            "grupo": request.form.get("grupo"),
            "usuario": usuario,
            "password": generate_password_hash(password),
            "calificaciones": [],
            "asistencias": []
        })

        padres.insert_one({
            "nombre": f"Padre de {request.form.get('nombre')}",
            "usuario": f"padre_{usuario}",
            "password": generate_password_hash(password),
            "alumno": request.form.get("nombre")
        })

    except Exception as e:
        return f"ERROR CREAR ALUMNO: {str(e)}"

    return redirect("/admin/alumnos")


@admin_bp.route("/editar_grupo", methods=["POST"])
def editar_grupo():
    alumnos.update_one(
        {"_id": ObjectId(request.form.get("id"))},
        {"$set": {"grupo": request.form.get("grupo")}}
    )
    return redirect("/admin/alumnos")


@admin_bp.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    alumnos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/alumnos")


@admin_bp.route("/subir_foto_alumno/<id>", methods=["POST"])
def subir_foto_alumno(id):

    foto = request.files.get("foto")

    if foto:
        alumnos.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"foto": base64.b64encode(foto.read()).decode()}}
        )

    return redirect("/admin/alumnos")


# ================= MAESTROS =================
@admin_bp.route("/maestros")
def ver_maestros():
    return render_template(
        "maestros.html",
        maestros=list(maestros.find()),
        grupos=list(grupos.find()),
        materias=list(materias.find())
    )


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


@admin_bp.route("/asignar_grupo_maestro", methods=["POST"])
def asignar_grupo_maestro():
    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro"))},
        {"$addToSet": {"grupos": request.form.get("grupo")}}
    )
    return redirect("/admin/maestros")


@admin_bp.route("/editar_grupos_maestro", methods=["POST"])
def editar_grupos_maestro():
    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$set": {"grupos": request.form.getlist("grupos")}}
    )
    return redirect("/admin/maestros")


@admin_bp.route("/asignar_materias", methods=["POST"])
def asignar_materias():
    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$addToSet": {"materias": {"$each": request.form.getlist("materias")}}}
    )
    return redirect("/admin/maestros")


@admin_bp.route("/editar_materias_maestro", methods=["POST"])
def editar_materias_maestro():
    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$set": {"materias": request.form.getlist("materias")}}
    )
    return redirect("/admin/maestros")


@admin_bp.route("/quitar_materia", methods=["POST"])
def quitar_materia():
    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$pull": {"materias": request.form.get("materia")}}
    )
    return redirect("/admin/maestros")


# ================= REPORTES =================
@admin_bp.route("/aprobar_reporte/<id>")
def aprobar_reporte(id):

    try:
        reporte = reportes.find_one({"_id": ObjectId(id)})
        pdf = generar_reporte_pdf(reporte)
        pdf.seek(0)

        reportes.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"estatus": "aprobado"}}
        )

        return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name="reporte.pdf")

    except Exception as e:
        return f"ERROR REPORTE: {str(e)}"


# ================= CITATORIOS =================
@admin_bp.route("/generar_citatorio/<id>")
def generar_citatorio(id):

    try:
        citatorio = citatorios.find_one({"_id": ObjectId(id)})
        pdf = generar_citatorio_pdf(citatorio)
        pdf.seek(0)

        return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name="citatorio.pdf")

    except Exception as e:
        return f"ERROR CITATORIO: {str(e)}"


# ================= PDFS =================
@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):

    try:
        pdf = generar_kardex(nombre)
        pdf.seek(0)
        return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name=f"kardex_{nombre}.pdf")

    except Exception as e:
        return f"ERROR KARDEX: {str(e)}"


@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):

    try:
        pdf = generar_boleta(nombre)
        pdf.seek(0)
        return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name=f"boleta_{nombre}.pdf")

    except Exception as e:
        return f"ERROR BOLETA: {str(e)}"