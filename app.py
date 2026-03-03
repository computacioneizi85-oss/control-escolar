from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
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
# LOGIN
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
# PANEL ADMIN
# ==========================
@app.route("/admin")
def admin():
    if "usuario" not in session:
        return redirect(url_for("login"))

    alumnos = list(db.alumnos.find())
    return render_template("admin.html", alumnos=alumnos)

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

    from bson.objectid import ObjectId
    db.alumnos.delete_one({"_id": ObjectId(id)})

    return redirect(url_for("admin"))

# ==========================
# LOGOUT
# ==========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ==========================
# EJECUCIÓN LOCAL
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)