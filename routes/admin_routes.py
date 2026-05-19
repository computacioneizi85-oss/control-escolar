# ================= IMPORTS =================
from flask import Blueprint, render_template, request, redirect, session, send_file, url_for
from bson.objectid import ObjectId
import os
from datetime import datetime

from database.mongo import (
    alumnos,
    grupos,
    materias,
    maestros,
    reportes,
    configuracion,
    horarios,
    citatorios,
    avisos,
    usuarios,
    admins_secundarios,
    bitacora,
    auditoria
)

from pdf.generador import (
    generar_kardex,
    generar_boleta,
    generar_citatorio_pdf
)

from pdf.generador import (
    generar_auditoria_pdf,
    generar_bitacora_pdf
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ================= VERIFICAR ADMIN =================
def verificar_admin():
    return session.get("rol") in ["admin", "superadmin"]


# ================= DASHBOARD =================
@admin_bp.route("/")
def admin_dashboard():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    config = configuracion.find_one()

    if not config:
        config = {
            "trimestre_1": True,
            "trimestre_2": False,
            "trimestre_3": False,
            "captura_evaluaciones": True
        }

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
        total_faltas=0,
        config=config
    )


# ================= ALUMNOS =================
@admin_bp.route("/alumnos")
def admin_alumnos():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "alumnos.html",
        alumnos=list(alumnos.find()),
        grupos=list(grupos.find())
    )


@admin_bp.route("/crear_alumno", methods=["POST"])
def crear_alumno():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    foto = request.files.get("foto")

    foto_base64 = ""

    if foto and foto.filename:

        import base64

        foto_base64 = base64.b64encode(
            foto.read()
        ).decode("utf-8")

    usuario = request.form.get("usuario")
    password = request.form.get("password")

    existe = alumnos.find_one({
        "usuario": usuario
    })

    if existe:
        return "⚠️ Ya existe un alumno con ese usuario"

    alumnos.insert_one({
        "nombre": request.form.get("nombre"),
        "grupo": request.form.get("grupo"),
        "usuario": usuario,
        "password": password,
        "foto": foto_base64,
        "rol": "alumno",
        "calificaciones": [],
        "asistencias": []
    })

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Creó alumno",
        "detalle": request.form.get("nombre"),
        "fecha": datetime.now()
    })

    return redirect("/admin/alumnos")


# ================= REGISTRO COMPLETO ALUMNO =================
@admin_bp.route("/registro_completo_alumno", methods=["POST"])
def registro_completo_alumno():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    foto = request.files.get("foto")
    ruta_foto = ""

    if foto and foto.filename:
        carpeta = "static/fotos"
        os.makedirs(carpeta, exist_ok=True)

        ruta_foto = f"{carpeta}/{foto.filename}"

        foto.save(ruta_foto)

    curp = request.form.get("curp")
    nombre = request.form.get("nombre")

    usuario = curp if curp else nombre.replace(" ", "").lower()
    password = curp[-4:] if curp else "1234"

    alumnos.insert_one({
        "nombre": nombre,
        "curp": curp,
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
        "usuario": usuario,
        "password": password,
        "rol": "alumno",
        "foto": ruta_foto,
        "calificaciones": [],
        "asistencias": []
    })

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Registro completo alumno",
        "detalle": nombre,
        "fecha": datetime.now()
    })

    return redirect("/admin")


@admin_bp.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumno = alumnos.find_one({"_id": ObjectId(id)})

    alumnos.delete_one({"_id": ObjectId(id)})

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Eliminó alumno",
        "detalle": alumno.get("nombre", ""),
        "fecha": datetime.now()
    })

    return redirect("/admin/alumnos")


# ================= MAESTROS =================
@admin_bp.route("/maestros")
def admin_maestros():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "maestros.html",
        maestros=list(maestros.find())
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

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Creó maestro",
        "detalle": request.form.get("nombre"),
        "fecha": datetime.now()
    })

    return redirect("/admin/maestros")


@admin_bp.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    maestro = maestros.find_one({"_id": ObjectId(id)})

    maestros.delete_one({"_id": ObjectId(id)})

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Eliminó maestro",
        "detalle": maestro.get("nombre", ""),
        "fecha": datetime.now()
    })

    return redirect("/admin/maestros")


# ================= GRUPOS =================
@admin_bp.route("/grupos")
def admin_grupos():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "grupos.html",
        grupos=list(grupos.find())
    )


@admin_bp.route("/crear_grupo", methods=["POST"])
def crear_grupo():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    grupos.insert_one({
        "nombre": request.form.get("nombre")
    })

    return redirect("/admin/grupos")


@admin_bp.route("/eliminar_grupo/<id>")
def eliminar_grupo(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    grupos.delete_one({"_id": ObjectId(id)})

    return redirect("/admin/grupos")


# ================= MATERIAS =================
@admin_bp.route("/materias")
def admin_materias():

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

    return redirect("/admin/materias")


@admin_bp.route("/eliminar_materia/<id>")
def eliminar_materia(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    materias.delete_one({"_id": ObjectId(id)})

    return redirect("/admin/materias")


# ================= HORARIOS =================
@admin_bp.route("/horarios")
def admin_horarios():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "horarios.html",
        horarios=list(horarios.find()),
        grupos=list(grupos.find()),
        materias=list(materias.find()),
        maestros=list(maestros.find())
    )


@admin_bp.route("/crear_horario", methods=["POST"])
def crear_horario():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

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

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    horarios.delete_one({"_id": ObjectId(id)})

    return redirect("/admin/horarios")


# ================= EVALUACIONES =================
@admin_bp.route("/evaluaciones")
def admin_evaluaciones():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    datos = []

    for alumno in alumnos.find():

        nombre_alumno = alumno.get("nombre", "")
        grupo_alumno = alumno.get("grupo", "")

        for cal in alumno.get("calificaciones", []):

            datos.append({
                "alumno": nombre_alumno,
                "grupo": cal.get("grupo", grupo_alumno),
                "materia": cal.get("materia", ""),
                "maestro": cal.get("maestro", ""),
                "calificacion": cal.get("calificacion", 0),
                "trimestre": cal.get("trimestre", ""),
                "enviado": True
            })

    config = configuracion.find_one() or {
        "trimestre_activo": "1",
        "trimestre_1": True,
        "trimestre_2": False,
        "trimestre_3": False,
        "captura_evaluaciones": True
    }

    return render_template(
        "evaluaciones_admin.html",
        datos=datos,
        config=config,
        maestros=list(maestros.find())
    )


# ================= CONFIGURACIÓN =================
@admin_bp.route("/configuracion")
def admin_configuracion():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    config = configuracion.find_one()

    return render_template(
        "configuracion.html",
        config=config
    )


# ================= GUARDAR CONFIG =================
@admin_bp.route("/guardar_configuracion", methods=["POST"])
def guardar_configuracion():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    try:
        import base64

        escudo_file = request.files.get("escudo")
        escudo_base64 = None

        if escudo_file and escudo_file.filename:
            escudo_base64 = base64.b64encode(
                escudo_file.read()
            ).decode("utf-8")

        config_actual = configuracion.find_one()

        if not escudo_base64 and config_actual:
            escudo_base64 = config_actual.get("escudo")

        configuracion.update_one(
            {},
            {
                "$set": {
                    "escuela": request.form.get("escuela"),
                    "ciclo": request.form.get("ciclo"),
                    "director": request.form.get("director"),
                    "direccion": request.form.get("direccion"),
                    "escudo": escudo_base64
                }
            },
            upsert=True
        )

        return redirect("/admin/configuracion")

    except Exception as e:
        return f"ERROR CONFIG: {str(e)}"


# ================= ADMINS SECUNDARIOS =================
@admin_bp.route("/admins")
def admins_panel():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "admins.html",
        admins=list(admins_secundarios.find()),
        auditoria=list(
            auditoria.find().sort("fecha", -1).limit(100)
        ),
        bitacora=list(
            bitacora.find().sort("fecha", -1).limit(100)
        )
    )


# ================= CREAR ADMIN =================
@admin_bp.route("/crear_admin_secundario", methods=["POST"])
def crear_admin_secundario():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    usuario = request.form.get("usuario")

    existe = admins_secundarios.find_one({
        "usuario": usuario
    })

    if existe:
        return redirect("/admin/admins")

    admins_secundarios.insert_one({
        "nombre": request.form.get("nombre"),
        "usuario": usuario,
        "password": request.form.get("password"),
        "escuela": request.form.get("escuela"),
        "rol": "admin",
        "activo": True,
        "fecha_creacion": datetime.now()
    })

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Creó admin secundario",
        "detalle": usuario,
        "fecha": datetime.now()
    })

    return redirect("/admin/admins")


# ================= DESACTIVAR ADMIN =================
@admin_bp.route("/desactivar_admin/<id>")
def desactivar_admin(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    admins_secundarios.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "activo": False
            }
        }
    )

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Desactivó admin",
        "detalle": id,
        "fecha": datetime.now()
    })

    return redirect("/admin/admins")


# ================= ACTIVAR ADMIN =================
@admin_bp.route("/activar_admin/<id>")
def activar_admin(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    admins_secundarios.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "activo": True
            }
        }
    )

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Activó admin",
        "detalle": id,
        "fecha": datetime.now()
    })

    return redirect("/admin/admins")

# ================= ACTIVAR TRIMESTRE =================
@admin_bp.route("/activar_trimestre/<numero>")
def activar_trimestre_numero(numero):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    configuracion.update_many(
        {},
        {
            "$set": {
                "trimestre_1": numero == "1",
                "trimestre_2": numero == "2",
                "trimestre_3": numero == "3",
                "trimestre_activo": numero
            }
        },
        upsert=True
    )

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Activó trimestre",
        "detalle": f"Trimestre {numero}",
        "fecha": datetime.now()
    })

    return redirect("/admin")


# ================= ACTIVAR CAPTURA =================
@admin_bp.route("/activar_captura")
def activar_captura():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    configuracion.update_many(
        {},
        {
            "$set": {
                "captura_evaluaciones": True
            }
        },
        upsert=True
    )

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Activó captura evaluaciones",
        "fecha": datetime.now()
    })

    return redirect("/admin")


# ================= DESACTIVAR CAPTURA =================
@admin_bp.route("/desactivar_captura")
def desactivar_captura():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    configuracion.update_many(
        {},
        {
            "$set": {
                "captura_evaluaciones": False
            }
        },
        upsert=True
    )

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Desactivó captura evaluaciones",
        "fecha": datetime.now()
    })

    return redirect("/admin")

# ================= DESHABILITAR TRIMESTRE =================
@admin_bp.route("/deshabilitar_trimestre/<numero>")
def deshabilitar_trimestre(numero):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    campo = f"trimestre_{numero}"

    configuracion.update_many(
        {},
        {
            "$set": {
                campo: False
            }
        },
        upsert=True
    )

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Deshabilitó trimestre",
        "detalle": f"Trimestre {numero}",
        "fecha": datetime.now()
    })

    return redirect("/admin")

# ================= CITATORIOS =================
@admin_bp.route("/citatorios")
def admin_citatorios():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "citatorios.html",
        citatorios=list(citatorios.find()),
        alumnos=list(alumnos.find())
    )


# ================= CREAR CITATORIO =================
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
        "estatus": "pendiente",
        "enterado": False
    })

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Creó citatorio",
        "detalle": request.form.get("alumno"),
        "fecha": datetime.now()
    })

    return redirect("/admin/citatorios")


# ================= PDF CITATORIO =================
@admin_bp.route("/citatorio_pdf/<id>")
def citatorio_pdf(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    citatorio = citatorios.find_one({
        "_id": ObjectId(id)
    })

    pdf = generar_citatorio_pdf(citatorio)

    return send_file(
        pdf,
        as_attachment=False,
        download_name="citatorio.pdf",
        mimetype="application/pdf"
    )


# ================= CONFIRMAR ASISTENCIA =================
@admin_bp.route("/confirmar_asistencia/<id>")
def confirmar_asistencia(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    citatorios.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "estatus": "asistio",
                "enterado": True
            }
        }
    )

    return redirect("/admin/citatorios")

# ================= ELIMINAR CITATORIO =================
@admin_bp.route("/eliminar_citatorio/<id>")
def eliminar_citatorio(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    citatorios.delete_one({
        "_id": ObjectId(id)
    })

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Eliminó citatorio",
        "detalle": id,
        "fecha": datetime.now()
    })

    return redirect("/admin/citatorios")


# ================= EDITAR CITATORIO =================
@admin_bp.route("/editar_citatorio/<id>", methods=["POST"])
def editar_citatorio(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    citatorios.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "motivo": request.form.get("motivo"),
                "fecha_cita": request.form.get("fecha"),
                "hora": request.form.get("hora")
            }
        }
    )

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Editó citatorio",
        "detalle": id,
        "fecha": datetime.now()
    })

    return redirect("/admin/citatorios")


# ================= KARDEX PDF =================
@admin_bp.route("/kardex/<nombre>")
def kardex_pdf(nombre):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    pdf = generar_kardex(nombre)

    return send_file(
        pdf,
        as_attachment=False,
        download_name=f"kardex_{nombre}.pdf",
        mimetype="application/pdf"
    )


# ================= BOLETA PDF =================
@admin_bp.route("/boleta/<nombre>")
def boleta_pdf(nombre):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    pdf = generar_boleta(nombre)

    return send_file(
        pdf,
        as_attachment=False,
        download_name=f"boleta_{nombre}.pdf",
        mimetype="application/pdf"
    )


# ================= EXPEDIENTE =================


# ================= EDITAR EXPEDIENTE =================
@admin_bp.route("/editar_expediente/<id>")
def editar_expediente(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumno = alumnos.find_one({
        "_id": ObjectId(id)
    })

    if not alumno:
        return redirect("/admin")

    return render_template(
        "editar_expediente.html",
        alumno=alumno
    )


# ================= GUARDAR EXPEDIENTE =================
@admin_bp.route("/guardar_expediente/<id>", methods=["POST"])
def guardar_expediente(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumno_actual = alumnos.find_one({
        "_id": ObjectId(id)
    })

    foto_base64 = alumno_actual.get("foto", "")

    foto = request.files.get("foto")

    if foto and foto.filename:

        import base64

        foto_base64 = base64.b64encode(
            foto.read()
        ).decode("utf-8")

    alumnos.update_one(
        {
            "_id": ObjectId(id)
        },
        {
            "$set": {

                "nombre": request.form.get("nombre"),
                "curp": request.form.get("curp"),
                "sexo": request.form.get("sexo"),
                "fecha_nacimiento": request.form.get("fecha_nacimiento"),
                "telefono": request.form.get("telefono"),
                "direccion": request.form.get("direccion"),
                "escuela_procedencia": request.form.get("escuela_procedencia"),
                "promedio": request.form.get("promedio"),
                "afecciones": request.form.get("afecciones"),

                "padre_nombre": request.form.get("padre_nombre"),
                "padre_telefono": request.form.get("padre_telefono"),
                "padre_correo": request.form.get("padre_correo"),

                "grupo": request.form.get("grupo"),

                "usuario": request.form.get("usuario"),
                "password": request.form.get("password"),

                "foto": foto_base64
            }
        }
    )

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Editó expediente",
        "detalle": request.form.get("nombre"),
        "fecha": datetime.now()
    })

    return redirect(f"/admin/expediente/{id}")

@admin_bp.route("/expediente/<id>")
def expediente_alumno(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumno = alumnos.find_one({
        "_id": ObjectId(id)
    })

    if not alumno:
        return redirect("/admin")

    return render_template(
        "expediente.html",
        alumno=alumno
    )

# ================= REPORTES =================
@admin_bp.route("/reportes")
def admin_reportes():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "reportes.html",
        reportes=list(reportes.find())
    )

# ================= ELIMINAR REPORTE =================
@admin_bp.route("/eliminar_reporte/<id>")
def eliminar_reporte(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    reportes.delete_one({
        "_id": ObjectId(id)
    })

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Eliminó reporte",
        "detalle": id,
        "fecha": datetime.now()
    })

    return redirect("/admin/reportes")


# ================= PDF REPORTE =================
@admin_bp.route("/reporte_pdf/<id>")
def reporte_pdf(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    from pdf.generador import generar_reporte_pdf

    reporte = reportes.find_one({
        "_id": ObjectId(id)
    })

    pdf = generar_reporte_pdf(reporte)

    return send_file(
        pdf,
        as_attachment=False,
        download_name="reporte.pdf",
        mimetype="application/pdf"
    )


# ================= AVISOS =================
@admin_bp.route("/avisos")
def admin_avisos():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    return render_template(
        "avisos.html",
        avisos=list(
            avisos.find().sort("fecha", -1)
        )
    )


# ================= CREAR AVISO =================
@admin_bp.route("/crear_aviso", methods=["POST"])
def crear_aviso():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    avisos.insert_one({
        "tipo": request.form.get("tipo"),
        "titulo": request.form.get("titulo"),
        "mensaje": request.form.get("mensaje"),
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
    })

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Creó aviso",
        "detalle": request.form.get("titulo"),
        "fecha": datetime.now()
    })

    return redirect("/admin/avisos")


# ================= EDITAR AVISO =================
@admin_bp.route("/editar_aviso/<id>", methods=["POST"])
def editar_aviso(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    avisos.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "titulo": request.form.get("titulo"),
                "mensaje": request.form.get("mensaje")
            }
        }
    )

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Editó aviso",
        "detalle": id,
        "fecha": datetime.now()
    })

    return redirect("/admin/avisos")


# ================= ELIMINAR AVISO =================
@admin_bp.route("/eliminar_aviso/<id>")
def eliminar_aviso(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    avisos.delete_one({
        "_id": ObjectId(id)
    })

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Eliminó aviso",
        "detalle": id,
        "fecha": datetime.now()
    })

    return redirect("/admin/avisos")

# ================= EXPEDIENTE PDF =================
@admin_bp.route("/expediente_pdf/<id>")
def expediente_pdf(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumno = alumnos.find_one({
        "_id": ObjectId(id)
    })

    if not alumno:
        return redirect("/admin")

    from pdf.generador import generar_expediente_pdf

    pdf = generar_expediente_pdf(alumno)

    return send_file(
        pdf,
        as_attachment=False,
        download_name=f"expediente_{alumno['nombre']}.pdf",
        mimetype="application/pdf"
    )

# ================= PDF AUDITORIA =================
@admin_bp.route("/auditoria_pdf")
def auditoria_pdf():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    usuario = request.args.get("usuario", "")
    fecha = request.args.get("fecha", "")

    filtro = {}

    if usuario:
        filtro["usuario"] = usuario

    registros = list(
        auditoria.find(filtro).sort("fecha", -1)
    )

    pdf = generar_auditoria_pdf(registros)

    return send_file(
        pdf,
        as_attachment=False,
        download_name="auditoria.pdf",
        mimetype="application/pdf"
    )


# ================= PDF BITACORA =================
@admin_bp.route("/bitacora_pdf")
def bitacora_pdf():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    usuario = request.args.get("usuario", "")

    filtro = {}

    if usuario:
        filtro["usuario"] = usuario

    registros = list(
        bitacora.find(filtro).sort("fecha", -1)
    )

    pdf = generar_bitacora_pdf(registros)

    return send_file(
        pdf,
        as_attachment=False,
        download_name="bitacora.pdf",
        mimetype="application/pdf"
    )

# ================= EDITAR GRUPO ALUMNO =================
@admin_bp.route("/editar_grupo", methods=["POST"])
def editar_grupo():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    alumno_id = request.form.get("id")

    grupo = request.form.get("grupo")

    alumnos.update_one(
        {"_id": ObjectId(alumno_id)},
        {
            "$set": {
                "grupo": grupo
            }
        }
    )

    return redirect("/admin/alumnos")

# ================= SUBIR FOTO ALUMNO =================
@admin_bp.route("/subir_foto_alumno/<id>", methods=["POST"])
def subir_foto_alumno(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    foto = request.files.get("foto")

    if foto and foto.filename:

        import base64

        foto_base64 = base64.b64encode(
            foto.read()
        ).decode("utf-8")

        alumnos.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "foto": foto_base64
                }
            }
        )

    return redirect("/admin/alumnos")

# ================= ELIMINAR ADMIN SECUNDARIO =================
@admin_bp.route("/eliminar_admin/<id>")
def eliminar_admin(id):

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    admins_secundarios.delete_one({
        "_id": ObjectId(id)
    })

    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "Eliminó administrador",
        "detalle": id,
        "fecha": datetime.now()
    })

    return redirect("/admin/admins")

# ================= BACKUP =================
@admin_bp.route("/backup/descargar")
def descargar_backup():

    if not verificar_admin():
        return redirect(url_for("auth.login"))

    import json
    from io import BytesIO

    backup = {
        "alumnos": list(alumnos.find({}, {"_id": 0})),
        "maestros": list(maestros.find({}, {"_id": 0})),
        "grupos": list(grupos.find({}, {"_id": 0})),
        "materias": list(materias.find({}, {"_id": 0})),
        "horarios": list(horarios.find({}, {"_id": 0})),
        "reportes": list(reportes.find({}, {"_id": 0})),
        "citatorios": list(citatorios.find({}, {"_id": 0})),
        "avisos": list(avisos.find({}, {"_id": 0})),
        "configuracion": list(configuracion.find({}, {"_id": 0}))
    }

    archivo = BytesIO()

    archivo.write(
        json.dumps(
            backup,
            indent=4,
            default=str,
            ensure_ascii=False
        ).encode("utf-8")
    )

    archivo.seek(0)

    return send_file(
        archivo,
        as_attachment=True,
        download_name="backup_sistema.json",
        mimetype="application/json"
    )


# ================= RESET TOTAL =================
@admin_bp.route("/reset_total", methods=["POST"])
def reset_total():

   if session.get("usuario") != "admin":
    return redirect("/admin")

    confirmacion = request.form.get("confirmacion")

    if confirmacion != "ELIMINAR TODO":
        return redirect("/admin")

    # ================= BACKUP AUTOMÁTICO =================
    bitacora.insert_one({
        "usuario": session.get("usuario"),
        "accion": "RESET TOTAL DEL SISTEMA",
        "fecha": datetime.now()
    })

    # ================= LIMPIAR COLECCIONES =================
    alumnos.delete_many({})
    grupos.delete_many({})
    materias.delete_many({})
    horarios.delete_many({})
    reportes.delete_many({})
    citatorios.delete_many({})
    avisos.delete_many({})
    auditoria.delete_many({})
    bitacora.delete_many({})

    return redirect("/admin")