from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import os

# -------- APP FLASK --------
app = Flask(__name__)
app.secret_key = "control_escolar_secret_2026"

# -------- CONEXION MONGO --------
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["control_escolar"]

alumnos = db["alumnos"]
maestros = db["maestros"]

# -------- LOGIN --------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        if usuario == "direccion" and password == "1234":
            session["user"] = usuario
            return redirect("/admin")
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")

# -------- PANEL ADMIN --------
@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect("/")
    
    lista_alumnos = list(alumnos.find())
    return render_template("admin.html", alumnos=lista_alumnos)

# -------- REGISTRAR ALUMNO --------
@app.route("/registrar_alumno", methods=["POST"])
def registrar_alumno():
    if "user" not in session:
        return redirect("/")

    nombre = request.form["nombre"]
    correo = request.form["correo"]
    grupo = request.form["grupo"]

    alumnos.insert_one({
        "nombre": nombre,
        "correo": correo,
        "grupo": grupo
    })

    return redirect("/admin")

# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# IMPORTANTE PARA RENDER
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)