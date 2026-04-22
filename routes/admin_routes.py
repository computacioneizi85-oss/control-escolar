from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
import base64
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


# ================= HORARIOS =================
@admin_bp.route("/horarios")
def ver_horarios():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "horarios_admin.html",
        horarios=list(horarios.find()),
        maestros=list(maestros.find()),
        materias=list(materias.find()),
        grupos=list(grupos.find())
    )


@admin_bp.route("/crear_horario", methods=["POST"])
def crear_horario():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

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
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    horarios.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/horarios")


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

    nombre = request.form.get("nombre")
    if nombre:
        grupos.insert_one({"nombre": nombre})
    return redirect("/admin/grupos")


@admin_bp.route("/eliminar_grupo/<id>")
def eliminar_grupo(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    grupos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/grupos")


# ================= MATERIAS =================
@admin_bp.route("/materias")
def ver_materias():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("materias.html", materias=list(materias.find()))


@admin_bp.route("/crear_materia", methods=["POST"])
def crear_materia():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    nombre = request.form.get("nombre")
    if nombre:
        materias.insert_one({"nombre": nombre})
    return redirect("/admin/materias")


@admin_bp.route("/eliminar_materia/<id>")
def eliminar_materia(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    materias.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/materias")


# ================= REPORTES =================
@admin_bp.route("/reportes")
def ver_reportes():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("reportes.html", reportes=list(reportes.find()))


@admin_bp.route("/aprobar_reporte/<id>")
def aprobar_reporte(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        reporte = reportes.find_one({"_id": ObjectId(id)})

        if not reporte:
            return "Reporte no encontrado"

        reportes.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"estatus": "aprobado"}}
        )

        pdf = generar_reporte_pdf(reporte)
        pdf.seek(0)

        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="reporte.pdf"
        )

    except Exception as e:
        return f"ERROR REPORTE: {str(e)}"


# ================= CITATORIOS =================
@admin_bp.route("/citatorios")
def ver_citatorios():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template("citatorios.html", citatorios=list(citatorios.find()))


@admin_bp.route("/generar_citatorio/<id>")
def generar_citatorio(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        citatorio = citatorios.find_one({"_id": ObjectId(id)})

        if not citatorio:
            return "Citatorio no encontrado"

        pdf = generar_citatorio_pdf(citatorio)
        pdf.seek(0)

        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="citatorio.pdf"
        )

    except Exception as e:
        return f"ERROR CITATORIO: {str(e)}"


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
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumnos.update_one(
        {"_id": ObjectId(request.form.get("id"))},
        {"$set": {"grupo": request.form.get("grupo")}}
    )
    return redirect("/admin/alumnos")


@admin_bp.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumnos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin/alumnos")


@admin_bp.route("/subir_foto_alumno/<id>", methods=["POST"])
def subir_foto_alumno(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    foto = request.files.get("foto")

    if foto and foto.filename:
        alumnos.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"foto": base64.b64encode(foto.read()).decode()}}
        )

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


@admin_bp.route("/asignar_grupo_maestro", methods=["POST"])
def asignar_grupo_maestro():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro"))},
        {"$addToSet": {"grupos": request.form.get("grupo")}}
    )
    return redirect("/admin/maestros")


@admin_bp.route("/editar_grupos_maestro", methods=["POST"])
def editar_grupos_maestro():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$set": {"grupos": request.form.getlist("grupos")}}
    )
    return redirect("/admin/maestros")


@admin_bp.route("/asignar_materias", methods=["POST"])
def asignar_materias():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    lista_materias = request.form.getlist("materias")
    maestro_id = request.form.get("maestro_id")

    if lista_materias:
        for materia in lista_materias:
            maestros.update_one(
                {"_id": ObjectId(maestro_id)},
                {"$addToSet": {"materias": materia}}
            )

    return redirect("/admin/maestros")


@admin_bp.route("/editar_materias_maestro", methods=["POST"])
def editar_materias_maestro():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$set": {"materias": request.form.getlist("materias")}}
    )
    return redirect("/admin/maestros")


@admin_bp.route("/quitar_materia", methods=["POST"])
def quitar_materia():
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestros.update_one(
        {"_id": ObjectId(request.form.get("maestro_id"))},
        {"$pull": {"materias": request.form.get("materia")}}
    )
    return redirect("/admin/maestros")

@admin_bp.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        maestros.delete_one({"_id": ObjectId(id)})
    except Exception as e:
        return f"ERROR ELIMINAR MAESTRO: {str(e)}"

    return redirect("/admin/maestros")


# ================= PDFS =================
@admin_bp.route("/kardex/<nombre>")
def kardex(nombre):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        pdf = generar_kardex(nombre)
        pdf.seek(0)
        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"kardex_{nombre}.pdf"
        )
    except Exception as e:
        return f"ERROR KARDEX: {str(e)}"


@admin_bp.route("/boleta/<nombre>")
def boleta(nombre):
    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        pdf = generar_boleta(nombre)
        pdf.seek(0)
        return send_file(
            pdf,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"boleta_{nombre}.pdf"
        )
    except Exception as e:
        return f"ERROR BOLETA: {str(e)}"

# ================= IMPORTAR BASE DE DATOS =================
import json

@admin_bp.route("/importar_bd", methods=["POST"])
def importar_bd():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    archivo = request.files.get("archivo")

    if not archivo:
        return "No se subió archivo"

    try:
        data = json.load(archivo)

        # ================= ALUMNOS =================
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

        # ================= MAESTROS =================
        for m in data.get("maestros", []):
            if not maestros.find_one({"usuario": m.get("usuario")}):
                maestros.insert_one({
                    "nombre": m.get("nombre"),
                    "usuario": m.get("usuario"),
                    "password": m.get("password", "1234"),
                    "grupos": m.get("grupos", []),
                    "materias": m.get("materias", [])
                })

        # ================= GRUPOS =================
        for g in data.get("grupos", []):
            if not grupos.find_one({"nombre": g.get("nombre")}):
                grupos.insert_one({"nombre": g.get("nombre")})

        # ================= MATERIAS =================
        for mat in data.get("materias", []):
            if not materias.find_one({"nombre": mat.get("nombre")}):
                materias.insert_one({"nombre": mat.get("nombre")})

    except Exception as e:
        return f"ERROR IMPORTAR: {str(e)}"

    return redirect("/admin")

from flask import Blueprint, render_template, session, redirect
from database.mongo import alumnos, avisos

alumno_bp = Blueprint("alumno", __name__)


# ================= SEGURIDAD =================
def verificar_alumno():
    return session.get("rol") == "alumno"


# ================= PANEL ALUMNO =================
@alumno_bp.route("/panel_alumno")
def panel_alumno():

    if not verificar_alumno():
        return redirect("/")

    alumno = alumnos.find_one({"usuario": session.get("usuario")})

    if not alumno:
        return "Alumno no encontrado"

    return render_template(
        "panel_alumno.html",
        alumno=alumno
    )


# ================= AVISOS =================
@alumno_bp.route("/avisos_alumno")  # 🔥 ruta única
def ver_avisos_alumno():

    if not verificar_alumno():
        return redirect("/")

    alumno = alumnos.find_one({"usuario": session.get("usuario")})

    lista_avisos = list(avisos.find({
        "$or": [
            {"tipo": "alumno"},
            {"tipo": "grupo", "grupo": alumno.get("grupo")}
        ]
    }))

    return render_template(
        "avisos_alumno.html",
        avisos=lista_avisos
    )

@admin_bp.route("/registro_completo", methods=["POST"])
def registro_completo():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        alumno = {
            "nombre": request.form.get("nombre"),
            "curp": request.form.get("curp"),
            "sexo": request.form.get("sexo"),
            "fecha_nacimiento": request.form.get("fecha"),
            "telefono": request.form.get("telefono"),
            "escuela_procedencia": request.form.get("escuela"),
            "promedio_primaria": request.form.get("promedio_primaria"),
            "promedio_anterior": request.form.get("promedio_anterior"),
            "afecciones": request.form.get("afecciones"),
            "beca": request.form.get("beca"),
            "grupo": request.form.get("grupo"),
            "usuario": request.form.get("usuario"),
            "password": generate_password_hash(request.form.get("password")),
            "calificaciones": [],
            "asistencias": []
        }

        alumnos.insert_one(alumno)

        padre = {
            "nombre": request.form.get("padre_nombre"),
            "ocupacion": request.form.get("padre_ocupacion"),
            "curp": request.form.get("padre_curp"),
            "parentesco": request.form.get("padre_parentesco"),
            "estudios": request.form.get("padre_estudios"),
            "telefono": request.form.get("padre_telefono"),
            "direccion": request.form.get("padre_direccion"),
            "extra": request.form.get("extra_nombre"),
            "extra_parentesco": request.form.get("extra_parentesco"),
            "extra_telefono": request.form.get("extra_telefono"),
            "correo": request.form.get("correo"),
            "usuario": f"padre_{request.form.get('usuario')}",
            "password": generate_password_hash(request.form.get("password")),
            "alumno": request.form.get("nombre")
        }

        padres.insert_one(padre)

    except Exception as e:
        return f"ERROR REGISTRO COMPLETO: {str(e)}"

    return redirect("/admin")