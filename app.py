from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import random
import string

app = Flask(__name__)
app.secret_key = "control_escolar_secret_key"

MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise Exception("MONGO_URI no configurado")

client = MongoClient(MONGO_URI)
db = client["control_escolar"]

# =====================================================
# UTILIDAD GENERAR PASSWORD
# =====================================================
def generar_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# =====================================================
# LOGIN DIRECCIÓN
# =====================================================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["usuario"] == "direccion" and request.form["password"] == "1234":
            session.clear()
            session["direccion"] = True
            return redirect("/admin")
        return render_template("login.html", error="Credenciales incorrectas")
    return render_template("login.html")

# =====================================================
# PANEL DIRECCIÓN
# =====================================================
@app.route("/admin")
def admin():
    if "direccion" not in session:
        return redirect("/")

    alumnos = list(db.alumnos.find())
    maestros = list(db.maestros.find())

    mensaje_password = session.pop("nueva_password", None)

    return render_template(
        "admin.html",
        alumnos=alumnos,
        maestros=maestros,
        nueva_password=mensaje_password
    )

# =====================================================
# REGISTRAR ALUMNO
# =====================================================
@app.route("/registrar_alumno", methods=["POST"])
def registrar_alumno():
    if "direccion" not in session:
        return redirect("/")

    password = request.form.get("password")
    if not password:
        password = generar_password()

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

# =====================================================
# REGISTRAR MAESTRO
# =====================================================
@app.route("/registrar_maestro", methods=["POST"])
def registrar_maestro():
    if "direccion" not in session:
        return redirect("/")

    password = request.form.get("password")
    if not password:
        password = generar_password()

    db.maestros.insert_one({
        "nombre": request.form["nombre"],
        "correo": request.form["correo"],
        "materia": request.form["materia"],
        "grupo": request.form["grupo"],
        "password": password
    })

    session["nueva_password"] = f"Contraseña del maestro: {password}"
    return redirect("/admin")

# =====================================================
# RESTAURAR PASSWORD MAESTRO
# =====================================================
@app.route("/reset_password_maestro/<id>")
def reset_password_maestro(id):
    if "direccion" not in session:
        return redirect("/")

    nueva = generar_password()

    db.maestros.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"password": nueva}}
    )

    session["nueva_password"] = f"Nueva contraseña del maestro: {nueva}"
    return redirect("/admin")

# =====================================================
# RESTAURAR PASSWORD ALUMNO
# =====================================================
@app.route("/reset_password_alumno/<id>")
def reset_password_alumno(id):
    if "direccion" not in session:
        return redirect("/")

    nueva = generar_password()

    db.alumnos.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"password": nueva}}
    )

    session["nueva_password"] = f"Nueva contraseña del alumno: {nueva}"
    return redirect("/admin")

# =====================================================
# ELIMINAR
# =====================================================
@app.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    db.alumnos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

@app.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):
    db.maestros.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

# =====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)