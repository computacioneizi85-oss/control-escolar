from flask import Flask, render_template, request, redirect, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = "ULTRA_SECRET_KEY_2026"

# ==== Cookies para HTTPS (Render) ====
# Configuración correcta para Render + navegadores PC
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 3600

# ==== MongoDB ====
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
mongo = PyMongo(app)

# ==========================================================
# SEGURIDAD
# ==========================================================
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

# ==========================================================
# LOGIN
# ==========================================================
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

        if user["role"] == "admin":
            return redirect("/admin")
        elif user["role"] == "maestro":
            return redirect("/maestro")
        else:
            return redirect("/alumno")

    return render_template("login.html")

# ==========================================================
# CREAR ADMIN (SOLO PRIMERA VEZ)
# ==========================================================
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

# ==========================================================
# PANEL ADMIN / DIRECCIÓN
# ==========================================================
@app.route("/admin")
@login_required("admin")
def admin():
    alumnos = list(mongo.db.alumnos.find())
    maestros = list(mongo.db.maestros.find())
    return render_template("admin.html", alumnos=alumnos, maestros=maestros)

# ---------- Registrar Maestro ----------
@app.route("/registrar_maestro", methods=["POST"])
@login_required("admin")
def registrar_maestro():
    nombre = request.form["nombre"]
    correo = request.form["correo"].strip().lower()
    password = generate_password_hash(request.form["password"])

    mongo.db.maestros.insert_one({"nombre": nombre, "correo": correo})
    mongo.db.usuarios.insert_one({"correo": correo, "password": password, "role": "maestro"})
    return redirect("/admin")

# ---------- Registrar Alumno ----------
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

# ---------- Reset Password ----------
@app.route("/reset_password/<correo>")
@login_required("admin")
def reset_password(correo):
    nueva = "123456"
    mongo.db.usuarios.update_one(
        {"correo": correo},
        {"$set": {"password": generate_password_hash(nueva)}}
    )
    return redirect("/admin")

# ---------- Eliminar ----------
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

# ==========================================================
# PANEL MAESTRO
# ==========================================================
@app.route("/maestro")
@login_required("maestro")
def maestro():
    alumnos = list(mongo.db.alumnos.find())
    return render_template("maestro.html", alumnos=alumnos)

# ---------- Calificaciones ----------
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

# ---------- Asistencias ----------
@app.route("/asistencia")
@login_required("maestro")
def asistencia():
    alumnos = list(mongo.db.alumnos.find())
    return render_template("asistencia.html", alumnos=alumnos)

@app.route("/guardar_asistencia", methods=["POST"])
@login_required("maestro")
def guardar_asistencia():
    fecha = request.form["fecha"]

    for alumno in mongo.db.alumnos.find():
        estado = request.form.get(str(alumno["_id"]))
        mongo.db.asistencias.insert_one({
            "alumno_id": alumno["_id"],
            "nombre": alumno["nombre"],
            "correo": alumno["correo"],
            "fecha": fecha,
            "estado": estado
        })

    return redirect("/maestro")

# ---------- Participaciones ----------
@app.route("/participaciones")
@login_required("maestro")
def participaciones():
    alumnos = list(mongo.db.alumnos.find())
    return render_template("participaciones.html", alumnos=alumnos)

@app.route("/guardar_participacion", methods=["POST"])
@login_required("maestro")
def guardar_participacion():
    alumno_id = request.form["alumno"]
    tipo = request.form["tipo"]
    fecha = request.form["fecha"]

    alumno = mongo.db.alumnos.find_one({"_id": ObjectId(alumno_id)})

    mongo.db.participaciones.insert_one({
        "alumno_id": alumno["_id"],
        "nombre": alumno["nombre"],
        "correo": alumno["correo"],
        "tipo": tipo,
        "fecha": fecha
    })
    return redirect("/maestro")

# ==========================================================
# PANEL ALUMNO
# ==========================================================
@app.route("/alumno")
@login_required("alumno")
def alumno():
    alumno = mongo.db.alumnos.find_one({"correo": session["user"]})
    asistencias = list(mongo.db.asistencias.find({"correo": session["user"]}))
    participaciones = list(mongo.db.participaciones.find({"correo": session["user"]}))
    return render_template("alumno.html", alumno=alumno,
                           asistencias=asistencias,
                           participaciones=participaciones)

# ==========================================================
# REPORTES DIRECCIÓN
# ==========================================================
@app.route("/reporte_asistencias")
@login_required("admin")
def reporte_asistencias():
    asistencias = list(mongo.db.asistencias.find().sort("fecha", -1))
    return render_template("reporte_asistencias.html", asistencias=asistencias)

@app.route("/reporte_participaciones")
@login_required("admin")
def reporte_participaciones():
    participaciones = list(mongo.db.participaciones.find().sort("fecha", -1))
    return render_template("reporte_participaciones.html", participaciones=participaciones)

@app.route("/reporte_calificaciones")
@login_required("admin")
def reporte_calificaciones():
    alumnos = list(mongo.db.alumnos.find())
    return render_template("reporte_calificaciones.html", alumnos=alumnos)

@app.route("/reporte_grupos")
@login_required("admin")
def reporte_grupos():
    grupos = mongo.db.alumnos.distinct("grupo")
    return render_template("reporte_grupos.html", grupos=grupos)

@app.route("/grupo/<grupo>")
@login_required("admin")
def ver_grupo(grupo):
    alumnos = list(mongo.db.alumnos.find({"grupo": grupo}))
    return render_template("ver_grupo.html", alumnos=alumnos, grupo=grupo)

# ==========================================================
# MODULO GRUPOS
# ==========================================================

@app.route("/grupos")
@login_required("admin")
def grupos():
    grupos = list(mongo.db.grupos.find())
    return render_template("grupos.html", grupos=grupos)


@app.route("/crear_grupo", methods=["POST"])
@login_required("admin")
def crear_grupo():
    nombre = request.form["nombre"]
    grado = request.form["grado"]

    mongo.db.grupos.insert_one({
        "nombre": nombre,
        "grado": grado
    })

    return redirect("/grupos")

@app.route("/grupo_detalle/<grupo>")
@login_required("admin")
def grupo_detalle(grupo):
    alumnos = list(mongo.db.alumnos.find({"grupo": grupo}))
    return render_template("grupo_detalle.html", alumnos=alumnos, grupo=grupo)


# ==========================================================
# LOGOUT
# ==========================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
