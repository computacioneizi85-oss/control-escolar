
from flask import Flask, render_template, request, redirect, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = "ULTRA_SECRET_KEY_2026"

app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
mongo = PyMongo(app)

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

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        password = request.form["password"]

        user = mongo.db.usuarios.find_one({"correo": correo})
        if user and check_password_hash(user["password"], password):
            session["user"] = correo
            session["role"] = user["role"]
            return redirect("/" + user["role"])

        return "Usuario o contraseña incorrectos"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ADMIN
@app.route("/admin")
@login_required("admin")
def admin():
    alumnos = list(mongo.db.alumnos.find())
    maestros = list(mongo.db.maestros.find())
    return render_template("admin.html", alumnos=alumnos, maestros=maestros)

@app.route("/registrar_maestro", methods=["POST"])
@login_required("admin")
def registrar_maestro():
    nombre = request.form["nombre"]
    correo = request.form["correo"]
    password = generate_password_hash(request.form["password"])

    mongo.db.maestros.insert_one({"nombre": nombre, "correo": correo})
    mongo.db.usuarios.insert_one({"correo": correo,"password": password,"role": "maestro"})
    return redirect("/admin")

@app.route("/registrar_alumno", methods=["POST"])
@login_required("admin")
def registrar_alumno():
    nombre = request.form["nombre"]
    correo = request.form["correo"]
    grupo = request.form["grupo"]
    password = generate_password_hash(request.form["password"])

    mongo.db.alumnos.insert_one({
        "nombre": nombre,
        "correo": correo,
        "grupo": grupo,
        "calificaciones": []
    })

    mongo.db.usuarios.insert_one({"correo": correo,"password": password,"role": "alumno"})
    return redirect("/admin")

# MAESTRO
@app.route("/maestro")
@login_required("maestro")
def maestro():
    alumnos = list(mongo.db.alumnos.find())
    return render_template("maestro.html", alumnos=alumnos)

@app.route("/agregar_calificacion", methods=["POST"])
@login_required("maestro")
def agregar_calificacion():
    alumno = request.form["alumno"]
    materia = request.form["materia"]
    calificacion = request.form["calificacion"]

    mongo.db.alumnos.update_one(
        {"nombre": alumno},
        {"$push": {"calificaciones": {"materia": materia, "calificacion": calificacion}}}
    )
    return redirect("/maestro")

# ALUMNO
@app.route("/alumno")
@login_required("alumno")
def alumno():
    alumno = mongo.db.alumnos.find_one({"correo": session["user"]})
    return render_template("alumno.html", alumno=alumno)

if __name__ == "__main__":
    app.run(debug=True)
