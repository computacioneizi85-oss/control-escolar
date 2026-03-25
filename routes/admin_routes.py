from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId
import base64

from database.mongo import alumnos, grupos, materias, maestros, reportes, configuracion, horarios, citatorios
from pdf.generador import generar_kardex, generar_boleta, generar_reporte_pdf, generar_citatorio_pdf

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def verificar_admin():
    return "rol" in session and session["rol"] == "admin"


# ================= DASHBOARD =================
@admin_bp.route("/")
def admin_dashboard():
    try:
        if not verificar_admin():
            return redirect(url_for("auth.login"))

        return render_template(
            "admin.html",
            alumnos=list(alumnos.find()),
            grupos=list(grupos.find()),
            maestros=list(maestros.find()),
            reportes=list(reportes.find())
        )

    except Exception as e:
        return f"<h1>ERROR DASHBOARD:</h1><pre>{str(e)}</pre>"


# ================= 🔥 CREAR MAESTRO (FIX) =================
@admin_bp.route("/crear_maestro", methods=["POST"])
def crear_maestro():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    nombre = request.form.get("nombre")
    usuario = request.form.get("usuario")
    password = request.form.get("password")

    if not nombre or not usuario or not password:
        return "Datos incompletos"

    maestros.insert_one({
        "nombre": nombre,
        "usuario": usuario,
        "password": password,
        "grupos": [],
        "materias": []
    })

    return redirect(url_for("admin.ver_maestros"))


# ================= 🔥 ASIGNAR GRUPO (FIX) =================
@admin_bp.route("/asignar_grupo_maestro", methods=["POST"])
def asignar_grupo_maestro():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestro_id = request.form.get("maestro")
    grupo = request.form.get("grupo")

    if not maestro_id or not grupo:
        return "Datos incompletos"

    maestro = maestros.find_one({"_id": ObjectId(maestro_id)})

    if not maestro:
        return "Maestro no encontrado"

    grupos_actuales = maestro.get("grupos", [])

    if grupo not in grupos_actuales:
        grupos_actuales.append(grupo)

    maestros.update_one(
        {"_id": ObjectId(maestro_id)},
        {"$set": {"grupos": grupos_actuales}}
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

    try:
        if not verificar_admin():
            return redirect(url_for("auth.login"))

        grupo = request.form.get("grupo")
        trimestre = str(request.form.get("trimestre"))

        for alumno in alumnos.find({"grupo": grupo}):

            nuevas = []

            for c in alumno.get("calificaciones", []):

                if str(c.get("trimestre")) == trimestre or c.get("trimestre") is None:
                    continue

                nuevas.append(c)

            alumnos.update_one(
                {"_id": alumno["_id"]},
                {"$set": {"calificaciones": nuevas, "enviado": False}}
            )

        return redirect(url_for("admin.ver_evaluaciones"))

    except Exception as e:
        return f"<h1>ERROR RESET:</h1><pre>{str(e)}</pre>"


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

    foto = request.files.get("foto")
    foto_base64 = ""

    if foto and foto.filename != "":
        foto_base64 = base64.b64encode(foto.read()).decode("utf-8")

    alumnos.insert_one({
        "nombre": request.form.get("nombre"),
        "grupo": request.form.get("grupo"),
        "foto": foto_base64,
        "calificaciones": [],
        "asistencias": [],
        "enviado": False
    })

    return redirect(url_for("admin.ver_alumnos"))


# ================= MENÚS =================
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


@admin_bp.route("/materias")
def ver_materias():
    if not verificar_admin():
        return redirect(url_for("auth.login"))
    return render_template("materias.html", materias=list(materias.find()))