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


# ================= VERIFICAR ADMIN =================
def verificar_admin():
    return session.get("rol") == "admin"


# ================= DASHBOARD =================
@admin_bp.route("/")
def admin_dashboard():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    lista_alumnos = list(alumnos.find())
    lista_grupos = list(grupos.find())
    lista_maestros = list(maestros.find())
    lista_reportes = list(reportes.find())
    lista_citatorios = list(citatorios.find())

    alumnos_riesgo = [a for a in lista_alumnos if not a.get("calificaciones")]
    ultimos_reportes = lista_reportes[-5:]

    total_asistencias = sum(len(a.get("asistencias", [])) for a in lista_alumnos)
    total_faltas = 0

    return render_template(
        "admin.html",
        alumnos=lista_alumnos,
        grupos=lista_grupos,
        maestros=lista_maestros,
        reportes=lista_reportes,
        citatorios=lista_citatorios,
        alumnos_riesgo=alumnos_riesgo,
        ultimos_reportes=ultimos_reportes,
        total_asistencias=total_asistencias,
        total_faltas=total_faltas
    )


# ================= TRIMESTRE =================
@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    trimestre = request.form.get("trimestre")
    estado = request.form.get("estado")

    configuracion.update_one(
        {},
        {"$set": {f"trimestre_{trimestre}": estado == "true"}},
        upsert=True
    )

    return redirect(url_for("admin.admin_dashboard"))


# ================= ALUMNOS =================
@admin_bp.route("/alumnos")
def ver_alumnos():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "alumnos.html",
        alumnos=list(alumnos.find()),
        grupos=list(grupos.find()),
        maestros=list(maestros.find())
    )


@admin_bp.route("/crear_alumno", methods=["POST"])
def crear_alumno():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    usuario = request.form.get("usuario")
    password = generate_password_hash(request.form.get("password"))

    alumnos.insert_one({
        "nombre": request.form.get("nombre"),
        "grupo": request.form.get("grupo"),
        "usuario": usuario,
        "password": password,
        "calificaciones": [],
        "asistencias": []
    })

    padres.insert_one({
        "nombre": f"Padre de {request.form.get('nombre')}",
        "usuario": f"padre_{usuario}",
        "password": generate_password_hash(request.form.get("password")),
        "alumno": request.form.get("nombre")
    })

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


# ================= GRUPOS =================
@admin_bp.route("/grupos")
def ver_grupos():
    return render_template("grupos.html", grupos=list(grupos.find()))


@admin_bp.route("/crear_grupo", methods=["POST"])
def crear_grupo():
    grupos.insert_one({"nombre": request.form.get("nombre")})
    return redirect("/admin/grupos")


@admin_bp.route("/eliminar_grupo/<id>")
def eliminar_grupo(id):
    grupos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/grupos")


# ================= MATERIAS =================
@admin_bp.route("/materias")
def ver_materias():
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


# ================= REPORTES =================
@admin_bp.route("/reportes")
def ver_reportes():
    return render_template("reportes_admin.html", reportes=list(reportes.find()))


@admin_bp.route("/aprobar_reporte/<id>")
def aprobar_reporte(id):

    reporte = reportes.find_one({"_id": ObjectId(id)})

    if not reporte:
        return "No encontrado"

    pdf = generar_reporte_pdf(reporte)
    pdf.seek(0)

    reportes.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estatus": "aprobado"}}
    )

    return send_file(pdf, mimetype='application/pdf', as_attachment=True)


# ================= CITATORIOS =================
@admin_bp.route("/citatorios")
def ver_citatorios():
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


@admin_bp.route("/generar_citatorio/<id>")
def generar_citatorio(id):

    try:
        citatorio = citatorios.find_one({"_id": ObjectId(id)})
        pdf = generar_citatorio_pdf(citatorio)
        pdf.seek(0)

        return send_file(pdf, mimetype='application/pdf', as_attachment=True)

    except Exception as e:
        return f"ERROR PDF: {str(e)}"


@admin_bp.route("/confirmar_asistencia/<id>")
def confirmar_asistencia(id):
    citatorios.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estatus": "asistio"}}
    )
    return redirect("/admin/citatorios")


# ================= PDFS =================
@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):
    pdf = generar_kardex(nombre)
    pdf.seek(0)
    return send_file(pdf, mimetype='application/pdf', as_attachment=True)


@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):
    pdf = generar_boleta(nombre)
    pdf.seek(0)
    return send_file(pdf, mimetype='application/pdf', as_attachment=True)