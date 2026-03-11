from flask import Blueprint, render_template, request, redirect, session, send_file
from bson.objectid import ObjectId
import os
from werkzeug.utils import secure_filename

from database.mongo import alumnos, grupos, materias, maestros, reportes, configuracion
from pdf.generador import generar_kardex, generar_boleta
from database.mongo import alumnos, grupos, materias, maestros, reportes, configuracion, horarios
from pdf.generador import generar_citatorio_pdf

from database.mongo import citatorios


admin_bp = Blueprint("admin", __name__)


# =========================
# VERIFICAR ADMIN
# =========================

def verificar_admin():

    if "rol" not in session:
        return False

    if session["rol"] != "admin":
        return False

    return True


# =========================
# DASHBOARD
# =========================

@admin_bp.route("/admin")
def admin_dashboard():

    if not verificar_admin():
        return redirect("/")

    lista_alumnos = list(alumnos.find())
    lista_grupos = list(grupos.find())
    lista_maestros = list(maestros.find())
    lista_reportes = list(reportes.find())

    return render_template(
        "admin.html",
        alumnos=lista_alumnos,
        grupos=lista_grupos,
        maestros=lista_maestros,
        reportes=lista_reportes
    )


# =========================
# ALUMNOS
# =========================

@admin_bp.route("/alumnos")
def ver_alumnos():

    if not verificar_admin():
        return redirect("/")

    grupo = request.args.get("grupo")
    maestro = request.args.get("maestro")

    filtro = {}

    if grupo and grupo != "":
        filtro["grupo"] = grupo

    if maestro and maestro != "":
        maestro_doc = maestros.find_one({"nombre": maestro})

        if maestro_doc:
            grupos_maestro = maestro_doc.get("grupos", [])
            filtro["grupo"] = {"$in": grupos_maestro}

    lista_alumnos = list(alumnos.find(filtro))
    lista_grupos = list(grupos.find())
    lista_maestros = list(maestros.find())

    return render_template(
        "alumnos.html",
        alumnos=lista_alumnos,
        grupos=lista_grupos,
        maestros=lista_maestros
    )


@admin_bp.route("/crear_alumno", methods=["POST"])
def crear_alumno():

    if not verificar_admin():
        return redirect("/")

    nombre = request.form.get("nombre")
    grupo = request.form.get("grupo")

    alumnos.insert_one({
        "nombre": nombre,
        "grupo": grupo,
        "calificaciones": [],
        "asistencias": []
    })

    return redirect("/alumnos")


@admin_bp.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):

    if not verificar_admin():
        return redirect("/")

    alumnos.delete_one({"_id": ObjectId(id)})

    return redirect("/alumnos")


# =========================
# MAESTROS
# =========================

@admin_bp.route("/maestros")
def ver_maestros():

    if not verificar_admin():
        return redirect("/")

    lista_maestros = list(maestros.find())
    lista_grupos = list(grupos.find())

    return render_template(
        "maestros.html",
        maestros=lista_maestros,
        grupos=lista_grupos
    )


@admin_bp.route("/crear_maestro", methods=["POST"])
def crear_maestro():

    if not verificar_admin():
        return redirect("/")

    nombre = request.form.get("nombre")
    usuario = request.form.get("usuario")
    password = request.form.get("password")

    maestros.insert_one({
        "nombre": nombre,
        "usuario": usuario,
        "password": password,
        "grupos": [],
        "materias": []
    })

    return redirect("/maestros")


@admin_bp.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):

    if not verificar_admin():
        return redirect("/")

    maestros.delete_one({"_id": ObjectId(id)})

    return redirect("/maestros")


# =========================
# ASIGNAR GRUPO A MAESTRO
# =========================

@admin_bp.route("/asignar_grupo_maestro", methods=["POST"])
def asignar_grupo_maestro():

    if not verificar_admin():
        return redirect("/")

    maestro_id = request.form.get("maestro")
    grupo = request.form.get("grupo")

    maestros.update_one(
        {"_id": ObjectId(maestro_id)},
        {"$addToSet": {"grupos": grupo}}
    )

    return redirect("/maestros")


# =========================
# GRUPOS
# =========================

@admin_bp.route("/grupos")
def ver_grupos():

    if not verificar_admin():
        return redirect("/")

    lista_grupos = list(grupos.find())

    return render_template(
        "grupos.html",
        grupos=lista_grupos
    )


@admin_bp.route("/crear_grupo", methods=["POST"])
def crear_grupo():

    if not verificar_admin():
        return redirect("/")

    nombre = request.form.get("nombre")

    grupos.insert_one({
        "nombre": nombre
    })

    return redirect("/grupos")


@admin_bp.route("/eliminar_grupo/<id>")
def eliminar_grupo(id):

    if not verificar_admin():
        return redirect("/")

    grupos.delete_one({"_id": ObjectId(id)})

    return redirect("/grupos")


# =========================
# MATERIAS
# =========================

@admin_bp.route("/materias")
def ver_materias():

    if not verificar_admin():
        return redirect("/")

    lista_materias = list(materias.find())
    lista_grupos = list(grupos.find())

    return render_template(
        "materias.html",
        materias=lista_materias,
        grupos=lista_grupos
    )


@admin_bp.route("/crear_materia", methods=["POST"])
def crear_materia():

    if not verificar_admin():
        return redirect("/")

    nombre = request.form.get("nombre")
    grupo = request.form.get("grupo")

    materias.insert_one({
        "nombre": nombre,
        "grupo": grupo
    })

    return redirect("/materias")


@admin_bp.route("/eliminar_materia/<id>")
def eliminar_materia(id):

    if not verificar_admin():
        return redirect("/")

    materias.delete_one({"_id": ObjectId(id)})

    return redirect("/materias")


# =========================
# REPORTES DISCIPLINARIOS
# =========================

@admin_bp.route("/reportes")
def ver_reportes():

    if not verificar_admin():
        return redirect("/")

    lista_reportes = list(reportes.find())

    return render_template(
        "reportes_admin.html",
        reportes=lista_reportes
    )

@admin_bp.route("/aprobar_reporte/<id>")
def aprobar_reporte(id):

    if not verificar_admin():
        return redirect("/")

    reporte = reportes.find_one({"_id": ObjectId(id)})

    if not reporte:
        return redirect("/reportes")

    from pdf.generador import generar_reporte_pdf

    ruta_pdf = generar_reporte_pdf(reporte)

    reportes.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "estatus": "aprobado",
                "pdf": ruta_pdf
            }
        }
    )

    return redirect("/reportes")

# =========================
# CONFIGURACIÓN ESCOLAR
# =========================

@admin_bp.route("/configuracion")
def ver_configuracion():

    if not verificar_admin():
        return redirect("/")

    datos = configuracion.find_one()

    return render_template(
        "configuracion.html",
        config=datos
    )


@admin_bp.route("/guardar_configuracion", methods=["POST"])
def guardar_configuracion():

    if not verificar_admin():
        return redirect("/")

    escuela = request.form.get("escuela")
    ciclo = request.form.get("ciclo")
    director = request.form.get("director")
    direccion = request.form.get("direccion")

    archivo = request.files.get("escudo")

    escudo_path = None

    if archivo and archivo.filename != "":

        nombre_archivo = secure_filename(archivo.filename)

        carpeta = "static/uploads"

        if not os.path.exists(carpeta):
            os.makedirs(carpeta)

        ruta = os.path.join(carpeta, nombre_archivo)

        archivo.save(ruta)

        escudo_path = os.path.abspath(ruta)

    datos = {
        "escuela": escuela,
        "ciclo": ciclo,
        "director": director,
        "direccion": direccion
    }

    if escudo_path:
        datos["escudo"] = escudo_path

    configuracion.update_one({}, {"$set": datos}, upsert=True)

    return redirect("/configuracion")


# =========================
# GENERAR KARDEX
# =========================

@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):

    if not verificar_admin():
        return redirect("/")

    archivo = generar_kardex(nombre)

    return send_file(
        archivo,
        as_attachment=True
    )


# =========================
# GENERAR BOLETA
# =========================

@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):

    if not verificar_admin():
        return redirect("/")

    archivo = generar_boleta(nombre)

    return send_file(
        archivo,
        as_attachment=True
    )

# =========================
# HORARIOS ESCOLARES
# =========================

@admin_bp.route("/horarios")
def ver_horarios():

    if not verificar_admin():
        return redirect("/")

    lista_horarios = list(horarios.find())
    lista_grupos = list(grupos.find())
    lista_materias = list(materias.find())
    lista_maestros = list(maestros.find())

    return render_template(
        "horarios.html",
        horarios=lista_horarios,
        grupos=lista_grupos,
        materias=lista_materias,
        maestros=lista_maestros
    )

@admin_bp.route("/crear_horario", methods=["POST"])
def crear_horario():

    if not verificar_admin():
        return redirect("/")

    grupo = request.form.get("grupo")
    materia = request.form.get("materia")
    maestro = request.form.get("maestro")
    dia = request.form.get("dia")
    hora = request.form.get("hora")

    horarios.insert_one({
        "grupo": grupo,
        "materia": materia,
        "maestro": maestro,
        "dia": dia,
        "hora": hora
    })

    return redirect("/horarios")

@admin_bp.route("/eliminar_horario/<id>")
def eliminar_horario(id):

    if not verificar_admin():
        return redirect("/")

    horarios.delete_one({"_id": ObjectId(id)})

    return redirect("/horarios")

# =========================
# ACTIVAR TRIMESTRES
# =========================

@admin_bp.route("/activar_trimestre", methods=["POST"])
def activar_trimestre():

    if not verificar_admin():
        return redirect("/")

    trimestre = request.form.get("trimestre")
    estado = request.form.get("estado") == "true"

    campo = f"trimestre{trimestre}"

    configuracion.update_one(
        {},
        {"$set": {campo: estado}},
        upsert=True
    )

    return redirect("/admin")

@admin_bp.route("/asistencias_admin")
def asistencias_admin():

    if not verificar_admin():
        return redirect("/")

    lista_alumnos = list(alumnos.find())
    lista_maestros = list(maestros.find())
    lista_grupos = list(grupos.find())

    return render_template(
        "asistencias_admin.html",
        alumnos=lista_alumnos,
        maestros=lista_maestros,
        grupos=lista_grupos
    )

# =========================
# REPORTE DE ASISTENCIAS
# =========================

@admin_bp.route("/asistencias")
def ver_asistencias():

    if not verificar_admin():
        return redirect("/")

    grupo = request.args.get("grupo")
    alumno = request.args.get("alumno")

    filtro = {}

    if grupo and grupo != "":
        filtro["grupo"] = grupo

    if alumno and alumno != "":
        filtro["nombre"] = {"$regex": alumno, "$options": "i"}

    lista_alumnos = list(alumnos.find(filtro))
    lista_grupos = list(grupos.find())
    lista_maestros = list(maestros.find())

    return render_template(
        "asistencias_admin.html",
        alumnos=lista_alumnos,
        grupos=lista_grupos,
        maestros=lista_maestros
    )

# =========================
# CITATORIOS
# =========================

@admin_bp.route("/citatorios")
def ver_citatorios():

    if not verificar_admin():
        return redirect("/")

    lista_citatorios = list(citatorios.find())
    lista_alumnos = list(alumnos.find())

    return render_template(
        "citatorios.html",
        citatorios=lista_citatorios,
        alumnos=lista_alumnos
    )


@admin_bp.route("/crear_citatorio", methods=["POST"])
def crear_citatorio():

    if not verificar_admin():
        return redirect("/")

    alumno = request.form.get("alumno")
    grupo = request.form.get("grupo")
    motivo = request.form.get("motivo")
    fecha = request.form.get("fecha")
    hora = request.form.get("hora")

    citatorios.insert_one({

        "alumno": alumno,
        "grupo": grupo,
        "motivo": motivo,
        "fecha_cita": fecha,
        "hora": hora,
        "estado": "pendiente"

    })

    return redirect("/citatorios")

@admin_bp.route("/generar_citatorio/<id>")
def generar_citatorio(id):

    if not verificar_admin():
        return redirect("/")

    citatorio = citatorios.find_one({"_id": ObjectId(id)})

    if not citatorio:
        return redirect("/citatorios")

    ruta_pdf = generar_citatorio_pdf(citatorio)

    citatorios.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"pdf": ruta_pdf}}
    )

    return redirect("/citatorios")