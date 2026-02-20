from flask import Flask, render_template, request, redirect, session, send_file
from flask_pymongo import PyMongo
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from bson.objectid import ObjectId
from datetime import timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os, io, random, string

# ========================= APP =========================
app = Flask(__name__)
app.secret_key = "ULTRA_SECRET_KEY_2026"

# ---------- Evitar cache ----------
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ---------- SESIONES (Render) ----------
SESSION_PATH = "/tmp/flask_session"
if not os.path.exists(SESSION_PATH):
    os.makedirs(SESSION_PATH)

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = SESSION_PATH
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)
Session(app)

# ---------- MongoDB ----------
mongo = PyMongo()
mongo.db = None

app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
if not app.config["MONGO_URI"]:
    raise Exception("MONGO_URI no configurado en Render")

mongo.init_app(app)

# Forzar usar base control_escolar
db = mongo.cx["control_escolar"]
mongo.db = db

# ========================= UTILIDADES =========================
def generar_password(longitud=8):
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(longitud))

# ========================= SEGURIDAD =========================
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

# ========================= LOGIN =========================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"].strip().lower()
        password = request.form["password"]

        user = mongo.db.usuarios.find_one({"correo": correo})
        if not user or not check_password_hash(user["password"], password):
            return "Usuario o contraseña incorrectos"

        session.clear()
        session["user"] = correo
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect("/admin")
        elif user["role"] == "maestro":
            return redirect("/maestro")

    return render_template("login.html")

# ========================= PANEL ADMIN =========================
@app.route("/admin")
@login_required("admin")
def admin():
    alumnos = list(mongo.db.alumnos.find())
    maestros = list(mongo.db.maestros.find())
    grupos = list(mongo.db.grupos.find())
    return render_template("admin.html", alumnos=alumnos, maestros=maestros, grupos=grupos)

# ========================= REGISTRAR ALUMNO =========================
@app.route("/nuevo_alumno")
@login_required("admin")
def nuevo_alumno():
    grupos = list(mongo.db.grupos.find())
    return render_template("nuevo_alumno.html", grupos=grupos)

@app.route("/guardar_alumno", methods=["POST"])
@login_required("admin")
def guardar_alumno():
    nombre = request.form["nombre"].strip()
    correo = request.form["correo"].strip().lower()
    grupo = request.form["grupo"]
    password_manual = request.form.get("password")

    if not password_manual:
        password = generar_password()
    else:
        password = password_manual

    mongo.db.alumnos.insert_one({
        "nombre": nombre,
        "correo": correo,
        "grupo": grupo,
        "calificacion": ""
    })

    mongo.db.usuarios.insert_one({
        "correo": correo,
        "password": generate_password_hash(password),
        "role": "alumno"
    })

    return render_template("usuario_creado.html",
                           correo=correo,
                           password=password,
                           tipo="Alumno")

# ========================= REGISTRAR MAESTRO =========================
@app.route("/nuevo_maestro")
@login_required("admin")
def nuevo_maestro():
    return render_template("nuevo_maestro.html")

@app.route("/guardar_maestro", methods=["POST"])
@login_required("admin")
def guardar_maestro():
    nombre = request.form["nombre"].strip()
    correo = request.form["correo"].strip().lower()
    password_manual = request.form.get("password")

    if not password_manual:
        password = generar_password()
    else:
        password = password_manual

    mongo.db.maestros.insert_one({
        "nombre": nombre,
        "correo": correo,
        "grupo": ""
    })

    mongo.db.usuarios.insert_one({
        "correo": correo,
        "password": generate_password_hash(password),
        "role": "maestro"
    })

    return render_template("usuario_creado.html",
                           correo=correo,
                           password=password,
                           tipo="Maestro")

# ========================= PANEL MAESTRO =========================
@app.route("/maestro")
@login_required("maestro")
def maestro():
    correo = session["user"]
    maestro = mongo.db.maestros.find_one({"correo": correo})

    if not maestro or maestro.get("grupo","") == "":
        return "<h2 style='text-align:center;margin-top:80px'>Dirección aún no te asigna un grupo</h2>"

    alumnos = list(mongo.db.alumnos.find({"grupo": maestro["grupo"]}))
    return render_template("maestro.html", alumnos=alumnos, grupo=maestro["grupo"])

# ========================= ASIGNAR GRUPO =========================
@app.route("/asignar_grupos")
@login_required("admin")
def asignar_grupos():
    maestros = list(mongo.db.maestros.find())
    grupos = list(mongo.db.grupos.find())
    return render_template("asignar_grupos.html", maestros=maestros, grupos=grupos)

@app.route("/guardar_asignacion", methods=["POST"])
@login_required("admin")
def guardar_asignacion():
    maestro_id = request.form["maestro"]
    grupo = request.form["grupo"]

    mongo.db.maestros.update_one(
        {"_id": ObjectId(maestro_id)},
        {"$set": {"grupo": grupo}}
    )
    return redirect("/asignar_grupos")

# ========================= PDF REPORTE =========================
def generar_pdf(reporte):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    pdf.setFont("Helvetica",14)
    pdf.drawString(170,750,"REPORTE DISCIPLINARIO ESCOLAR")

    pdf.setFont("Helvetica",11)
    pdf.drawString(50,720,f"Alumno: {reporte['alumno']}")
    pdf.drawString(50,700,f"Grupo: {reporte['grupo']}")
    pdf.drawString(50,680,f"Maestro: {reporte['maestro']}")
    pdf.drawString(50,660,f"Fecha: {reporte['fecha']}")

    pdf.drawString(50,630,"Motivo:")
    pdf.drawString(50,610,reporte["razon"])

    pdf.drawString(50,580,"Consecuencia:")
    pdf.drawString(50,560,reporte["consecuencia"])

    pdf.line(80,200,250,200)
    pdf.drawString(100,185,"Firma Maestro")

    pdf.line(330,200,520,200)
    pdf.drawString(360,185,"Firma Padre/Tutor")

    pdf.save()
    buffer.seek(0)
    return buffer

@app.route("/reporte_pdf/<id>")
@login_required("admin")
def reporte_pdf(id):
    reporte = mongo.db.reportes.find_one({"_id": ObjectId(id)})
    return send_file(generar_pdf(reporte),
                     mimetype="application/pdf",
                     as_attachment=True,
                     download_name="reporte.pdf")

# ========================= LOGOUT =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ===== Render/Gunicorn =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)