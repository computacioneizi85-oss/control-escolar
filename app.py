from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = "control_escolar_secret"

# =============================
# CONEXION MONGODB ATLAS
# =============================

MONGO_URI = "mongodb+srv://joel:CAMELLO2052@cluster0.ethhsnm.mongodb.net/control_escolar?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)

db = client["control_escolar"]

alumnos = db.alumnos
maestros = db.maestros
grupos = db.grupos


# =============================
# PAGINA PRINCIPAL
# =============================

@app.route("/")
def index():
    return render_template("index.html")


# =============================
# LOGIN ADMIN
# =============================

@app.route("/login_admin", methods=["POST"])
def login_admin():

    usuario = request.form["usuario"]
    password = request.form["password"]

    if usuario == "admin" and password == "admin123":

        session["admin"] = True

        return redirect("/admin")

    return redirect("/")


# =============================
# LOGIN MAESTRO
# =============================

@app.route("/login_maestro", methods=["POST"])
def login_maestro():

    correo = request.form["correo"]
    password = request.form["password"]

    maestro = maestros.find_one({
        "correo": correo,
        "password": password
    })

    if maestro:

        session["maestro"] = correo

        return redirect("/panel_maestro")

    return redirect("/")


# =============================
# PANEL ADMIN
# =============================

@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/")

    lista_alumnos = list(alumnos.find())
    lista_maestros = list(maestros.find())
    lista_grupos = list(grupos.find())

    return render_template(
        "admin.html",
        alumnos=lista_alumnos,
        maestros=lista_maestros,
        grupos=lista_grupos
    )


# =============================
# PANEL MAESTRO
# =============================

@app.route("/panel_maestro")
def panel_maestro():

    if "maestro" not in session:
        return redirect("/")

    lista_alumnos = list(alumnos.find())

    return render_template(
        "panel_maestro.html",
        alumnos=lista_alumnos
    )


# =============================
# CREAR GRUPO
# =============================

@app.route("/crear_grupo", methods=["POST"])
def crear_grupo():

    nombre = request.form["nombre"]

    grupos.insert_one({
        "nombre": nombre
    })

    return redirect("/admin")


# =============================
# CREAR ALUMNO
# =============================

@app.route("/crear_alumno", methods=["POST"])
def crear_alumno():

    nombre = request.form["nombre"]
    correo = request.form["correo"]
    grupo = request.form["grupo"]

    alumnos.insert_one({
        "nombre": nombre,
        "correo": correo,
        "grupo": grupo
    })

    return redirect("/admin")


# =============================
# CREAR MAESTRO
# =============================

@app.route("/crear_maestro", methods=["POST"])
def crear_maestro():

    nombre = request.form["nombre"]
    correo = request.form["correo"]
    password = request.form["password"]

    maestros.insert_one({
        "nombre": nombre,
        "correo": correo,
        "password": password
    })

    return redirect("/admin")


# =============================
# CERRAR SESION
# =============================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =============================
# INICIAR SERVIDOR
# =============================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)