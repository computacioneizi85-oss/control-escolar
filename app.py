from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = "control_escolar_secret"


# ======================================
# CONEXION A MONGODB ATLAS
# ======================================

MONGO_URI = "mongodb+srv://joel:CAMELLO2052@cluster0.ethhsnm.mongodb.net/control_escolar?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)

db = client["control_escolar"]

usuarios = db["usuarios"]
alumnos = db["alumnos"]
grupos = db["grupos"]


# ======================================
# CREAR ADMIN SI NO EXISTE
# ======================================

if usuarios.count_documents({"usuario": "admin"}) == 0:

    usuarios.insert_one({
        "usuario": "admin",
        "password": "1234",
        "rol": "admin"
    })


# ======================================
# LOGIN
# ======================================

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=['POST'])
def login():

    usuario = request.form['usuario']
    password = request.form['password']

    user = usuarios.find_one({
        "usuario": usuario,
        "password": password
    })

    if user:

        session["usuario"] = usuario
        session["rol"] = user["rol"]

        if user["rol"] == "admin":
            return redirect("/admin")

        if user["rol"] == "maestro":
            return redirect("/panel_maestro")

    return "Credenciales incorrectas"


# ======================================
# PANEL ADMIN
# ======================================

@app.route('/admin')
def admin():

    lista_alumnos = list(alumnos.find())
    lista_grupos = list(grupos.find())

    for a in lista_alumnos:
        a["_id"] = str(a["_id"])

    for g in lista_grupos:
        g["_id"] = str(g["_id"])

    return render_template(
        "admin.html",
        alumnos=lista_alumnos,
        grupos=lista_grupos
    )


# ======================================
# CREAR ALUMNO
# ======================================

@app.route('/crear_alumno', methods=['POST'])
def crear_alumno():

    alumnos.insert_one({

        "nombre": request.form['nombre'],
        "apellido": request.form['apellido'],
        "correo": request.form['correo'],
        "grupo": request.form['grupo']

    })

    return redirect("/admin")


# ======================================
# CREAR GRUPO
# ======================================

@app.route('/crear_grupo', methods=['POST'])
def crear_grupo():

    grupos.insert_one({

        "nombre": request.form['nombre']

    })

    return redirect("/admin")


# ======================================
# CREAR MAESTRO
# ======================================

@app.route('/crear_maestro', methods=['POST'])
def crear_maestro():

    usuarios.insert_one({

        "usuario": request.form['usuario'],
        "password": request.form['password'],
        "rol": "maestro"

    })

    return redirect("/admin")


# ======================================
# PANEL MAESTRO
# ======================================

@app.route('/panel_maestro')
def panel_maestro():

    lista_alumnos = list(alumnos.find())

    for a in lista_alumnos:
        a["_id"] = str(a["_id"])

    return render_template(
        "panel_maestro.html",
        alumnos=lista_alumnos
    )


# ======================================
# LOGOUT
# ======================================

@app.route('/logout')
def logout():

    session.clear()

    return redirect("/")


# ======================================
# RUN SERVER
# ======================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )