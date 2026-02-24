from flask import Flask, render_template, request, redirect, session
from flask_pymongo import PyMongo
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from bson.objectid import ObjectId
from datetime import timedelta
import os, random, string
import unicodedata
import re
from pymongo import MongoClient

# ================= APP =================
app = Flask(__name__)
app.secret_key = "CONTROL_ESCOLAR_2026"

# ================= NORMALIZAR TEXTO =================
def normalizar(texto):
    if not texto:
        return ""
    texto = texto.lower().strip()
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')
    texto = re.sub(r'\s+', ' ', texto)
    return texto

# ================= SESIONES =================
SESSION_DIR = "/tmp/flask_session"
os.makedirs(SESSION_DIR, exist_ok=True)

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = SESSION_DIR
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)
Session(app)

# ================= MONGODB =================
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise Exception("Falta MONGO_URI en Render")

app.config["MONGO_URI"] = MONGO_URI
mongo = PyMongo(app)

cliente = MongoClient(MONGO_URI)
mongo.db = cliente["control_escolar"]

# ================= REPARAR REGISTROS =================
def reparar_registros():

    alumnos = list(mongo.db.alumnos.find())

    mapa_alumnos = {}
    for al in alumnos:
        mapa_alumnos[normalizar(al["nombre"])] = str(al["_id"])

    # ---- ASISTENCIAS ----
    asistencias = mongo.db.asistencias.find({"alumno_id": {"$exists": False}})
    for a in asistencias:
        if "alumno" in a:
            nombre = normalizar(a["alumno"])
            if nombre in mapa_alumnos:
                mongo.db.asistencias.update_one(
                    {"_id": a["_id"]},
                    {"$set": {"alumno_id": mapa_alumnos[nombre]}}
                )

    # ---- PARTICIPACIONES ----
    participaciones = mongo.db.participaciones.find({"alumno_id": {"$exists": False}})
    for p in participaciones:
        if "alumno" in p:
            nombre = normalizar(p["alumno"])
            if nombre in mapa_alumnos:
                mongo.db.participaciones.update_one(
                    {"_id": p["_id"]},
                    {"$set": {"alumno_id": mapa_alumnos[nombre]}}
                )

reparar_registros()

# ================= UTILIDADES =================
def generar_password(long=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(long))

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

# ================= CREAR ADMIN =================
def crear_admin():
    admin = mongo.db.usuarios.find_one({"correo":"admin@escuela.com"})
    if not admin:
        mongo.db.usuarios.insert_one({
            "correo":"admin@escuela.com",
            "password":generate_password_hash("admin123"),
            "role":"admin"
        })
crear_admin()

# ================= LOGIN =================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"].lower()
        password = request.form["password"]

        user = mongo.db.usuarios.find_one({"correo":correo})

        if not user or not check_password_hash(user["password"],password):
            return "Usuario o contraseña incorrectos"

        session["user"] = correo
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect("/admin")
        else:
            return redirect("/maestro")

    return render_template("login.html")

# ================= PANEL ADMIN =================
@app.route("/admin")
@login_required("admin")
def admin():
    alumnos=list(mongo.db.alumnos.find())
    maestros=list(mongo.db.maestros.find())
    grupos=list(mongo.db.grupos.find())
    return render_template("admin.html", alumnos=alumnos, maestros=maestros, grupos=grupos)

# ================= PANEL MAESTRO =================
@app.route("/maestro")
@login_required("maestro")
def maestro():
    correo=session["user"]
    maestro=mongo.db.maestros.find_one({"correo":correo})

    if not maestro or maestro.get("grupo","")=="":
        return "Aún no tienes grupo asignado"

    alumnos=list(mongo.db.alumnos.find({"grupo":maestro["grupo"]}))
    return render_template("maestro.html", alumnos=alumnos, grupo=maestro["grupo"])

# ================= ASISTENCIAS =================
@app.route("/reporte_asistencias")
@login_required("admin")
def reporte_asistencias():

    datos=list(mongo.db.asistencias.find().sort("fecha",-1))
    asistencias=[]

    for a in datos:

        nombre="Desconocido"
        grupo=""

        if "alumno_id" in a:
            alumno=mongo.db.alumnos.find_one({"_id":ObjectId(a["alumno_id"])})
            if alumno:
                nombre=alumno["nombre"]
                grupo=alumno.get("grupo","")

        asistencias.append({
            "nombre":nombre,
            "grupo":grupo,
            "fecha":a.get("fecha",""),
            "estado":a.get("estado","")
        })

    return render_template("reporte_asistencias.html", asistencias=asistencias)

# ================= PARTICIPACIONES =================
@app.route("/reporte_participaciones")
@login_required("admin")
def reporte_participaciones():

    datos=list(mongo.db.participaciones.find().sort("fecha",-1))
    participaciones=[]

    for p in datos:

        nombre="Desconocido"
        grupo=""

        if "alumno_id" in p:
            alumno=mongo.db.alumnos.find_one({"_id":ObjectId(p["alumno_id"])})
            if alumno:
                nombre=alumno["nombre"]
                grupo=alumno.get("grupo","")

        participaciones.append({
            "nombre":nombre,
            "grupo":grupo,
            "fecha":p.get("fecha",""),
            "puntos":p.get("puntos","")
        })

    return render_template("reporte_participaciones.html", participaciones=participaciones)

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)