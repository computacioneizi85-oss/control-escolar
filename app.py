```python
# ==========================================
# CONTROL ESCOLAR - VERSION COMPATIBLE MONGO
# ESTABLE PARA RENDER
# ==========================================

from flask import Flask, render_template, request, redirect, session, flash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2 import TemplateNotFound
import os

app = Flask(__name__)
app.secret_key = "CONTROL_ESCOLAR_2026_PRO"

# ---------------- MONGODB ----------------
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["control_escolar"]

usuarios = db.usuarios
alumnos = db.alumnos
grupos = db.grupos
asistencias = db.asistencias
participaciones = db.participaciones
calificaciones = db.calificaciones
reportes = db.reportes

# ---------------- SAFE RENDER ----------------
def safe_render(template, **context):
    try:
        return render_template(template, **context)
    except TemplateNotFound:
        return f"<h2 style='color:red'>Falta el archivo: {template}</h2>"

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        password = request.form["password"]

        user = usuarios.find_one({"correo": correo})

        if user and check_password_hash(user["password"], password):
            session["usuario"] = str(user["_id"])
            session["rol"] = user["rol"]

            if user["rol"] == "admin":
                return redirect("/admin")
            elif user["rol"] == "maestro":
                return redirect("/maestro")

        flash("Correo o contraseña incorrectos")

    return safe_render("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- PANEL ADMIN ----------------
@app.route("/admin")
def admin():
    if session.get("rol") != "admin":
        return redirect("/")

    lista_alumnos = list(alumnos.find())
    lista_maestros = list(usuarios.find({"rol": "maestro"}))
    lista_grupos = list(grupos.find())

    return safe_render("admin.html",
        alumnos=lista_alumnos,
        maestros=lista_maestros,
        grupos=lista_grupos
    )

# ---------------- CREAR GRUPO ----------------
@app.route("/crear_grupo", methods=["POST"])
def crear_grupo():
    if session.get("rol") != "admin":
        return redirect("/")

    nombre = request.form["nombre"]

    if not grupos.find_one({"nombre": nombre}):
        grupos.insert_one({"nombre": nombre})

    return redirect("/admin")

# ---------------- ELIMINAR GRUPO ----------------
@app.route("/eliminar_grupo/<nombre>")
def eliminar_grupo(nombre):
    if session.get("rol") != "admin":
        return redirect("/")

    grupos.delete_one({"nombre": nombre})
    alumnos.update_many({"grupo": nombre}, {"$set": {"grupo": ""}})
    usuarios.update_many({"grupo": nombre}, {"$set": {"grupo": ""}})

    return redirect("/admin")

# ---------------- REGISTRAR MAESTRO ----------------
@app.route("/registrar_maestro", methods=["POST"])
def registrar_maestro():
    if session.get("rol") != "admin":
        return redirect("/")

    nombre = request.form["nombre"]
    correo = request.form["correo"]
    password = request.form["password"] or "123456"

    usuarios.insert_one({
        "nombre": nombre,
        "correo": correo,
        "password": generate_password_hash(password),
        "rol": "maestro",
        "grupo": ""
    })

    return redirect("/admin")

# ---------------- REGISTRAR ALUMNO ----------------
@app.route("/registrar_alumno", methods=["POST"])
def registrar_alumno():
    if session.get("rol") != "admin":
        return redirect("/")

    nombre = request.form["nombre"]
    correo = request.form["correo"]
    grupo = request.form["grupo"]
    password = request.form["password"] or "123456"

    user_id = usuarios.insert_one({
        "nombre": nombre,
        "correo": correo,
        "password": generate_password_hash(password),
        "rol": "alumno",
        "grupo": grupo
    }).inserted_id

    alumnos.insert_one({
        "usuario_id": user_id,
        "nombre": nombre,
        "grupo": grupo,
        "calificacion": ""
    })

    return redirect("/admin")

# ---------------- PANEL MAESTRO ----------------
@app.route("/maestro")
def maestro():
    if session.get("rol") != "maestro":
        return redirect("/")

    return safe_render("maestro.html")

# ---------------- ASISTENCIAS ----------------
@app.route("/asistencias")
def ver_asistencias():
    data = []
    for a in asistencias.find():
        data.append({
            "nombre": a.get("alumno","Desconocido"),
            "grupo": a.get("grupo","-"),
            "fecha": a.get("fecha","-"),
            "estado": a.get("estado","-")
        })
    return safe_render("asistencias_admin.html", registros=data)

# ---------------- PARTICIPACIONES ----------------
@app.route("/participaciones")
def ver_participaciones():
    data = []
    for p in participaciones.find():
        data.append({
            "nombre": p.get("alumno","Desconocido"),
            "grupo": p.get("grupo","-"),
            "fecha": p.get("fecha","-"),
            "puntos": p.get("puntos","0")
        })
    return safe_render("participaciones_admin.html", registros=data)

# ---------------- CALIFICACIONES ----------------
@app.route("/calificaciones")
def ver_calificaciones():
    lista = list(alumnos.find())
    return safe_render("calificaciones_admin.html", registros=lista)

# ---------------- REPORTES ----------------
@app.route("/reportes")
def ver_reportes():
    lista = list(reportes.find())
    return safe_render("reportes_admin.html", reportes=lista)

# ---------------- RUN LOCAL ----------------
if __name__ == "__main__":
    app.run(debug=True)
```
