from flask import Flask, render_template, request, redirect, session, send_file
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from bson.objectid import ObjectId
from datetime import timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import io

app = Flask(__name__)
app.secret_key = "ULTRA_SECRET_KEY_2026"

# ===== SESIONES (ARREGLADO PARA RENDER) =====
app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.permanent_session_lifetime = timedelta(hours=8)

# ===== MONGODB =====
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
mongo = PyMongo(app)

@app.before_request
def mantener_sesion_activa():
    if "user" in session:
        session.permanent = True
        session.modified = True

# ===== SEGURIDAD =====
def login_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user" not in session:
                return redirect("/")
            if session.get("role") != role:
                return "Acceso denegado"
            return f(*args, **kwargs)
        return decorated
    return wrapper

# ===== LOGIN =====
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"].strip().lower()
        password = request.form["password"]

        user = mongo.db.usuarios.find_one({"correo": correo})
        if not user or not check_password_hash(user["password"], password):
            return "Usuario o contraseña incorrectos"

        session["user"] = correo
        session["role"] = user["role"]
        session.permanent = True

        if user["role"] == "admin":
            return redirect("/admin")
        elif user["role"] == "maestro":
            return redirect("/maestro")
        else:
            return redirect("/alumno")

    return render_template("login.html")

# ===== CREAR ADMIN =====
@app.route("/crear_admin")
def crear_admin():
    if mongo.db.usuarios.find_one({"correo": "admin@escuela.com"}):
        return "Admin ya existe"

    mongo.db.usuarios.insert_one({
        "correo": "admin@escuela.com",
        "password": generate_password_hash("admin123"),
        "role": "admin"
    })
    return "ADMIN CREADO"

# ===== PANEL ADMIN =====
@app.route("/admin")
@login_required("admin")
def admin():
    alumnos = list(mongo.db.alumnos.find())
    maestros = list(mongo.db.maestros.find())
    grupos = list(mongo.db.grupos.find())
    return render_template("admin.html", alumnos=alumnos, maestros=maestros, grupos=grupos)

# ===== REGISTRAR MAESTRO =====
@app.route("/registrar_maestro", methods=["POST"])
@login_required("admin")
def registrar_maestro():
    nombre = request.form["nombre"]
    correo = request.form["correo"].strip().lower()
    password = generate_password_hash(request.form["password"])

    mongo.db.maestros.insert_one({"nombre": nombre, "correo": correo})
    mongo.db.usuarios.insert_one({"correo": correo, "password": password, "role": "maestro"})
    return redirect("/admin")

# ===== REGISTRAR ALUMNO =====
@app.route("/registrar_alumno", methods=["POST"])
@login_required("admin")
def registrar_alumno():
    nombre = request.form["nombre"]
    correo = request.form["correo"].strip().lower()
    grupo = request.form["grupo"]
    password = generate_password_hash(request.form["password"])

    mongo.db.alumnos.insert_one({
        "nombre": nombre,
        "correo": correo,
        "grupo": grupo,
        "calificaciones": []
    })

    mongo.db.usuarios.insert_one({"correo": correo, "password": password, "role": "alumno"})
    return redirect("/admin")

# ===== PANEL MAESTRO =====
@app.route("/maestro")
@login_required("maestro")
def maestro():
    maestro = mongo.db.maestros.find_one({"correo": session["user"]})
    if not maestro or "grupo" not in maestro:
        return "No tienes grupo asignado"

    alumnos = list(mongo.db.alumnos.find({"grupo": maestro["grupo"]}))
    return render_template("maestro.html", alumnos=alumnos, grupo=maestro["grupo"])

# ===== REPORTES DISCIPLINARIOS =====
@app.route("/reportes")
@login_required("maestro")
def panel_reportes():
    maestro = mongo.db.maestros.find_one({"correo": session["user"]})
    alumnos = list(mongo.db.alumnos.find({"grupo": maestro["grupo"]}))
    reportes = list(mongo.db.reportes.find({"maestro": session["user"]}))
    return render_template("reportes_maestro.html", alumnos=alumnos, reportes=reportes)

@app.route("/crear_reporte", methods=["POST"])
@login_required("maestro")
def crear_reporte():
    alumno_id = request.form["alumno"]
    razon = request.form["razon"]
    fecha = request.form["fecha"]
    consecuencia = request.form["consecuencia"]

    alumno = mongo.db.alumnos.find_one({"_id": ObjectId(alumno_id)})

    mongo.db.reportes.insert_one({
        "alumno": alumno["nombre"],
        "correo_alumno": alumno["correo"],
        "grupo": alumno["grupo"],
        "maestro": session["user"],
        "fecha": fecha,
        "razon": razon,
        "consecuencia": consecuencia,
        "estado": "pendiente"
    })

    return redirect("/reportes")

@app.route("/reportes_admin")
@login_required("admin")
def reportes_admin():
    reportes = list(mongo.db.reportes.find().sort("fecha", -1))
    return render_template("reportes_admin.html", reportes=reportes)

@app.route("/aprobar_reporte/<id>")
@login_required("admin")
def aprobar_reporte(id):
    mongo.db.reportes.update_one({"_id": ObjectId(id)}, {"$set": {"estado": "aprobado"}})
    return redirect("/reportes_admin")

# ===== GENERADOR PDF =====
def generar_pdf(reporte):

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    pdf.setFont("Helvetica", 16)
    pdf.drawString(170, 750, "REPORTE DISCIPLINARIO ESCOLAR")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, 720, f"Alumno: {reporte['alumno']}")
    pdf.drawString(50, 700, f"Grupo: {reporte['grupo']}")
    pdf.drawString(50, 680, f"Maestro: {reporte['maestro']}")
    pdf.drawString(50, 660, f"Fecha: {reporte['fecha']}")

    pdf.drawString(50, 630, "Motivo del reporte:")
    y = 610
    for linea in str(reporte["razon"]).split("\n"):
        pdf.drawString(50, y, linea[:90])
        y -= 15

    pdf.drawString(50, y-10, "Consecuencia aplicada:")
    y -= 30
    for linea in str(reporte["consecuencia"]).split("\n"):
        pdf.drawString(50, y, linea[:90])
        y -= 15

    # Firmas
    pdf.line(80, 200, 250, 200)
    pdf.drawString(100, 185, "Firma del Maestro")

    pdf.line(330, 200, 520, 200)
    pdf.drawString(360, 185, "Firma del Padre o Tutor")

    pdf.line(200, 120, 400, 120)
    pdf.drawString(250, 105, "Firma de Dirección")

    pdf.drawString(80, 80, "Favor de entregar este documento firmado al día siguiente.")

    pdf.save()
    buffer.seek(0)
    return buffer

# ===== DESCARGAR PDF (FUNCIONA EN RENDER) =====
@app.route("/reporte_pdf/<id>")
def reporte_pdf(id):

    if "user" not in session:
        return redirect("/")

    reporte = mongo.db.reportes.find_one({"_id": ObjectId(id)})

    if session["role"] == "maestro":
        if reporte["maestro"] != session["user"]:
            return "No autorizado"

    buffer = generar_pdf(reporte)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="reporte_disciplinario.pdf",
        mimetype="application/pdf"
    )

# ===== LOGOUT =====
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
