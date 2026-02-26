from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = "control_escolar_secret_key"

# ----------------------------
# CONFIGURACION DE SESION (IMPORTANTE PARA RENDER)
# ----------------------------
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"


# ----------------------------
# CONEXION A MONGODB ATLAS
# ----------------------------
MONGO_URI = os.environ.get("MONGO_URI")

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=5000
)

try:
    client.admin.command("ping")
    print("MongoDB conectado correctamente")
except Exception as e:
    print("MongoDB no disponible al iniciar:", e)

db = client["control_escolar"]
coleccion_alumnos = db["alumnos"]


# =====================================================
# LOGIN
# =====================================================
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        usuario = request.form.get("usuario")
        password = request.form.get("password")

        if usuario == "direccion" and password == "1234":
            session["usuario"] = usuario
            session["rol"] = "direccion"
            return redirect(url_for("admin"))

        return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")


# =====================================================
# PANEL ADMIN
# =====================================================
@app.route("/admin")
def admin():

    if "usuario" not in session:
        return redirect(url_for("login"))

    lista_alumnos = list(coleccion_alumnos.find())

    return render_template("admin.html", alumnos=lista_alumnos)


# =====================================================
# FORMULARIO NUEVO ALUMNO
# =====================================================
@app.route("/nuevo_alumno")
def nuevo_alumno():

    if "usuario" not in session:
        return redirect(url_for("login"))

    return render_template("nuevo_alumno.html")


# =====================================================
# GUARDAR ALUMNO
# =====================================================
@app.route("/guardar_alumno", methods=["POST"])
def guardar_alumno():

    if "usuario" not in session:
        return redirect(url_for("login"))

    nombre = request.form.get("nombre")
    correo = request.form.get("correo")
    grupo = request.form.get("grupo")

    if nombre and correo and grupo:
        coleccion_alumnos.insert_one({
            "nombre": nombre,
            "correo": correo,
            "grupo": grupo
        })

    return redirect(url_for("admin"))


# =====================================================
# LOGOUT
# =====================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =====================================================
# ARRANQUE LOCAL (Render no usa esto)
# =====================================================
if __name__ == "__main__":
    app.run(debug=True)