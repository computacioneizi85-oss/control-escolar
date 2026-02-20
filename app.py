from flask import Flask, render_template, request, redirect, session, send_file
from flask_pymongo import PyMongo
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from bson.objectid import ObjectId
from datetime import timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import io

# ========================= APP =========================
app = Flask(__name__)
app.secret_key = "ULTRA_SECRET_KEY_2026"

# ---------- SESIONES (Render - filesystem) ----------
SESSION_PATH = "/tmp/flask_session"
if not os.path.exists(SESSION_PATH):
    os.makedirs(SESSION_PATH)

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = SESSION_PATH
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)
Session(app)

# ---------- MONGODB (inicializa DESPUÉS de crear app) ----------
mongo = PyMongo()
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")

if not app.config["MONGO_URI"]:
    raise Exception("MONGO_URI no está configurado en Render")

mongo.init_app(app)

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
@app.route("/", methods=["GET", "POST"])
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
        else:
            return redirect("/")

    return render_template("login.html")

# ========================= CREAR ADMIN =========================
@app.route("/crear_admin")
def crear_admin():
    if not mongo.db.usuarios.find_one({"correo": "admin@escuela.com"}):
        mongo.db.usuarios.insert_one({
            "correo": "admin@escuela.com",
            "password": generate_password_hash("admin123"),
            "role": "admin"
        })
    return "Admin creado"

# ========================= PANEL ADMIN =========================
@app.route("/admin")
@login_required("admin")
def admin():
    alumnos = list(mongo.db.alumnos.find())
    maestros = list(mongo.db.maestros.find())
    grupos = list(mongo.db.grupos.find())
    return render_template("admin.html", alumnos=alumnos, maestros=maestros, grupos=grupos)

# ========================= PANEL MAESTRO =========================
@app.route("/maestro")
@login_required("maestro")
def maestro():
    maestro = mongo.db.maestros.find_one({"correo": session["user"]})

    if not maestro:
        return "<h2 style='text-align:center;margin-top:80px'>Cuenta de maestro no registrada</h2>"

    if "grupo" not in maestro or maestro["grupo"] == "":
        return "<h2 style='text-align:center;margin-top:80px'>Dirección debe asignarte un grupo</h2>"

    alumnos = list(mongo.db.alumnos.find({"grupo": maestro["grupo"]}))
    return render_template("maestro.html", alumnos=alumnos, grupo=maestro["grupo"])

# ========================= GRUPOS =========================
@app.route("/panel_grupos")
@login_required("admin")
def panel_grupos():
    grupos = list(mongo.db.grupos.find())
    return render_template("panel_grupos.html", grupos=grupos)

@app.route("/crear_grupo", methods=["POST"])
@login_required("admin")
def crear_grupo():
    nombre = request.form["nombre"].strip().upper()
    if not mongo.db.grupos.find_one({"nombre": nombre}):
        mongo.db.grupos.insert_one({"nombre": nombre})
    return redirect("/panel_grupos")

@app.route("/eliminar_grupo/<id>")
@login_required("admin")
def eliminar_grupo(id):
    mongo.db.grupos.delete_one({"_id": ObjectId(id)})
    return redirect("/panel_grupos")

# ========================= ASIGNAR MAESTRO =========================
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

# ========================= REPORTES DISCIPLINARIOS =========================
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
    reportes = list(mongo.db.reportes.find())
    return render_template("reportes_admin.html", reportes=reportes)

@app.route("/aprobar_reporte/<id>")
@login_required("admin")
def aprobar_reporte(id):
    mongo.db.reportes.update_one({"_id": ObjectId(id)}, {"$set": {"estado": "aprobado"}})
    return redirect("/reportes_admin")

# ========================= PDF =========================
def generar_pdf(reporte):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    pdf.setFont("Helvetica", 14)
    pdf.drawString(170, 750, "REPORTE DISCIPLINARIO ESCOLAR")

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, 720, f"Alumno: {reporte['alumno']}")
    pdf.drawString(50, 700, f"Grupo: {reporte['grupo']}")
    pdf.drawString(50, 680, f"Maestro: {reporte['maestro']}")
    pdf.drawString(50, 660, f"Fecha: {reporte['fecha']}")

    pdf.drawString(50, 630, "Motivo:")
    pdf.drawString(50, 610, reporte["razon"])

    pdf.drawString(50, 580, "Consecuencia:")
    pdf.drawString(50, 560, reporte["consecuencia"])

    pdf.line(80, 200, 250, 200)
    pdf.drawString(100, 185, "Firma Maestro")

    pdf.line(330, 200, 520, 200)
    pdf.drawString(360, 185, "Firma Padre/Tutor")

    pdf.save()
    buffer.seek(0)
    return buffer

@app.route("/reporte_pdf/<id>")
@login_required("admin")
def reporte_pdf(id):
    reporte = mongo.db.reportes.find_one({"_id": ObjectId(id)})
    return send_file(generar_pdf(reporte), mimetype="application/pdf",
                     as_attachment=True, download_name="reporte.pdf")

# ========================= MENÚS DIRECCIÓN =========================
@app.route("/reporte_asistencias")
@login_required("admin")
def reporte_asistencias():
    asistencias = list(mongo.db.asistencias.find())
    return render_template("reporte_asistencias.html", asistencias=asistencias)

@app.route("/reporte_participaciones")
@login_required("admin")
def reporte_participaciones():
    participaciones = list(mongo.db.participaciones.find())
    return render_template("reporte_participaciones.html", participaciones=participaciones)

@app.route("/reporte_calificaciones")
@login_required("admin")
def reporte_calificaciones():
    alumnos = list(mongo.db.alumnos.find())
    return render_template("reporte_calificaciones.html", alumnos=alumnos)

# ========================= LOGOUT =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")