from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
from datetime import datetime

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


# ================= ALUMNOS =================
@admin_bp.route("/alumnos")
def ver_alumnos():
    return render_template("alumnos.html",
        alumnos=list(alumnos.find()),
        grupos=list(grupos.find()),
        maestros=list(maestros.find())
    )


@admin_bp.route("/crear_alumno", methods=["POST"])
def crear_alumno():
    alumnos.insert_one({
        "nombre": request.form.get("nombre"),
        "grupo": request.form.get("grupo"),
        "usuario": request.form.get("usuario"),
        "password": generate_password_hash(request.form.get("password")),
        "calificaciones": [],
        "asistencias": []
    })
    return redirect("/admin/alumnos")


# 🔥 NUEVO REGISTRO COMPLETO
@admin_bp.route("/registro_completo_alumno", methods=["POST"])
def registro_completo_alumno():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumnos.insert_one({
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

        "grupo": request.form.get("grupo"),

        "calificaciones": [],
        "asistencias": []
    })

    return redirect("/admin")


@admin_bp.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    alumnos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/alumnos")


# ================= MAESTROS =================
@admin_bp.route("/maestros")
def ver_maestros():
    return render_template("maestros.html",
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


@admin_bp.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):
    maestros.delete_one({"_id": ObjectId(id)})
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
    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$set": {"materias": request.form.getlist("materias")}}
    )
    return redirect("/admin/maestros")


@admin_bp.route("/editar_grupos_maestro", methods=["POST"])
def editar_grupos_maestro():
    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$set": {"grupos": request.form.getlist("grupos")}}
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
    return render_template("materias.html",
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
def ver_horarios():
    return render_template("horarios_admin.html",
        horarios=list(horarios.find()),
        maestros=list(maestros.find()),
        materias=list(materias.find()),
        grupos=list(grupos.find())
    )


@admin_bp.route("/crear_horario", methods=["POST"])
def crear_horario():
    horarios.insert_one(request.form.to_dict())
    return redirect("/admin/horarios")


@admin_bp.route("/eliminar_horario/<id>")
def eliminar_horario(id):
    horarios.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/horarios")


# ================= REPORTES =================
@admin_bp.route("/reportes")
def ver_reportes():
    return render_template("reportes.html", reportes=list(reportes.find()))


@admin_bp.route("/generar_reporte/<id>")
def generar_reporte(id):
    reporte = reportes.find_one({"_id": ObjectId(id)})
    pdf = generar_reporte_pdf(reporte)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf", as_attachment=True, download_name="reporte.pdf")


# ================= CITATORIOS =================
@admin_bp.route("/citatorios")
def ver_citatorios():
    return render_template("citatorios.html",
        citatorios=list(citatorios.find()),
        alumnos=list(alumnos.find())
    )


@admin_bp.route("/crear_citatorio", methods=["POST"])
def crear_citatorio():
    citatorios.insert_one({
        **request.form.to_dict(),
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


@admin_bp.route("/generar_citatorio/<id>")
def generar_citatorio(id):
    citatorio = citatorios.find_one({"_id": ObjectId(id)})
    pdf = generar_citatorio_pdf(citatorio)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf", as_attachment=True, download_name="citatorio.pdf")


# ================= AVISOS =================
@admin_bp.route("/avisos")
def ver_avisos():
    return render_template("avisos_admin.html", avisos=list(avisos.find()))


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


# ================= PDFS =================
@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):
    pdf = generar_kardex(nombre)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf", as_attachment=True,
                     download_name=f"kardex_{nombre}.pdf")


@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):
    pdf = generar_boleta(nombre)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf", as_attachment=True,
                     download_name=f"boleta_{nombre}.pdf")


# ================= TRIMESTRE =================
@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():
    configuracion.update_one(
        {},
        {
            "$set": {
                "trimestre_activo": request.form.get("trimestre"),
                "trimestre_habilitado": request.form.get("estado") == "true"
            }
        },
        upsert=True
    )
    return redirect("/admin")


# ================= CONFIG =================
@admin_bp.route("/configuracion")
def ver_configuracion():
    config = configuracion.find_one() or {}
    return render_template("configuracion.html", config=config)


# ================= IMPORTAR BD =================
@admin_bp.route("/importar_bd", methods=["POST"])
def importar_bd():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    archivo = request.files.get("archivo")

    if not archivo:
        return "No se subió archivo"

    import json

    data = json.load(archivo)

    alumnos.delete_many({})
    maestros.delete_many({})
    grupos.delete_many({})
    materias.delete_many({})
    horarios.delete_many({})

    if "alumnos" in data:
        alumnos.insert_many(data["alumnos"])

    if "maestros" in data:
        maestros.insert_many(data["maestros"])

    if "grupos" in data:
        grupos.insert_many(data["grupos"])

    if "materias" in data:
        materias.insert_many(data["materias"])

    if "horarios" in data:
        horarios.insert_many(data["horarios"])

    return redirect("/admin")

@admin_bp.route("/expediente/<id>")
def expediente(id):

    alumno = alumnos.find_one({"_id": ObjectId(id)})

    return render_template("expediente.html", alumno=alumno)

@admin_bp.route("/filtrar_alumnos")
def filtrar_alumnos():

    grupo = request.args.get("grupo")
    nombre = request.args.get("nombre")

    query = {}

    if grupo:
        query["grupo"] = grupo

    if nombre:
        query["nombre"] = {"$regex": nombre, "$options": "i"}

    return render_template("alumnos.html",
        alumnos=list(alumnos.find(query))
    )

# ================= EDITAR EXPEDIENTE =================
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

    alumnos.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
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
        }
    )

    return redirect(f"/admin/expediente/{id}")