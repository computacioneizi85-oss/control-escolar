from flask import Flask, render_template, request, redirect, session, url_for
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from pymongo import MongoClient
import os
import time

app = Flask(__name__)
app.secret_key = "ULTRA_SECRET_KEY_2026"


# CONFIGURACION PARA RENDER (COOKIES Y SESIONES)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = "None"
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600


# =========================
# CONEXION MONGODB ATLAS
# =========================
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")

mongo = PyMongo(app)

# ---- ESPERAR CONEXION REAL A MONGODB ----
db = None
for i in range(10):
    try:
        db = mongo.cx.get_database()
        db.command("ping")
        print("MongoDB conectado correctamente")
        break
    except Exception as e:
        print("Esperando conexión MongoDB...")
        time.sleep(2)

# =========================
# DECORADOR SEGURIDAD
# =========================
def login_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user" not in session:
                return redirect("/")
            if session["role"] != role:
                return "Acceso denegado"
            return f(*args, **kwargs)
        return decorated
    return wrapper

# =========================
# LOGIN
# =========================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        password = request.form["password"]

        usuarios = mongo.cx.get_database().usuarios
        user = usuarios.find_one({"correo": correo})

        if user and check_password_hash(user["password"], password):
            session["user"] = correo
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin")
            elif user["role"] == "maestro":
                return redirect("/maestro")
            else:
                return redirect("/alumno")

        return "Usuario o contraseña incorrectos"

    return render_template("login.html")

# =========================
# CREAR ADMIN (SOLO PRIMERA VEZ)
# =========================
@app.route("/crear_admin")
def crear_admin():
    from werkzeug.security import generate_password_hash

    usuarios = mongo.cx.get_database().usuarios

    admin_existente = usuarios.find_one({"correo": "admin@escuela.com"})
    if admin_existente:
        return "El admin ya existe"

    usuarios.insert_one({
        "correo": "admin@escuela.com",
        "password": generate_password_hash("admin123"),
        "role": "admin"
    })

    return "ADMIN CREADO, YA PUEDES INICIAR SESION"

# =========================
# ADMIN
# =========================
@app.route("/admin")
@login_required("admin")
def admin():
    database = mongo.cx.get_database()
    alumnos = list(database.alumnos.find())
    maestros = list(database.maestros.find())
    return render_template("admin.html", alumnos=alumnos, maestros=maestros)

# REGISTRAR MAESTRO
@app.route("/registrar_maestro", methods=["POST"])
@login_required("admin")
def registrar_maestro():
    database = mongo.cx.get_database()

    nombre = request.form["nombre"]
    correo = request.form["correo"]
    password = generate_password_hash(request.form["password"])

    database.maestros.insert_one({"nombre": nombre, "correo": correo})
    database.usuarios.insert_one({
        "correo": correo,
        "password": password,
        "role": "maestro"
    })

    return redirect("/admin")

# REGISTRAR ALUMNO
@app.route("/registrar_alumno", methods=["POST"])
@login_required("admin")
def registrar_alumno():
    database = mongo.cx.get_database()

    nombre = request.form["nombre"]
    correo = request.form["correo"]
    grupo = request.form["grupo"]
    password = generate_password_hash(request.form["password"])

    database.alumnos.insert_one({
        "nombre": nombre,
        "correo": correo,
        "grupo": grupo,
        "calificaciones": []
    })

    database.usuarios.insert_one({
        "correo": correo,
        "password": password,
        "role": "alumno"
    })

    return redirect("/admin")

# =========================
# MAESTRO
# =========================
@app.route("/maestro")
@login_required("maestro")
def maestro():
    database = mongo.cx.get_database()
    alumnos = list(database.alumnos.find())
    return render_template("maestro.html", alumnos=alumnos)

@app.route("/agregar_calificacion", methods=["POST"])
@login_required("maestro")
def agregar_calificacion():
    database = mongo.cx.get_database()

    alumno = request.form["alumno"]
    materia = request.form["materia"]
    calificacion = request.form["calificacion"]

    database.alumnos.update_one(
        {"nombre": alumno},
        {"$push": {"calificaciones": {"materia": materia, "calificacion": calificacion}}}
    )
    return redirect("/maestro")

# =========================
# ALUMNO
# =========================
@app.route("/alumno")
@login_required("alumno")
def alumno():
    database = mongo.cx.get_database()
    alumno = database.alumnos.find_one({"correo": session["user"]})
    return render_template("alumno.html", alumno=alumno)

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =========================
# RUN LOCAL
# =========================
if __name__ == "__main__":
    app.run(debug=True)
