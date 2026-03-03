from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = "control_escolar_secret_key"

# ==========================
# CONEXIÓN A MONGO
# ==========================
MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise Exception("MONGO_URI no está configurado en Render")

client = MongoClient(MONGO_URI)
db = client["control_escolar"]

# ==========================
# RUTA PRINCIPAL
# ==========================
@app.route("/")
def home():
    return redirect(url_for("login"))

# ==========================
# LOGIN DIRECCIÓN
# ==========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        password = request.form.get("password")

        # Usuario fijo de dirección (puedes cambiarlo)
        if usuario == "direccion" and password == "1234":
            session["usuario"] = usuario
            return redirect(url_for("admin"))
        else:
            return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")

# ==========================
# LOGOUT
# ==========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ==========================
# PANEL ADMIN
# ==========================
@app.route("/admin")
def admin():
    if "usuario" not in session:
        return redirect(url_for("login"))

    alumnos = list(db.alumnos.find())
    maestros = list(db.maestros.find())

    return render_template("admin.html", alumnos=alumnos, maestros=maestros)

# ==========================
# REGISTRAR ALUMNO
# ==========================
@app.route("/registrar_alumno", methods=["POST"])
def registrar_alumno():
    if "usuario" not in session:
        return redirect(url_for("login"))

    nombre = request.form.get("nombre")
    apellido = request.form.get("apellido")
    correo = request.form.get("correo")
    grado = request.form.get("grado")
    grupo = request.form.get("grupo")

    db.alumnos.insert_one({
        "nombre": nombre,
        "apellido": apellido,
        "correo": correo,
        "grado": grado,
        "grupo": grupo
    })

    return redirect(url_for("admin"))

# ==========================
# ELIMINAR ALUMNO
# ==========================
@app.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    db.alumnos.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("admin"))

# ==========================
# REGISTRAR MAESTRO
# ==========================
@app.route("/registrar_maestro", methods=["POST"])
def registrar_maestro():
    if "usuario" not in session:
        return redirect(url_for("login"))

    nombre = request.form.get("nombre")
    correo = request.form.get("correo")
    materia = request.form.get("materia")

    password = "1234"  # contraseña inicial

    db.maestros.insert_one({
        "nombre": nombre,
        "correo": correo,
        "materia": materia,
        "password": password
    })

    return redirect(url_for("admin"))

# ==========================
# ELIMINAR MAESTRO
# ==========================
@app.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    db.maestros.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("admin"))

# ==========================
# RESTAURAR CONTRASEÑA MAESTRO
# ==========================
@app.route("/reset_password_maestro/<id>")
def reset_password_maestro(id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    nueva_password = "maestro123"

    db.maestros.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"password": nueva_password}}
    )

    return redirect(url_for("admin"))

# ==========================
# EJECUCIÓN LOCAL
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)