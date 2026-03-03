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
app.secret_key = "control_escolar_secret"

# ===============================
# CONEXIÓN MONGO
# ===============================
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise Exception("MONGO_URI no configurado")

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
    reportes = list(db.reportes.find())
    mensaje_password = session.pop("nueva_password", None)

    return render_template(
        "admin.html",
        alumnos=alumnos,
        maestros=maestros,
        grupos=grupos,
        reportes=reportes,
        nueva_password=mensaje_password
    )

# ===============================
# CONFIGURACIÓN
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
    if "direccion" not in session:
        return redirect("/")
    db.alumnos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

@app.route("/reset_password_alumno/<id>")
def reset_password_alumno(id):
    if "direccion" not in session:
        return redirect("/")
    nueva = generar_password()
    db.alumnos.update_one({"_id": ObjectId(id)}, {"$set": {"password": nueva}})
    session["nueva_password"] = f"Nueva contraseña alumno: {nueva}"
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

@app.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):
    if "direccion" not in session:
        return redirect("/")
    db.maestros.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

@app.route("/reset_password_maestro/<id>")
def reset_password_maestro(id):
    if "direccion" not in session:
        return redirect("/")
    nueva = generar_password()
    db.maestros.update_one({"_id": ObjectId(id)}, {"$set": {"password": nueva}})
    session["nueva_password"] = f"Nueva contraseña maestro: {nueva}"
    return redirect("/admin")

# ===============================
# GRUPOS
# ===============================
@app.route("/crear_grupo", methods=["POST"])
def crear_grupo():
    if "direccion" not in session:
        return redirect("/")
    nombre = request.form.get("nombre_grupo")
    if not db.grupos.find_one({"nombre": nombre}):
        db.grupos.insert_one({"nombre": nombre})
    return redirect("/admin")

@app.route("/eliminar_grupo/<id>")
def eliminar_grupo(id):
    if "direccion" not in session:
        return redirect("/")
    db.grupos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

# ===============================
# KARDEX PDF
# ===============================
@app.route("/kardex/<id>")
def generar_kardex(id):
    if "direccion" not in session and "maestro_id" not in session:
        return redirect("/")

    alumno = db.alumnos.find_one({"_id": ObjectId(id)})
    if not alumno:
        return "Alumno no encontrado"

    config = db.configuracion.find_one()

    if not os.path.exists("static"):
        os.makedirs("static")

    ruta = f"static/kardex_{id}.pdf"

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
        ["Alumno:", alumno["nombre"] + " " + alumno["apellido"]],
        ["Grado:", alumno["grado"]],
        ["Grupo:", alumno["grupo"]],
    ]

    tabla = Table(datos)
    tabla.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.grey)]))
    elementos.append(tabla)

    elementos.append(Spacer(1, 40))
    elementos.append(Paragraph("Firma Dirección: ____________________", styles["Normal"]))
    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph("Firma Padre/Tutor: ____________________", styles["Normal"]))

    doc.build(elementos)

    return redirect("/" + ruta)

# ===============================
# APROBAR REPORTE + PDF
# ===============================
@app.route("/aprobar_reporte/<id>")
def aprobar_reporte(id):
    if "direccion" not in session:
        return redirect("/")

    reporte = db.reportes.find_one({"_id": ObjectId(id)})
    if not reporte:
        return "Reporte no encontrado"

    db.reportes.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estado": "Aprobado"}}
    )

    generar_pdf_reporte(reporte)

    return redirect("/static/reporte_" + str(id) + ".pdf")

def generar_pdf_reporte(reporte):
    config = db.configuracion.find_one()

    if not os.path.exists("static"):
        os.makedirs("static")

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