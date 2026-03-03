from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os
import random
import string
from werkzeug.utils import secure_filename

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

app = Flask(__name__)
app.secret_key = "control_escolar_premium_secret"

# ===============================
# CONEXIÓN MONGO
# ===============================
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["control_escolar"]

# ===============================
# UTILIDADES
# ===============================
def generar_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def ciclo_escolar_actual():
    hoy = datetime.now()
    año = hoy.year
    if hoy.month >= 8:
        return f"{año}-{año+1}"
    else:
        return f"{año-1}-{año}"

# ===============================
# LOGIN DIRECCIÓN
# ===============================
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["usuario"] == "direccion" and request.form["password"] == "1234":
            session.clear()
            session["direccion"] = True
            return redirect("/admin")
        return render_template("login.html", error="Credenciales incorrectas")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ===============================
# PANEL ADMIN
# ===============================
@app.route("/admin")
def admin():
    if "direccion" not in session:
        return redirect("/")

    alumnos = list(db.alumnos.find())
    maestros = list(db.maestros.find())
    grupos = list(db.grupos.find())
    mensaje_password = session.pop("nueva_password", None)

    return render_template(
        "admin.html",
        alumnos=alumnos,
        maestros=maestros,
        grupos=grupos,
        nueva_password=mensaje_password
    )

# ===============================
# CONFIGURACIÓN INSTITUCIONAL
# ===============================
@app.route("/configuracion", methods=["GET", "POST"])
def configuracion():
    if "direccion" not in session:
        return redirect("/")

    if request.method == "POST":
        nombre = request.form.get("nombre_colegio")
        logo = request.files.get("logo")

        config = db.configuracion.find_one()
        logo_nombre = None

        if logo and logo.filename != "":
            if not os.path.exists("static"):
                os.makedirs("static")
            logo_nombre = secure_filename(logo.filename)
            logo.save(os.path.join("static", logo_nombre))

        if config:
            db.configuracion.update_one(
                {"_id": config["_id"]},
                {"$set": {
                    "nombre_colegio": nombre,
                    "logo": logo_nombre if logo_nombre else config.get("logo")
                }}
            )
        else:
            db.configuracion.insert_one({
                "nombre_colegio": nombre,
                "logo": logo_nombre
            })

        return redirect("/configuracion")

    config = db.configuracion.find_one()
    return render_template("configuracion.html", config=config)

# ===============================
# ALUMNOS
# ===============================
@app.route("/registrar_alumno", methods=["POST"])
def registrar_alumno():
    password = request.form.get("password") or generar_password()

    db.alumnos.insert_one({
        "nombre": request.form["nombre"],
        "apellido": request.form["apellido"],
        "correo": request.form["correo"],
        "grado": request.form["grado"],
        "grupo": request.form["grupo"],
        "password": password
    })

    session["nueva_password"] = f"Contraseña alumno: {password}"
    return redirect("/admin")

@app.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    db.alumnos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

# ===============================
# MAESTROS
# ===============================
@app.route("/registrar_maestro", methods=["POST"])
def registrar_maestro():
    password = request.form.get("password") or generar_password()

    db.maestros.insert_one({
        "nombre": request.form["nombre"],
        "correo": request.form["correo"],
        "materia": request.form["materia"],
        "grupo": request.form["grupo"],
        "password": password
    })

    session["nueva_password"] = f"Contraseña maestro: {password}"
    return redirect("/admin")

# ===============================
# GRUPOS
# ===============================
@app.route("/crear_grupo", methods=["POST"])
def crear_grupo():
    nombre = request.form.get("nombre_grupo")
    if not db.grupos.find_one({"nombre": nombre}):
        db.grupos.insert_one({"nombre": nombre})
    return redirect("/admin")

# ===============================
# LOGIN MAESTRO
# ===============================
@app.route("/login_maestro", methods=["GET", "POST"])
def login_maestro():
    if request.method == "POST":
        maestro = db.maestros.find_one({
            "correo": request.form["correo"],
            "password": request.form["password"]
        })
        if maestro:
            session.clear()
            session["maestro_id"] = str(maestro["_id"])
            return redirect("/panel_maestro")
        return render_template("login_maestro.html", error="Credenciales incorrectas")
    return render_template("login_maestro.html")

@app.route("/panel_maestro")
def panel_maestro():
    if "maestro_id" not in session:
        return redirect("/login_maestro")

    maestro = db.maestros.find_one({"_id": ObjectId(session["maestro_id"])})
    alumnos = list(db.alumnos.find({"grupo": maestro["grupo"]}))
    return render_template("panel_maestro.html", maestro=maestro, alumnos=alumnos)

# ===============================
# ASISTENCIAS
# ===============================
@app.route("/guardar_asistencia", methods=["POST"])
def guardar_asistencia():
    if "maestro_id" not in session:
        return redirect("/login_maestro")

    maestro = db.maestros.find_one({"_id": ObjectId(session["maestro_id"])})
    fecha = datetime.now().strftime("%Y-%m-%d")

    for key in request.form:
        if key.startswith("alumno_"):
            alumno_id = key.replace("alumno_", "")
            estado = request.form.get(key)

            db.asistencias.delete_many({
                "alumno_id": alumno_id,
                "fecha": fecha
            })

            db.asistencias.insert_one({
                "alumno_id": alumno_id,
                "grupo": maestro["grupo"],
                "fecha": fecha,
                "estado": estado
            })

    return redirect("/panel_maestro")

@app.route("/asistencias_admin")
def asistencias_admin():
    if "direccion" not in session:
        return redirect("/")

    asistencias = list(db.asistencias.find())
    return render_template("asistencias_admin.html", asistencias=asistencias)

# ===============================
# REPORTES DISCIPLINARIOS
# ===============================
@app.route("/crear_reporte", methods=["POST"])
def crear_reporte():
    if "maestro_id" in session:
        creador = "Maestro"
    elif "direccion" in session:
        creador = "Dirección"
    else:
        return redirect("/")

    alumno_id = request.form["alumno_id"]
    alumno = db.alumnos.find_one({"_id": ObjectId(alumno_id)})

    db.reportes.insert_one({
        "alumno_id": alumno_id,
        "nombre_alumno": alumno["nombre"] + " " + alumno["apellido"],
        "motivo": request.form["motivo"],
        "consecuencia": request.form["consecuencia"],
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "estado": "Pendiente",
        "creado_por": creador
    })

    return redirect("/admin")

@app.route("/reportes_admin")
def reportes_admin():
    if "direccion" not in session:
        return redirect("/")
    reportes = list(db.reportes.find())
    return render_template("reportes_admin.html", reportes=reportes)

@app.route("/aprobar_reporte/<id>")
def aprobar_reporte(id):
    if "direccion" not in session:
        return redirect("/")

    reporte = db.reportes.find_one({"_id": ObjectId(id)})
    db.reportes.update_one({"_id": ObjectId(id)}, {"$set": {"estado": "Aprobado"}})

    generar_pdf_reporte(reporte)
    return redirect("/reportes_admin")

# ===============================
# PDF REPORTE
# ===============================
def generar_pdf_reporte(reporte):

    config = db.configuracion.find_one()
    ruta = f"static/reporte_{reporte['_id']}.pdf"

    doc = SimpleDocTemplate(ruta, pagesize=A4)
    elementos = []
    styles = getSampleStyleSheet()

    if config and config.get("logo"):
        logo_path = os.path.join("static", config["logo"])
        if os.path.exists(logo_path):
            elementos.append(Image(logo_path, width=120, height=80))
            elementos.append(Spacer(1, 20))

    nombre_colegio = config["nombre_colegio"] if config else "Colegio"
    elementos.append(Paragraph(f"<b>{nombre_colegio}</b>", styles["Title"]))
    elementos.append(Spacer(1, 10))
    elementos.append(Paragraph(f"Ciclo Escolar: {ciclo_escolar_actual()}", styles["Normal"]))
    elementos.append(Spacer(1, 20))

    datos = [
        ["Alumno:", reporte["nombre_alumno"]],
        ["Motivo:", reporte["motivo"]],
        ["Consecuencia:", reporte["consecuencia"]],
        ["Fecha:", reporte["fecha"]],
    ]

    tabla = Table(datos)
    tabla.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.grey)]))
    elementos.append(tabla)

    elementos.append(Spacer(1, 40))
    elementos.append(Paragraph("Firma Dirección: ____________________", styles["Normal"]))
    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph("Firma Padre/Tutor: ____________________", styles["Normal"]))

    doc.build(elementos)

# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)