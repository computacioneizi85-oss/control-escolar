from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = "control_escolar_secret_key"

# ===============================
# CONEXION A MONGODB ATLAS
# ===============================

MONGO_URI = os.environ.get("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["control_escolar"]

usuarios = db["usuarios"]
alumnos = db["alumnos"]

# ===============================
# CREAR USUARIO ADMIN SI NO EXISTE
# ===============================

if usuarios.count_documents({"usuario": "direccion"}) == 0:
    usuarios.insert_one({
        "usuario": "direccion",
        "password": "1234",
        "rol": "admin"
    })

# ===============================
# LOGIN
# ===============================

@app.route("/", methods=["GET"])
def home():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    usuario = request.form["usuario"]
    password = request.form["password"]

    user = usuarios.find_one({
        "usuario": usuario,
        "password": password
    })

    if user:
        session["usuario"] = usuario
        return redirect(url_for("admin"))
    else:
        return render_template("login.html", error="Usuario o contraseña incorrectos")


# ===============================
# PANEL ADMIN
# ===============================

@app.route("/admin")
def admin():
    if "usuario" not in session:
        return redirect(url_for("home"))

    lista_alumnos = list(alumnos.find())
    return render_template("admin.html", alumnos=lista_alumnos)


# ===============================
# REGISTRAR ALUMNO
# ===============================

@app.route("/registrar_alumno", methods=["POST"])
def registrar_alumno():

    if "usuario" not in session:
        return redirect(url_for("home"))

    nombre = request.form["nombre"]
    correo = request.form["correo"]
    grupo = request.form["grupo"]

    alumnos.insert_one({
        "nombre": nombre,
        "correo": correo,
        "grupo": grupo
    })

    return redirect(url_for("admin"))


# ===============================
# ELIMINAR ALUMNO
# ===============================

@app.route("/eliminar_alumno/<id>", methods=["POST"])
def eliminar_alumno():

    if "usuario" not in session:
        return redirect(url_for("home"))

    alumnos.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("admin"))


# ===============================
# CERRAR SESION
# ===============================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))