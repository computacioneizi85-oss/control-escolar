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

# ===================== APP =====================
app = Flask(__name__)
app.secret_key = "ULTRA_SECRET_KEY_2026"

# -------- Evitar cache (ver cambios al instante) --------
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# -------- Sesiones (Render filesystem) --------
SESSION_PATH = "/tmp/flask_session"
os.makedirs(SESSION_PATH, exist_ok=True)

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = SESSION_PATH
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=12)
Session(app)

# -------- MongoDB --------
mongo = PyMongo()
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
if not app.config["MONGO_URI"]:
    raise Exception("Falta configurar MONGO_URI en Render")

mongo.init_app(app)
# Forzar usar la BD correcta aunque el URI no la tenga
mongo.db = mongo.cx["control_escolar"]

# ===================== UTILIDADES =====================
def generar_password(longitud=8):
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(longitud))

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
        elif user["role"] == "maestro":
            return redirect("/maestro")

    return render_template("login.html")

# ===================== PANEL ADMIN =====================
@app.route("/admin")
@login_required("admin")
def admin():
    alumnos = list(mongo.db.alumnos.find())
    maestros = list(mongo.db.maestros.find())
    grupos = list(mongo.db.grupos.find())
    return render_template("admin.html", alumnos=alumnos, maestros=maestros, grupos=grupos)

# ===================== REGISTRAR ALUMNO =====================
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
    password = request.form.get("password")

    if not password:
        password = generar_password()

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

    return render_template("usuario_creado.html", correo=correo, password=password, tipo="Alumno")

# ===================== REGISTRAR MAESTRO =====================
@app.route("/nuevo_maestro")
@login_required("admin")
def nuevo_maestro():
    return render_template("nuevo_maestro.html")

@app.route("/guardar_maestro", methods=["POST"])
@login_required("admin")
def guardar_maestro():
    nombre = request.form["nombre"].strip()
    correo = request.form["correo"].strip().lower()
    password = request.form.get("password")

    if not password:
        password = generar_password()

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

    return render_template("usuario_creado.html", correo=correo, password=password, tipo="Maestro")

# ===================== ELIMINAR =====================
@app.route("/eliminar_alumno/<id>")
@login_required("admin")
def eliminar_alumno(id):
    alumno = mongo.db.alumnos.find_one({"_id": ObjectId(id)})
    if alumno:
        mongo.db.usuarios.delete_one({"correo": alumno["correo"]})
        mongo.db.alumnos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

@app.route("/eliminar_maestro/<id>")
@login_required("admin")
def eliminar_maestro(id):
    maestro = mongo.db.maestros.find_one({"_id": ObjectId(id)})
    if maestro:
        mongo.db.usuarios.delete_one({"correo": maestro["correo"]})
        mongo.db.maestros.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

# ===================== RESET PASSWORD =====================
@app.route("/reset_password/<correo>")
@login_required("admin")
def reset_password(correo):
    nueva = generar_password()
    mongo.db.usuarios.update_one(
        {"correo": correo},
        {"$set": {"password": generate_password_hash(nueva)}}
    )
    return render_template("usuario_creado.html", correo=correo, password=nueva, tipo="Contraseña restablecida")

# ===================== ASIGNAR GRUPO =====================
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
    mongo.db.maestros.update_one({"_id": ObjectId(maestro_id)}, {"$set": {"grupo": grupo}})
    return redirect("/asignar_grupos")

# ===================== PANEL MAESTRO =====================
@app.route("/maestro")
@login_required("maestro")
def maestro():
    correo = session["user"]
    maestro = mongo.db.maestros.find_one({"correo": correo})

    if not maestro or maestro.get("grupo","") == "":
        return "<h2 style='text-align:center;margin-top:80px'>Dirección aún no te asigna un grupo</h2>"

    alumnos = list(mongo.db.alumnos.find({"grupo": maestro["grupo"]}))
    return render_template("maestro.html", alumnos=alumnos, grupo=maestro["grupo"])

# ===================== SUBMENÚS DIRECCIÓN (ROBUSTOS) =====================
@app.route("/reporte_asistencias")
@login_required("admin")
def reporte_asistencias():

    asistencias_db = list(mongo.db.asistencias.find().sort("fecha",-1))
    asistencias = []

    for a in asistencias_db:

        nombre = "Desconocido"

        # registros nuevos con alumno_id
        if "alumno_id" in a:
            try:
                alumno = mongo.db.alumnos.find_one({"_id": ObjectId(a["alumno_id"])})
                if alumno:
                    nombre = alumno["nombre"]
            except:
                pass

        # registros antiguos
        elif "alumno" in a:
            nombre = a["alumno"]

        asistencias.append({
            "nombre": nombre,
            "fecha": a.get("fecha",""),
            "estado": a.get("estado","")
        })

    return render_template("reporte_asistencias.html", asistencias=asistencias)


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


@app.route("/reporte_calificaciones")
@login_required("admin")
def reporte_calificaciones():
    alumnos = list(mongo.db.alumnos.find())
    return render_template("reporte_calificaciones.html", alumnos=alumnos)

@app.route("/grupo/<grupo>")
@login_required("admin")
def ver_grupo(grupo):
    alumnos = list(mongo.db.alumnos.find({"grupo":grupo}))
    maestros = list(mongo.db.maestros.find({"grupo":grupo}))
    grupos = list(mongo.db.grupos.find())
    return render_template("admin.html", alumnos=alumnos, maestros=maestros, grupos=grupos)

@app.route("/reportes_admin")
@login_required("admin")
def reportes_admin():
    reportes = list(mongo.db.reportes.find())
    return render_template("reportes_admin.html", reportes=reportes)

# ===================== LOGOUT =====================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# Para correr local / Gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)