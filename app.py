```python
from flask import Flask, render_template, request, redirect, session, g, send_file, abort
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import hashlib
from datetime import datetime

# --------------------------------------------------
# CONFIGURACION APP
# --------------------------------------------------

app = Flask(__name__)
app.secret_key = "control_escolar_secret_key_2026"


# --------------------------------------------------
# CONEXION MONGODB (ESTABLE PARA RENDER)
# --------------------------------------------------

def get_db():
    if "mongo_db" not in g:
        mongo_uri = os.environ.get("MONGO_URI")

        if not mongo_uri:
            raise Exception("MONGO_URI no configurada en Render")

        client = MongoClient(mongo_uri)
        g.mongo_client = client
        g.mongo_db = client["control_escolar"]

    return g.mongo_db


@app.teardown_appcontext
def close_db(e=None):
    client = g.pop("mongo_client", None)
    if client:
        client.close()


def db():
    return get_db()


# --------------------------------------------------
# HASH PASSWORD
# --------------------------------------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        correo = request.form["correo"]
        password = hash_password(request.form["password"])

        user = db().usuarios.find_one({
            "correo": correo,
            "password": password
        })

        if user:
            session["user_id"] = str(user["_id"])
            session["tipo"] = user["tipo"]

            if user["tipo"] == "admin":
                return redirect("/admin")
            elif user["tipo"] == "maestro":
                return redirect("/maestro")
            else:
                return redirect("/alumno")

    return render_template("login.html")


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# --------------------------------------------------
# PANEL ADMIN
# --------------------------------------------------

@app.route("/admin")
def admin():
    if session.get("tipo") != "admin":
        return redirect("/")

    alumnos = list(db().usuarios.find({"tipo": "alumno"}))
    maestros = list(db().usuarios.find({"tipo": "maestro"}))
    grupos = list(db().grupos.find())

    return render_template("admin.html",
                           alumnos=alumnos,
                           maestros=maestros,
                           grupos=grupos)


# --------------------------------------------------
# CREAR GRUPO
# --------------------------------------------------

@app.route("/crear_grupo", methods=["POST"])
def crear_grupo():
    if session.get("tipo") != "admin":
        return redirect("/")

    nombre = request.form["nombre"]

    if not db().grupos.find_one({"nombre": nombre}):
        db().grupos.insert_one({"nombre": nombre})

    return redirect("/admin")


# --------------------------------------------------
# ELIMINAR GRUPO
# --------------------------------------------------

@app.route("/eliminar_grupo/<nombre>")
def eliminar_grupo(nombre):
    if session.get("tipo") != "admin":
        return redirect("/")

    db().grupos.delete_one({"nombre": nombre})

    db().usuarios.update_many(
        {"grupo": nombre},
        {"$set": {"grupo": ""}}
    )

    return redirect("/admin")


# --------------------------------------------------
# REGISTRAR ALUMNO
# --------------------------------------------------

@app.route("/registrar_alumno", methods=["POST"])
def registrar_alumno():
    if session.get("tipo") != "admin":
        return redirect("/")

    nombre = request.form["nombre"]
    correo = request.form["correo"]
    grupo = request.form["grupo"]
    password = request.form["password"] or "123456"

    db().usuarios.insert_one({
        "nombre": nombre,
        "correo": correo,
        "grupo": grupo,
        "tipo": "alumno",
        "password": hash_password(password)
    })

    return redirect("/admin")


# --------------------------------------------------
# REGISTRAR MAESTRO
# --------------------------------------------------

@app.route("/registrar_maestro", methods=["POST"])
def registrar_maestro():
    if session.get("tipo") != "admin":
        return redirect("/")

    nombre = request.form["nombre"]
    correo = request.form["correo"]
    grupo = request.form["grupo"]
    password = request.form["password"] or "123456"

    db().usuarios.insert_one({
        "nombre": nombre,
        "correo": correo,
        "grupo": grupo,
        "tipo": "maestro",
        "password": hash_password(password)
    })

    return redirect("/admin")


# --------------------------------------------------
# ASIGNAR MAESTRO A GRUPO
# --------------------------------------------------

@app.route("/asignar_grupo", methods=["POST"])
def asignar_grupo():
    if session.get("tipo") != "admin":
        return redirect("/")

    maestro_id = request.form["maestro"]
    grupo = request.form["grupo"]

    db().usuarios.update_one(
        {"_id": ObjectId(maestro_id)},
        {"$set": {"grupo": grupo}}
    )

    return redirect("/admin")


# --------------------------------------------------
# ASISTENCIAS
# --------------------------------------------------

@app.route("/asistencias")
def asistencias():
    if "tipo" not in session:
        return redirect("/")

    registros = list(db().asistencias.find())

    for r in registros:
        alumno = db().usuarios.find_one({"_id": ObjectId(r["alumno_id"])})
        if alumno:
            r["nombre"] = alumno["nombre"]
            r["grupo"] = alumno.get("grupo", "")
        else:
            r["nombre"] = "Alumno eliminado"

    return render_template("asistencias.html", registros=registros)


# --------------------------------------------------
# PARTICIPACIONES
# --------------------------------------------------

@app.route("/participaciones")
def participaciones():
    if "tipo" not in session:
        return redirect("/")

    registros = list(db().participaciones.find())

    for r in registros:
        alumno = db().usuarios.find_one({"_id": ObjectId(r["alumno_id"])})
        if alumno:
            r["nombre"] = alumno["nombre"]
            r["grupo"] = alumno.get("grupo", "")
        else:
            r["nombre"] = "Alumno eliminado"

    return render_template("participaciones.html", registros=registros)


# --------------------------------------------------
# CALIFICACIONES
# --------------------------------------------------

@app.route("/calificaciones")
def calificaciones():
    if "tipo" not in session:
        return redirect("/")

    registros = list(db().calificaciones.find())

    for r in registros:
        alumno = db().usuarios.find_one({"_id": ObjectId(r["alumno_id"])})
        if alumno:
            r["nombre"] = alumno["nombre"]
            r["grupo"] = alumno.get("grupo", "")
        else:
            r["nombre"] = "Alumno eliminado"

    return render_template("calificaciones.html", registros=registros)


# --------------------------------------------------
# KARDEX PDF (LAZY REPORTLAB)
# --------------------------------------------------

@app.route("/kardex/<alumno_id>")
def kardex(alumno_id):

    if session.get("tipo") != "admin":
        return redirect("/")

    alumno = db().usuarios.find_one({"_id": ObjectId(alumno_id)})
    if not alumno:
        abort(404)

    # IMPORTACION DIFERIDA (NO ROMPE RENDER)
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    filename = f"kardex_{alumno['nombre']}.pdf"

    c = canvas.Canvas(filename, pagesize=letter)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(180, 750, "KARDEX ESCOLAR")

    c.setFont("Helvetica", 12)
    c.drawString(100, 700, f"Nombre: {alumno['nombre']}")
    c.drawString(100, 680, f"Correo: {alumno['correo']}")
    c.drawString(100, 660, f"Grupo: {alumno.get('grupo','')}")

    c.drawString(100, 620, "Firma del padre o tutor: _________________________")

    c.save()

    return send_file(filename, as_attachment=True)


# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
```
