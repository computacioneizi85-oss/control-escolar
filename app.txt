from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os
import random
import string

from werkzeug.utils import secure_filename

# PDF
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

app = Flask(__name__)
app.secret_key = "control_escolar_premium_secret"

# ===============================
# CONEXIÓN A MONGO
# ===============================
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise Exception("MONGO_URI no configurado en Render")

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
# PANEL DIRECCIÓN
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

    session["nueva_password"] = f"Contraseña del alumno: {password}"
    return redirect("/admin")

@app.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    db.alumnos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

@app.route("/reset_password_alumno/<id>")
def reset_password_alumno(id):
    nueva = generar_password()
    db.alumnos.update_one({"_id": ObjectId(id)}, {"$set": {"password": nueva}})
    session["nueva_password"] = f"Nueva contraseña del alumno: {nueva}"
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

    session["nueva_password"] = f"Contraseña del maestro: {password}"
    return redirect("/admin")

@app.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):
    db.maestros.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

@app.route("/reset_password_maestro/<id>")
def reset_password_maestro(id):
    nueva = generar_password()
    db.maestros.update_one({"_id": ObjectId(id)}, {"$set": {"password": nueva}})
    session["nueva_password"] = f"Nueva contraseña del maestro: {nueva}"
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

@app.route("/eliminar_grupo/<id>")
def eliminar_grupo(id):
    db.grupos.delete_one({"_id": ObjectId(id)})
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

@app.route("/logout_maestro")
def logout_maestro():
    session.clear()
    return redirect("/login_maestro")

# ===============================
# PANEL MAESTRO
# ===============================
@app.route("/panel_maestro")
def panel_maestro():
    maestro = db.maestros.find_one({"_id": ObjectId(session["maestro_id"])})
    alumnos = list(db.alumnos.find({"grupo": maestro.get("grupo")}))
    return render_template("panel_maestro.html", maestro=maestro, alumnos=alumnos)

# ===============================
# KARDEX PREMIUM
# ===============================
@app.route("/kardex/<id>")
def generar_kardex(id):

    alumno = db.alumnos.find_one({"_id": ObjectId(id)})
    asistencias = list(db.asistencias.find({"alumno_id": id}))
    reportes = list(db.reportes.find({"alumno_id": id, "estado": "Aprobado"}))
    config = db.configuracion.find_one()

    if not os.path.exists("static"):
        os.makedirs("static")

    ruta = f"static/kardex_{id}.pdf"
    doc = SimpleDocTemplate(ruta, pagesize=A4)
    elementos = []
    styles = getSampleStyleSheet()

    nombre_colegio = config["nombre_colegio"] if config else "Nombre del Colegio"
    ciclo = ciclo_escolar_actual()

    # Logo
    if config and config.get("logo"):
        logo_path = os.path.join("static", config["logo"])
        if os.path.exists(logo_path):
            elementos.append(Image(logo_path, width=120, height=80))
            elementos.append(Spacer(1, 20))

    elementos.append(Paragraph(f"<b>{nombre_colegio}</b>", styles["Title"]))
    elementos.append(Spacer(1, 10))
    elementos.append(Paragraph(f"Ciclo Escolar: {ciclo}", styles["Normal"]))
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
    elementos.append(Paragraph("Firma Dirección: ____________________________", styles["Normal"]))
    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph("Firma Padre/Tutor: ____________________________", styles["Normal"]))

    doc.build(elementos)

    return redirect(f"/static/kardex_{id}.pdf")

# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)