from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
import base64
from datetime import datetime
import json

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


# ================= SEGURIDAD =================
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


# ================= AVISOS =================
@admin_bp.route("/avisos")
def ver_avisos():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("avisos.html", avisos=list(avisos.find()))


@admin_bp.route("/crear_aviso", methods=["POST"])
def crear_aviso():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    avisos.insert_one({
        "tipo": request.form.get("tipo"),
        "titulo": request.form.get("titulo"),
        "mensaje": request.form.get("mensaje"),
        "fecha": datetime.now().strftime("%d/%m/%Y")
    })

    return redirect("/admin/avisos")


@admin_bp.route("/eliminar_aviso/<id>")
def eliminar_aviso(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    avisos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/avisos")


@admin_bp.route("/editar_aviso/<id>", methods=["POST"])
def editar_aviso(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    avisos.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "titulo": request.form.get("titulo"),
            "mensaje": request.form.get("mensaje")
        }}
    )
    return redirect("/admin/avisos")


# ================= CONFIGURACIÓN =================
@admin_bp.route("/configuracion")
def ver_configuracion():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    config = configuracion.find_one() or {}
    return render_template("configuracion.html", config=config)


@admin_bp.route("/guardar_configuracion", methods=["POST"])
def guardar_configuracion():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    datos = {
        "escuela": request.form.get("escuela"),
        "ciclo": request.form.get("ciclo"),
        "director": request.form.get("director"),
        "direccion": request.form.get("direccion")
    }

    escudo = request.files.get("escudo")
    if escudo and escudo.filename:
        datos["escudo"] = base64.b64encode(escudo.read()).decode()

    configuracion.update_one({}, {"$set": datos}, upsert=True)
    return redirect("/admin/configuracion")


# ================= TRIMESTRE =================
@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    configuracion.update_one(
        {},
        {"$set": {
            f"trimestre_{request.form.get('trimestre')}": request.form.get("estado") == "true"
        }},
        upsert=True
    )

    return redirect("/admin")


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

    password = request.form.get("password") or "1234"
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

    return redirect("/admin/alumnos")


@admin_bp.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumnos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/alumnos")


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

    return redirect("/admin/maestros")


@admin_bp.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestros.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/maestros")


# ================= PDFS =================
@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    pdf = generar_kardex(nombre)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf", as_attachment=True)


@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    pdf = generar_boleta(nombre)
    pdf.seek(0)
    return send_file(pdf, mimetype="application/pdf", as_attachment=True)


# ================= IMPORTAR BD =================
@admin_bp.route("/importar_bd", methods=["POST"])
def importar_bd():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    archivo = request.files.get("archivo")

    if not archivo:
        return "No se subió archivo"

    data = json.load(archivo)

    for a in data.get("alumnos", []):
        if not alumnos.find_one({"usuario": a.get("usuario")}):
            alumnos.insert_one({
                "nombre": a.get("nombre"),
                "grupo": a.get("grupo"),
                "usuario": a.get("usuario"),
                "password": generate_password_hash(a.get("password", "1234")),
                "calificaciones": [],
                "asistencias": []
            })

    return redirect("/admin")


# ================= REGISTRO COMPLETO =================
@admin_bp.route("/registro_completo", methods=["POST"])
def registro_completo():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        password = request.form.get("password") or "1234"
        usuario = request.form.get("usuario")

        if not usuario:
            return "Usuario requerido"

        if alumnos.find_one({"usuario": usuario}):
            return "Usuario ya existe"

        alumno = {
            "nombre": request.form.get("nombre") or "",
            "curp": request.form.get("curp") or "",
            "sexo": request.form.get("sexo") or "",
            "fecha_nacimiento": request.form.get("fecha") or "",
            "telefono": request.form.get("telefono") or "",
            "escuela_procedencia": request.form.get("escuela") or "",
            "promedio_primaria": request.form.get("promedio_primaria") or "",
            "promedio_anterior": request.form.get("promedio_anterior") or "",
            "afecciones": request.form.get("afecciones") or "",
            "beca": request.form.get("beca") or "",
            "grupo": request.form.get("grupo") or "",
            "usuario": usuario,
            "password": generate_password_hash(password),
            "calificaciones": [],
            "asistencias": []
        }

        alumnos.insert_one(alumno)

        padres.insert_one({
            "nombre": request.form.get("padre_nombre") or "",
            "usuario": f"padre_{usuario}",
            "password": generate_password_hash(password),
            "alumno": alumno["nombre"]
        })

    except Exception as e:
        return f"ERROR REGISTRO COMPLETO: {str(e)}"

    return redirect("/admin")