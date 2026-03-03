from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os
import random
import string

app = Flask(__name__)
app.secret_key = "control_escolar_secret_key"

# ===============================
# CONEXIÓN A MONGO
# ===============================
MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise Exception("MONGO_URI no configurado en Render")

client = MongoClient(MONGO_URI)
db = client["control_escolar"]

# ===============================
# GENERADOR DE PASSWORD
# ===============================
def generar_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# ===============================
# LOGIN DIRECCIÓN
# ===============================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["usuario"] == "direccion" and request.form["password"] == "1234":
            session.clear()
            session["direccion"] = True
            return redirect("/admin")
        return render_template("login.html", error="Credenciales incorrectas")
    return render_template("login.html")

# ===============================
# LOGOUT DIRECCIÓN
# ===============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ===============================
# PANEL DIRECCIÓN
# ===============================
@app.route("/admin")
def admin():
    if "direccion" not in session:
        return redirect("/")

    alumnos = list(db.alumnos.find())
    maestros = list(db.maestros.find())
    grupos = list(db.grupos.find())

    mensaje_password = session.pop("nueva_password", None)

    return render_template(
        "admin.html",
        alumnos=alumnos,
        maestros=maestros,
        grupos=grupos,
        nueva_password=mensaje_password
    )

# ===============================
# REGISTRAR ALUMNO
# ===============================
@app.route("/registrar_alumno", methods=["POST"])
def registrar_alumno():
    if "direccion" not in session:
        return redirect("/")

    password = request.form.get("password") or generar_password()

    db.alumnos.insert_one({
        "nombre": request.form["nombre"],
        "apellido": request.form["apellido"],
        "correo": request.form["correo"],
        "grado": request.form["grado"],
        "grupo": request.form["grupo"],
        "password": password
    })

    session["nueva_password"] = f"Contraseña del alumno: {password}"
    return redirect("/admin")

# ===============================
# ELIMINAR ALUMNO
# ===============================
@app.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    if "direccion" not in session:
        return redirect("/")

    db.alumnos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

# ===============================
# RESET PASSWORD ALUMNO
# ===============================
@app.route("/reset_password_alumno/<id>")
def reset_password_alumno(id):
    if "direccion" not in session:
        return redirect("/")

    nueva = generar_password()
    db.alumnos.update_one({"_id": ObjectId(id)}, {"$set": {"password": nueva}})
    session["nueva_password"] = f"Nueva contraseña del alumno: {nueva}"
    return redirect("/admin")

# ===============================
# REGISTRAR MAESTRO
# ===============================
@app.route("/registrar_maestro", methods=["POST"])
def registrar_maestro():
    if "direccion" not in session:
        return redirect("/")

    password = request.form.get("password") or generar_password()

    db.maestros.insert_one({
        "nombre": request.form["nombre"],
        "correo": request.form["correo"],
        "materia": request.form["materia"],
        "grupo": request.form["grupo"],
        "password": password
    })

    session["nueva_password"] = f"Contraseña del maestro: {password}"
    return redirect("/admin")

# ===============================
# ELIMINAR MAESTRO
# ===============================
@app.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):
    if "direccion" not in session:
        return redirect("/")

    db.maestros.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

# ===============================
# RESET PASSWORD MAESTRO
# ===============================
@app.route("/reset_password_maestro/<id>")
def reset_password_maestro(id):
    if "direccion" not in session:
        return redirect("/")

    nueva = generar_password()
    db.maestros.update_one({"_id": ObjectId(id)}, {"$set": {"password": nueva}})
    session["nueva_password"] = f"Nueva contraseña del maestro: {nueva}"
    return redirect("/admin")

# ===============================
# CREAR GRUPO
# ===============================
@app.route("/crear_grupo", methods=["POST"])
def crear_grupo():
    if "direccion" not in session:
        return redirect("/")

    nombre = request.form.get("nombre_grupo")

    if not db.grupos.find_one({"nombre": nombre}):
        db.grupos.insert_one({"nombre": nombre})

    return redirect("/admin")

# ===============================
# ELIMINAR GRUPO
# ===============================
@app.route("/eliminar_grupo/<id>")
def eliminar_grupo(id):
    if "direccion" not in session:
        return redirect("/")

    db.grupos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

# ===============================
# LOGIN MAESTRO
# ===============================
@app.route("/login_maestro", methods=["GET", "POST"])
def login_maestro():
    if request.method == "POST":
        correo = request.form.get("correo")
        password = request.form.get("password")

        maestro = db.maestros.find_one({
            "correo": correo,
            "password": password
        })

        if maestro:
            session.clear()
            session["maestro_id"] = str(maestro["_id"])
            return redirect("/panel_maestro")
        else:
            return render_template("login_maestro.html", error="Credenciales incorrectas")

    return render_template("login_maestro.html")

# ===============================
# PANEL MAESTRO
# ===============================
@app.route("/panel_maestro")
def panel_maestro():
    if "maestro_id" not in session:
        return redirect("/login_maestro")

    maestro = db.maestros.find_one({"_id": ObjectId(session["maestro_id"])})
    alumnos = list(db.alumnos.find({"grupo": maestro.get("grupo")}))

    return render_template("panel_maestro.html", maestro=maestro, alumnos=alumnos)

# ===============================
# GUARDAR ASISTENCIA
# ===============================
@app.route("/guardar_asistencia", methods=["POST"])
def guardar_asistencia():
    if "maestro_id" not in session:
        return redirect("/login_maestro")

    maestro_id = session["maestro_id"]
    maestro = db.maestros.find_one({"_id": ObjectId(maestro_id)})
    fecha = datetime.now().strftime("%Y-%m-%d")

    for key in request.form:
        if key.startswith("alumno_"):
            alumno_id = key.replace("alumno_", "")
            estado = request.form.get(key)

            alumno = db.alumnos.find_one({"_id": ObjectId(alumno_id)})

            db.asistencias.insert_one({
                "alumno_id": alumno_id,
                "nombre_alumno": alumno["nombre"] + " " + alumno["apellido"],
                "grupo": maestro["grupo"],
                "fecha": fecha,
                "estado": estado,
                "maestro_id": maestro_id
            })

    return redirect("/panel_maestro")

# ===============================
# VER ASISTENCIAS EN DIRECCIÓN
# ===============================
@app.route("/asistencias_admin")
def asistencias_admin():
    if "direccion" not in session:
        return redirect("/")

    grupo = request.args.get("grupo")

    if grupo:
        asistencias = list(db.asistencias.find({"grupo": grupo}))
    else:
        asistencias = list(db.asistencias.find())

    grupos = list(db.grupos.find())

    return render_template(
        "asistencias_admin.html",
        asistencias=asistencias,
        grupos=grupos
    )

# ===============================
# LOGOUT MAESTRO
# ===============================
@app.route("/logout_maestro")
def logout_maestro():
    session.clear()
    return redirect("/login_maestro")

# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)