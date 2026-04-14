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

    try:
        lista_alumnos = list(alumnos.find())
        lista_grupos = list(grupos.find())
        lista_maestros = list(maestros.find())
        lista_reportes = list(reportes.find())
        lista_citatorios = list(citatorios.find())

        alumnos_riesgo = [a for a in lista_alumnos if not a.get("calificaciones")]
        ultimos_reportes = lista_reportes[-5:] if lista_reportes else []

        total_asistencias = sum(
            len(a.get("asistencias", []))
            for a in lista_alumnos
            if isinstance(a.get("asistencias", []), list)
        )

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

    except Exception as e:
        return f"ERROR DASHBOARD: {str(e)}"


# ================= TRIMESTRE =================
@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    trimestre = request.form.get("trimestre")
    estado = request.form.get("estado")

    configuracion.update_one(
        {},
        {
            "$set": {
                f"trimestre_{trimestre}": True if estado == "true" else False
            }
        },
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
    password = request.form.get("password")

    if not usuario or not password:
        return "Faltan usuario o contraseña"

    password_hash = generate_password_hash(password)

    alumnos.insert_one({
        "nombre": request.form.get("nombre"),
        "grupo": request.form.get("grupo"),
        "usuario": usuario,
        "password": password_hash,
        "calificaciones": [],
        "asistencias": []
    })

    padres.insert_one({
        "nombre": f"Padre de {request.form.get('nombre')}",
        "usuario": f"padre_{usuario}",
        "password": generate_password_hash(password),
        "alumno": request.form.get("nombre")
    })

    return redirect(url_for("admin.ver_alumnos"))


@admin_bp.route("/editar_grupo", methods=["POST"])
def editar_grupo():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumnos.update_one(
        {"_id": ObjectId(request.form.get("id"))},
        {"$set": {"grupo": request.form.get("grupo")}}
    )

    return redirect(url_for("admin.ver_alumnos"))


@admin_bp.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumnos.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("admin.ver_alumnos"))


@admin_bp.route("/subir_foto_alumno/<id>", methods=["POST"])
def subir_foto_alumno(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    foto = request.files.get("foto")

    if foto:
        imagen_base64 = base64.b64encode(foto.read()).decode("utf-8")

        alumnos.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"foto": imagen_base64}}
        )

    return redirect(url_for("admin.ver_alumnos"))


# ================= MAESTROS =================
@admin_bp.route("/maestros")
def ver_maestros():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "maestros.html",
        maestros=list(maestros.find()),
        grupos=list(grupos.find()),
        materias=list(materias.find())
    )


@admin_bp.route("/crear_maestro", methods=["POST"])
def crear_maestro():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestros.insert_one({
        "nombre": request.form.get("nombre"),
        "usuario": request.form.get("usuario"),
        "password": request.form.get("password"),
        "grupos": [],
        "materias": []
    })

    return redirect(url_for("admin.ver_maestros"))


@admin_bp.route("/asignar_grupo_maestro", methods=["POST"])
def asignar_grupo_maestro():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro"))},
        {"$addToSet": {"grupos": request.form.get("grupo")}}
    )

    return redirect(url_for("admin.ver_maestros"))


@admin_bp.route("/editar_grupos_maestro", methods=["POST"])
def editar_grupos_maestro():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$set": {"grupos": request.form.getlist("grupos")}}
    )

    return redirect(url_for("admin.ver_maestros"))


@admin_bp.route("/editar_materias_maestro", methods=["POST"])
def editar_materias_maestro():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$set": {"materias": request.form.getlist("materias")}}
    )

    return redirect(url_for("admin.ver_maestros"))


@admin_bp.route("/asignar_materias", methods=["POST"])
def asignar_materias():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$addToSet": {"materias": {"$each": request.form.getlist("materias")}}}
    )

    return redirect(url_for("admin.ver_maestros"))


@admin_bp.route("/quitar_materia", methods=["POST"])
def quitar_materia():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$pull": {"materias": request.form.get("materia")}}
    )

    return redirect(url_for("admin.ver_maestros"))


# ================= GRUPOS =================
@admin_bp.route("/grupos")
def ver_grupos():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("grupos.html", grupos=list(grupos.find()))


@admin_bp.route("/crear_grupo", methods=["POST"])
def crear_grupo():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    grupos.insert_one({"nombre": request.form.get("nombre")})
    return redirect(url_for("admin.ver_grupos"))


@admin_bp.route("/eliminar_grupo/<id>")
def eliminar_grupo(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    grupos.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("admin.ver_grupos"))


# ================= MATERIAS =================
@admin_bp.route("/materias")
def ver_materias():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "materias.html",
        materias=list(materias.find()),
        grupos=list(grupos.find())
    )


@admin_bp.route("/crear_materia", methods=["POST"])
def crear_materia():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    materias.insert_one({
        "nombre": request.form.get("nombre"),
        "grupo": request.form.get("grupo")
    })

    return redirect(url_for("admin.ver_materias"))


@admin_bp.route("/eliminar_materia/<id>")
def eliminar_materia(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    materias.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("admin.ver_materias"))


# ================= REPORTES =================
@admin_bp.route("/reportes")
def ver_reportes():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("reportes_admin.html", reportes=list(reportes.find()))


@admin_bp.route("/aprobar_reporte/<string:id>")
def aprobar_reporte(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    reporte = reportes.find_one({"_id": ObjectId(id)})

    if not reporte:
        return "Reporte no encontrado"

    pdf = generar_reporte_pdf(reporte)

    reportes.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estatus": "aprobado"}}
    )

    return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name="reporte.pdf")


# ================= CITATORIOS =================
@admin_bp.route("/citatorios")
def ver_citatorios():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "citatorios.html",
        citatorios=list(citatorios.find()),
        alumnos=list(alumnos.find())
    )


@admin_bp.route("/crear_citatorio", methods=["POST"])
def crear_citatorio():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    citatorios.insert_one({
        "alumno": request.form.get("alumno"),
        "grupo": request.form.get("grupo"),
        "motivo": request.form.get("motivo"),
        "fecha_cita": request.form.get("fecha"),
        "hora": request.form.get("hora"),
        "estatus": "pendiente"
    })

    return redirect(url_for("admin.ver_citatorios"))


@admin_bp.route("/generar_citatorio/<string:id>")
def generar_citatorio(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    citatorio = citatorios.find_one({"_id": ObjectId(id)})

    if not citatorio:
        return "Citatorio no encontrado"

    pdf = generar_citatorio_pdf(citatorio)

    return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name="citatorio.pdf")


# ================= PDFS =================
@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    pdf = generar_kardex(nombre)

    return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name=f"kardex_{nombre}.pdf")


@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    pdf = generar_boleta(nombre)

    return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name=f"boleta_{nombre}.pdf")