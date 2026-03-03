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

# =====================================================
# RUTA PRINCIPAL
# =====================================================
@app.route("/")
def home():
    return redirect(url_for("login"))

# =====================================================
# LOGIN DIRECCIÓN
# =====================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        password = request.form.get("password")

        if usuario == "direccion" and password == "1234":
            session.clear()
            session["direccion"] = True
            return redirect(url_for("admin"))
        else:
            return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")

# =====================================================
# LOGOUT DIRECCIÓN
# =====================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =====================================================
# PANEL DIRECCIÓN
# =====================================================
@app.route("/admin")
def admin():
    if "direccion" not in session:
        return redirect(url_for("login"))

    alumnos = list(db.alumnos.find())
    maestros = list(db.maestros.find())

    return render_template("admin.html", alumnos=alumnos, maestros=maestros)

# =====================================================
# REGISTRAR ALUMNO
# =====================================================
@app.route("/registrar_alumno", methods=["POST"])
def registrar_alumno():
    if "direccion" not in session:
        return redirect(url_for("login"))

    db.alumnos.insert_one({
        "nombre": request.form.get("nombre"),
        "apellido": request.form.get("apellido"),
        "correo": request.form.get("correo"),
        "grado": request.form.get("grado"),
        "grupo": request.form.get("grupo")
    })

    return redirect(url_for("admin"))

# =====================================================
# ELIMINAR ALUMNO
# =====================================================
@app.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    if "direccion" not in session:
        return redirect(url_for("login"))

    db.alumnos.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("admin"))

# =====================================================
# REGISTRAR MAESTRO
# =====================================================
@app.route("/registrar_maestro", methods=["POST"])
def registrar_maestro():
    if "direccion" not in session:
        return redirect(url_for("login"))

    db.maestros.insert_one({
        "nombre": request.form.get("nombre"),
        "correo": request.form.get("correo"),
        "materia": request.form.get("materia"),
        "grupo": request.form.get("grupo"),
        "password": "1234"
    })

    return redirect(url_for("admin"))

# =====================================================
# ELIMINAR MAESTRO
# =====================================================
@app.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):
    if "direccion" not in session:
        return redirect(url_for("login"))

    db.maestros.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("admin"))

# =====================================================
# RESET PASSWORD MAESTRO
# =====================================================
@app.route("/reset_password_maestro/<id>")
def reset_password_maestro(id):
    if "direccion" not in session:
        return redirect(url_for("login"))

    db.maestros.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"password": "maestro123"}}
    )

    return redirect(url_for("admin"))

# =====================================================
# LOGIN MAESTRO
# =====================================================
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
            return redirect(url_for("panel_maestro"))
        else:
            return render_template("login_maestro.html", error="Credenciales incorrectas")

    return render_template("login_maestro.html")

# =====================================================
# PANEL MAESTRO
# =====================================================
@app.route("/panel_maestro")
def panel_maestro():
    if "maestro_id" not in session:
        return redirect(url_for("login_maestro"))

    maestro = db.maestros.find_one({"_id": ObjectId(session["maestro_id"])})

    alumnos = list(db.alumnos.find({"grupo": maestro.get("grupo")}))

    return render_template(
        "panel_maestro.html",
        maestro=maestro,
        alumnos=alumnos
    )

# =====================================================
# LOGOUT MAESTRO
# =====================================================
@app.route("/logout_maestro")
def logout_maestro():
    session.clear()
    return redirect(url_for("login_maestro"))

# =====================================================
# EJECUCIÓN LOCAL
# =====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)