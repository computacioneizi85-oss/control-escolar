# ===================== IMPORTS =====================
from flask import Flask, render_template, request, redirect, session, send_file
from flask_pymongo import PyMongo
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from bson.objectid import ObjectId
from datetime import timedelta
import os, random, string, io

# ===================== APP =====================
app = Flask(__name__)
app.secret_key = "CONTROL_ESCOLAR_SECRET_2026"

# --- Evitar cache (ver cambios al instante) ---
@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# --- Sesiones (Render usa /tmp) ---
SESSION_DIR = "/tmp/flask_session"
os.makedirs(SESSION_DIR, exist_ok=True)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = SESSION_DIR
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)
Session(app)

# ===================== MONGODB =====================
# Debes tener MONGO_URI configurado en Render (Environment)
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise Exception("Falta la variable de entorno MONGO_URI en Render")

app.config["MONGO_URI"] = MONGO_URI
mongo = PyMongo(app)

# Forzar base "control_escolar" aunque el URI no la traiga
from pymongo import MongoClient
cliente = MongoClient(MONGO_URI)
mongo.db = cliente["control_escolar"]

# ===================== UTILIDADES =====================
def generar_password(n=8):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(n))

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

# ===================== CREAR ADMIN AUTOMÁTICO =====================
def crear_admin():
    admin = mongo.db.usuarios.find_one({"correo": "admin@escuela.com"})
    if not admin:
        mongo.db.usuarios.insert_one({
            "correo": "admin@escuela.com",
            "password": generate_password_hash("admin123"),
            "role": "admin"
        })
        print("ADMIN CREADO → admin@escuela.com / admin123")

crear_admin()

# ===================== LOGIN =====================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"].strip().lower()
        password = request.form["password"]

        user = mongo.db.usuarios.find_one({"correo": correo})
        if not user or not check_password_hash(user["password"], password):
            return "Usuario o contraseña incorrectos"

        session["user"] = correo
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect("/admin")
        if user["role"] == "maestro":
            return redirect("/maestro")

    return render_template("login.html")

# ===================== PANEL DIRECCION =====================
@app.route("/admin")
@login_required("admin")
def admin():
    alumnos = list(mongo.db.alumnos.find())
    maestros = list(mongo.db.maestros.find())
    grupos = list(mongo.db.grupos.find())
    return render_template("admin.html", alumnos=alumnos, maestros=maestros, grupos=grupos)

# ===================== REGISTRAR MAESTRO =====================
@app.route("/nuevo_maestro")
@login_required("admin")
def nuevo_maestro():
    grupos = list(mongo.db.grupos.find().sort("nombre",1))
    return render_template("nuevo_maestro.html", grupos=grupos)

@app.route("/guardar_maestro", methods=["POST"])
@login_required("admin")
def guardar_maestro():
    nombre = request.form["nombre"]
    correo = request.form["correo"].lower()
    grupo = request.form["grupo"]
    password = request.form.get("password")

    if not password:
        password = generar_password()

    mongo.db.maestros.insert_one({
        "nombre": nombre,
        "correo": correo,
        "grupo": grupo
    })

    mongo.db.usuarios.insert_one({
        "correo": correo,
        "password": generate_password_hash(password),
        "role": "maestro"
    })

    return f"Maestro creado. Usuario: {correo} | Contraseña: {password} <br><a href='/admin'>Volver</a>"

# ===================== REGISTRAR ALUMNO =====================
@app.route("/nuevo_alumno")
@login_required("admin")
def nuevo_alumno():
    grupos = list(mongo.db.grupos.find())
    return render_template("nuevo_alumno.html", grupos=grupos)

@app.route("/guardar_alumno", methods=["POST"])
@login_required("admin")
def guardar_alumno():
    nombre = request.form["nombre"]
    correo = request.form["correo"].lower()
    grupo = request.form["grupo"]
    password = request.form.get("password")

    if not password:
        password = generar_password()

    mongo.db.alumnos.insert_one({
        "nombre": nombre,
        "correo": correo,
        "grupo": grupo
    })

    mongo.db.usuarios.insert_one({
        "correo": correo,
        "password": generate_password_hash(password),
        "role": "alumno"
    })

    return f"Alumno creado. Usuario: {correo} | Contraseña: {password} <br><a href='/admin'>Volver</a>"

# ===================== PANEL MAESTRO =====================
@app.route("/maestro")
@login_required("maestro")
def maestro():
    correo = session["user"]
    maestro = mongo.db.maestros.find_one({"correo": correo})

    if not maestro or not maestro.get("grupo"):
        return "<h2 style='text-align:center;margin-top:80px'>Dirección aún no te asigna grupo</h2>"

    alumnos = list(mongo.db.alumnos.find({"grupo": maestro["grupo"]}))
    return render_template("maestro.html", alumnos=alumnos, grupo=maestro["grupo"])

# ===================== ASISTENCIAS (SEGURO) =====================
@app.route("/reporte_asistencias")
@login_required("admin")
def reporte_asistencias():
    asistencias_db = list(mongo.db.asistencias.find().sort("fecha",-1))
    asistencias = []

    for a in asistencias_db:
        nombre = "Desconocido"

        if "alumno_id" in a:
            try:
                alumno = mongo.db.alumnos.find_one({"_id": ObjectId(a["alumno_id"])})
                if alumno:
                    nombre = alumno["nombre"]
            except:
                pass
        elif "alumno" in a:
            nombre = a["alumno"]

        asistencias.append({
            "nombre": nombre,
            "fecha": a.get("fecha",""),
            "estado": a.get("estado","")
        })

    return render_template("reporte_asistencias.html", asistencias=asistencias)

# ===================== PARTICIPACIONES (SEGURO) =====================
@app.route("/reporte_participaciones")
@login_required("admin")
def reporte_participaciones():
    partes_db = list(mongo.db.participaciones.find().sort("fecha",-1))
    participaciones = []

    for p in partes_db:
        nombre = "Desconocido"

        if "alumno_id" in p:
            try:
                alumno = mongo.db.alumnos.find_one({"_id": ObjectId(p["alumno_id"])})
                if alumno:
                    nombre = alumno["nombre"]
            except:
                pass
        elif "alumno" in p:
            nombre = p["alumno"]

        participaciones.append({
            "nombre": nombre,
            "fecha": p.get("fecha",""),
            "puntos": p.get("puntos","")
        })

    return render_template("reporte_participaciones.html", participaciones=participaciones)

# ===================== LOGOUT =====================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ===================== RUN =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)