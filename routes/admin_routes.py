from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId

from database.mongo import alumnos, grupos, materias, maestros, reportes, configuracion, horarios, citatorios
from pdf.generador import generar_kardex, generar_boleta, generar_reporte_pdf, generar_citatorio_pdf

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ================= VERIFICAR ADMIN =================
def verificar_admin():
    return "rol" in session and session["rol"] == "admin"


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
        reportes=list(reportes.find())
    )


# ================= CONFIGURACIÓN =================
@admin_bp.route("/configuracion")
def configuracion_admin():
    if not verificar_admin():
        return redirect(url_for("auth.login"))
    return render_template("configuracion.html")


# ================= CREAR MAESTRO =================
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


# ================= ASIGNAR GRUPO =================
@admin_bp.route("/asignar_grupo_maestro", methods=["POST"])
def asignar_grupo_maestro():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestro_id = request.form.get("maestro")
    grupo = request.form.get("grupo")

    maestro = maestros.find_one({"_id": ObjectId(maestro_id)})
    grupos_actuales = maestro.get("grupos", [])

    if grupo not in grupos_actuales:
        grupos_actuales.append(grupo)

    maestros.update_one(
        {"_id": ObjectId(maestro_id)},
        {"$set": {"grupos": grupos_actuales}}
    )

    return redirect(url_for("admin.ver_maestros"))


# ================= EDITAR GRUPOS =================
@admin_bp.route("/editar_grupos_maestro", methods=["POST"])
def editar_grupos_maestro():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestro_id = request.form.get("maestro_id")
    grupos_sel = request.form.getlist("grupos")

    maestros.update_one(
        {"_id": ObjectId(maestro_id)},
        {"$set": {"grupos": grupos_sel}}
    )

    return redirect(url_for("admin.ver_maestros"))


# ================= EDITAR MATERIAS =================
@admin_bp.route("/editar_materias_maestro", methods=["POST"])
def editar_materias_maestro():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestro_id = request.form.get("maestro_id")
    materias_sel = request.form.getlist("materias")

    maestros.update_one(
        {"_id": ObjectId(maestro_id)},
        {"$set": {"materias": materias_sel}}
    )

    return redirect(url_for("admin.ver_maestros"))


# ================= TRIMESTRE =================
@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    configuracion.update_one(
        {"tipo": "trimestre"},
        {"$set": {
            "trimestre": str(request.form.get("trimestre")),
            "estado": request.form.get("estado")
        }},
        upsert=True
    )

    alumnos.update_many({}, {"$set": {"enviado": False}})

    return redirect(url_for("admin.admin_dashboard"))


@admin_bp.route("/cerrar_trimestre")
def cerrar_trimestre():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    configuracion.update_one(
        {"tipo": "trimestre"},
        {"$set": {"estado": "false"}}
    )

    return redirect(url_for("admin.ver_evaluaciones"))


# ================= EVALUACIONES =================
@admin_bp.route("/evaluaciones")
def ver_evaluaciones():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    datos = []

    for a in alumnos.find():
        for c in a.get("calificaciones", []):
            datos.append({
                "alumno": a.get("nombre"),
                "grupo": a.get("grupo"),
                "materia": c.get("materia"),
                "calificacion": c.get("calificacion"),
                "trimestre": str(c.get("trimestre")),
                "enviado": a.get("enviado", False)
            })

    config = configuracion.find_one({"tipo": "trimestre"}) or {}

    return render_template("evaluaciones_admin.html", datos=datos, config=config)


# ================= RESET GRUPO =================
@admin_bp.route("/reset_grupo", methods=["POST"])
def reset_grupo():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    grupo = request.form.get("grupo")

    alumnos.update_many(
        {"grupo": grupo},
        {"$set": {"calificaciones": [], "enviado": False}}
    )

    return redirect(url_for("admin.ver_evaluaciones"))


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

    # 🔥 actualizar estado
    reportes.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estado": "aprobado"}}
    )

    pdf = generar_reporte_pdf(reporte)
    pdf.seek(0)

    return send_file(pdf, mimetype="application/pdf")


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
        "fecha": request.form.get("fecha"),
        "hora": request.form.get("hora"),
        "estado": "pendiente"
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
    pdf.seek(0)

    return send_file(pdf, mimetype="application/pdf")


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


# ================= GRUPOS =================
@admin_bp.route("/grupos")
def ver_grupos():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("grupos.html", grupos=list(grupos.find()))


# ================= MATERIAS =================
@admin_bp.route("/materias")
def ver_materias():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("materias.html", materias=list(materias.find()))


# ================= HORARIOS =================
@admin_bp.route("/horarios")
def ver_horarios():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("horarios.html", horarios=list(horarios.find()))


# ================= ASISTENCIAS =================
@admin_bp.route("/asistencias")
def ver_asistencias():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("asistencias_admin.html", alumnos=list(alumnos.find()))


# ================= PDFS =================
@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    pdf = generar_kardex(nombre)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf")


@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    pdf = generar_boleta(nombre)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf")