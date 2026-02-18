from flask import Flask, render_template, request, redirect, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from bson.objectid import ObjectId
from datetime import timedelta
import os

app = Flask(__name__)
app.secret_key = "ULTRA_SECRET_KEY_2026"

# ================= SESIONES (ARREGLA ACCESO DENEGADO) =================
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.permanent_session_lifetime = timedelta(hours=8)

# ================= MONGODB =================
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
mongo = PyMongo(app)

# renovar sesion automaticamente
@app.before_request
def mantener_sesion_activa():
    if "user" in session:
        session.permanent = True
        session.modified = True

# ======================================================
# SEGURIDAD
# ======================================================
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

# ======================================================
# LOGIN
# ======================================================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"].strip().lower()
        password = request.form["password"]

        user = mongo.db.usuarios.find_one({"correo": correo})

        if not user:
            return "Usuario o contraseña incorrectos"

        if not check_password_hash(user["password"], password):
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

# ======================================================
# CREAR ADMIN (PRIMERA VEZ)
# ======================================================
@app.route("/crear_admin")
def crear_admin():
    if mongo.db.usuarios.find_one({"correo": "admin@escuela.com"}):
        return "El admin ya existe"

    mongo.db.usuarios.insert_one({
        "correo": "admin@escuela.com",
        "password": generate_password_hash("admin123"),
        "role": "admin"
    })
    return "ADMIN CREADO"

# ======================================================
# PANEL ADMIN
# ======================================================
@app.route("/admin")
@login_required("admin")
def admin():
    alumnos = list(mongo.db.alumnos.find())
    maestros = list(mongo.db.maestros.find())
    grupos = list(mongo.db.grupos.find())
    return render_template("admin.html", alumnos=alumnos, maestros=maestros, grupos=grupos)

# ======================================================
# REGISTRAR MAESTRO
# ======================================================
@app.route("/registrar_maestro", methods=["POST"])
@login_required("admin")
def registrar_maestro():
    nombre = request.form["nombre"]
    correo = request.form["correo"].strip().lower()
    password = generate_password_hash(request.form["password"])

    mongo.db.maestros.insert_one({"nombre": nombre, "correo": correo})
    mongo.db.usuarios.insert_one({"correo": correo, "password": password, "role": "maestro"})

    return redirect("/admin")

# ======================================================
# REGISTRAR ALUMNO
# ======================================================
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

# ======================================================
# RESET PASSWORD
# ======================================================
@app.route("/reset_password/<correo>")
@login_required("admin")
def reset_password(correo):
    mongo.db.usuarios.update_one(
        {"correo": correo},
        {"$set": {"password": generate_password_hash("123456")}}
    )
    return redirect("/admin")

# ======================================================
# ELIMINAR USUARIOS
# ======================================================
@app.route("/eliminar_alumno/<correo>")
@login_required("admin")
def eliminar_alumno(correo):
    mongo.db.alumnos.delete_one({"correo": correo})
    mongo.db.usuarios.delete_one({"correo": correo})
    mongo.db.asistencias.delete_many({"correo": correo})
    mongo.db.participaciones.delete_many({"correo": correo})
    return redirect("/admin")

@app.route("/eliminar_maestro/<correo>")
@login_required("admin")
def eliminar_maestro(correo):
    mongo.db.maestros.delete_one({"correo": correo})
    mongo.db.usuarios.delete_one({"correo": correo})
    return redirect("/admin")

# ======================================================
# CREAR / ELIMINAR GRUPOS
# ======================================================
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

@app.route("/eliminar_grupo/<grupo>")
@login_required("admin")
def eliminar_grupo(grupo):
    mongo.db.grupos.delete_one({"nombre": grupo})
    mongo.db.alumnos.update_many({"grupo": grupo}, {"$set": {"grupo": "SIN_GRUPO"}})
    return redirect("/panel_grupos")

# ======================================================
# ASIGNAR GRUPO A MAESTRO
# ======================================================
@app.route("/asignar_grupos")
@login_required("admin")
def asignar_grupos():
    maestros = list(mongo.db.maestros.find())
    grupos_db = list(mongo.db.grupos.find())
    grupos = [g["nombre"] for g in grupos_db]
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

# ======================================================
# PANEL MAESTRO (SOLO SU GRUPO)
# ======================================================
@app.route("/maestro")
@login_required("maestro")
def maestro():
    correo = session["user"]
    maestro = mongo.db.maestros.find_one({"correo": correo})

    if not maestro or "grupo" not in maestro:
        return "No tienes grupo asignado. Contacta a dirección."

    alumnos = list(mongo.db.alumnos.find({"grupo": maestro["grupo"]}))
    return render_template("maestro.html", alumnos=alumnos, grupo=maestro["grupo"])

# CALIFICACIONES
@app.route("/agregar_calificacion", methods=["POST"])
@login_required("maestro")
def agregar_calificacion():
    alumno_id = request.form["alumno"]
    materia = request.form["materia"]
    calificacion = request.form["calificacion"]

    mongo.db.alumnos.update_one(
        {"_id": ObjectId(alumno_id)},
        {"$push": {"calificaciones": {"materia": materia, "calificacion": calificacion}}}
    )
    return redirect("/maestro")

# ASISTENCIAS
@app.route("/asistencia")
@login_required("maestro")
def asistencia():
    correo = session["user"]
    maestro = mongo.db.maestros.find_one({"correo": correo})
    alumnos = list(mongo.db.alumnos.find({"grupo": maestro["grupo"]}))
    return render_template("asistencia.html", alumnos=alumnos)

@app.route("/guardar_asistencia", methods=["POST"])
@login_required("maestro")
def guardar_asistencia():
    fecha = request.form["fecha"]
    correo = session["user"]
    maestro = mongo.db.maestros.find_one({"correo": correo})

    for alumno in mongo.db.alumnos.find({"grupo": maestro["grupo"]}):
        estado = request.form.get(str(alumno["_id"]))

        mongo.db.asistencias.insert_one({
            "nombre": alumno["nombre"],
            "correo": alumno["correo"],
            "grupo": alumno["grupo"],
            "fecha": fecha,
            "estado": estado
        })

    return redirect("/maestro")

# PARTICIPACIONES
@app.route("/participaciones")
@login_required("maestro")
def participaciones():
    correo = session["user"]
    maestro = mongo.db.maestros.find_one({"correo": correo})
    alumnos = list(mongo.db.alumnos.find({"grupo": maestro["grupo"]}))
    return render_template("participaciones.html", alumnos=alumnos)

@app.route("/guardar_participacion", methods=["POST"])
@login_required("maestro")
def guardar_participacion():
    alumno_id = request.form["alumno"]
    tipo = request.form["tipo"]
    fecha = request.form["fecha"]

    alumno = mongo.db.alumnos.find_one({"_id": ObjectId(alumno_id)})

    mongo.db.participaciones.insert_one({
        "nombre": alumno["nombre"],
        "correo": alumno["correo"],
        "grupo": alumno["grupo"],
        "tipo": tipo,
        "fecha": fecha
    })

    return redirect("/maestro")

# ======================================================
# PANEL ALUMNO
# ======================================================
@app.route("/alumno")
@login_required("alumno")
def alumno():
    alumno = mongo.db.alumnos.find_one({"correo": session["user"]})
    asistencias = list(mongo.db.asistencias.find({"correo": session["user"]}))
    participaciones = list(mongo.db.participaciones.find({"correo": session["user"]}))
    return render_template("alumno.html", alumno=alumno,
                           asistencias=asistencias,
                           participaciones=participaciones)

# ======================================================
# LOGOUT
# ======================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
