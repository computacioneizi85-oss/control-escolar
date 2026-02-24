from flask import Flask, render_template, request, redirect, session
from flask_pymongo import PyMongo
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from bson.objectid import ObjectId
from datetime import timedelta
import os, random, string

# ================= APP =================
app = Flask(__name__)
app.secret_key = "CONTROL_ESCOLAR_2026"

# ----------- SESIONES -----------
SESSION_DIR = "/tmp/flask_session"
os.makedirs(SESSION_DIR, exist_ok=True)

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = SESSION_DIR
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)
Session(app)

# ----------- MONGODB -----------
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise Exception("Debes configurar MONGO_URI en Render")

app.config["MONGO_URI"] = MONGO_URI
mongo = PyMongo(app)

from pymongo import MongoClient
cliente = MongoClient(MONGO_URI)
mongo.db = cliente["control_escolar"]

# ================= REPARAR REGISTROS ANTIGUOS =================
def reparar_registros():

    # ---- ASISTENCIAS ----
    asistencias = mongo.db.asistencias.find({"alumno_id": {"$exists": False}})

    for a in asistencias:
        if "alumno" in a:
            alumno = mongo.db.alumnos.find_one({"nombre": a["alumno"]})
            if alumno:
                mongo.db.asistencias.update_one(
                    {"_id": a["_id"]},
                    {"$set": {"alumno_id": str(alumno["_id"])}}
                )

    # ---- PARTICIPACIONES ----
    participaciones = mongo.db.participaciones.find({"alumno_id": {"$exists": False}})

    for p in participaciones:
        if "alumno" in p:
            alumno = mongo.db.alumnos.find_one({"nombre": p["alumno"]})
            if alumno:
                mongo.db.participaciones.update_one(
                    {"_id": p["_id"]},
                    {"$set": {"alumno_id": str(alumno["_id"])}}
                )

# ejecutar al iniciar servidor
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
    alumnos = list(mongo.db.alumnos.find())
    maestros = list(mongo.db.maestros.find())
    grupos = list(mongo.db.grupos.find())
    return render_template("admin.html", alumnos=alumnos, maestros=maestros, grupos=grupos)

# ================= CREAR MAESTRO =================
@app.route("/nuevo_maestro")
@login_required("admin")
def nuevo_maestro():
    grupos = list(mongo.db.grupos.find())
    return render_template("nuevo_maestro.html", grupos=grupos)

@app.route("/guardar_maestro", methods=["POST"])
@login_required("admin")
def guardar_maestro():

    nombre = request.form["nombre"]
    correo = request.form["correo"].lower()
    grupo = request.form["grupo"]
    password = request.form.get("password")

    if password == "":
        password = generar_password()

    mongo.db.maestros.insert_one({
        "nombre":nombre,
        "correo":correo,
        "grupo":grupo
    })

    mongo.db.usuarios.insert_one({
        "correo":correo,
        "password":generate_password_hash(password),
        "role":"maestro"
    })

    return redirect("/admin")

# ================= CREAR ALUMNO =================
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

    if password == "":
        password = generar_password()

    mongo.db.alumnos.insert_one({
        "nombre":nombre,
        "correo":correo,
        "grupo":grupo,
        "calificacion":""
    })

    mongo.db.usuarios.insert_one({
        "correo":correo,
        "password":generate_password_hash(password),
        "role":"alumno"
    })

    return redirect("/admin")

# ================= ELIMINAR =================
@app.route("/eliminar_alumno/<id>")
@login_required("admin")
def eliminar_alumno(id):
    alumno = mongo.db.alumnos.find_one({"_id":ObjectId(id)})
    if alumno:
        mongo.db.usuarios.delete_one({"correo":alumno["correo"]})
        mongo.db.alumnos.delete_one({"_id":ObjectId(id)})
    return redirect("/admin")

@app.route("/eliminar_maestro/<id>")
@login_required("admin")
def eliminar_maestro(id):
    maestro = mongo.db.maestros.find_one({"_id":ObjectId(id)})
    if maestro:
        mongo.db.usuarios.delete_one({"correo":maestro["correo"]})
        mongo.db.maestros.delete_one({"_id":ObjectId(id)})
    return redirect("/admin")

# ================= RESET PASSWORD =================
@app.route("/reset_password/<correo>")
@login_required("admin")
def reset_password(correo):
    nueva = generar_password()
    mongo.db.usuarios.update_one(
        {"correo":correo},
        {"$set":{"password":generate_password_hash(nueva)}}
    )
    return f"Nueva contraseña: {nueva}<br><a href='/admin'>Volver</a>"

# ================= PANEL MAESTRO =================
@app.route("/maestro")
@login_required("maestro")
def maestro():
    correo = session["user"]
    maestro = mongo.db.maestros.find_one({"correo":correo})

    if not maestro or maestro.get("grupo","")=="":
        return "Aún no tienes grupo asignado"

    alumnos = list(mongo.db.alumnos.find({"grupo":maestro["grupo"]}))
    return render_template("maestro.html", alumnos=alumnos, grupo=maestro["grupo"])

# ================= ASISTENCIAS =================
@app.route("/reporte_asistencias")
@login_required("admin")
def reporte_asistencias():
    datos = list(mongo.db.asistencias.find())
    asistencias=[]
    for a in datos:
        nombre=a.get("alumno","Desconocido")
        asistencias.append({
            "nombre":nombre,
            "fecha":a.get("fecha",""),
            "estado":a.get("estado","")
        })
    return render_template("reporte_asistencias.html", asistencias=asistencias)

# ================= PARTICIPACIONES =================
@app.route("/reporte_participaciones")
@login_required("admin")
def reporte_participaciones():
    datos=list(mongo.db.participaciones.find())
    participaciones=[]
    for p in datos:
        nombre=p.get("alumno","Desconocido")
        participaciones.append({
            "nombre":nombre,
            "fecha":p.get("fecha",""),
            "puntos":p.get("puntos","")
        })
    return render_template("reporte_participaciones.html", participaciones=participaciones)

# ================= CALIFICACIONES =================
@app.route("/reporte_calificaciones")
@login_required("admin")
def reporte_calificaciones():
    alumnos=list(mongo.db.alumnos.find())
    return render_template("reporte_calificaciones.html", alumnos=alumnos)

# ================= ASIGNAR GRUPO =================
@app.route("/asignar_grupos")
@login_required("admin")
def asignar_grupos():
    maestros=list(mongo.db.maestros.find())
    grupos=list(mongo.db.grupos.find())
    return render_template("asignar_grupos.html", maestros=maestros, grupos=grupos)

@app.route("/guardar_asignacion", methods=["POST"])
@login_required("admin")
def guardar_asignacion():
    maestro_id=request.form["maestro"]
    grupo=request.form["grupo"]
    mongo.db.maestros.update_one({"_id":ObjectId(maestro_id)},{"$set":{"grupo":grupo}})
    return redirect("/asignar_grupos")

# ================= REPORTES DISCIPLINARIOS =================
@app.route("/reportes_admin")
@login_required("admin")
def reportes_admin():
    reportes=list(mongo.db.reportes.find())
    return render_template("reportes_admin.html", reportes=reportes)

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)