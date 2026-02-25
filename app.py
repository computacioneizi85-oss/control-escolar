```python
from flask import Flask, render_template, request, redirect, session, flash, g
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2 import TemplateNotFound
import os

app = Flask(__name__)
app.secret_key = "CONTROL_ESCOLAR_2026_RENDER"

# =========================================================
# CONEXION A MONGODB (ESTABLE PARA RENDER)
# =========================================================

def get_db():
    if "mongo_db" not in g:
        mongo_uri = os.environ.get("MONGO_URI")
        client = MongoClient(mongo_uri)
        g.mongo_client = client
        g.mongo_db = client["control_escolar"]
    return g.mongo_db

@app.teardown_appcontext
def close_db(error=None):
    client = g.pop("mongo_client", None)
    if client:
        client.close()

def usuarios(): return get_db().usuarios
def alumnos(): return get_db().alumnos
def grupos(): return get_db().grupos
def asistencias(): return get_db().asistencias
def participaciones(): return get_db().participaciones
def calificaciones(): return get_db().calificaciones
def reportes(): return get_db().reportes

# =========================================================
# SAFE RENDER (SI FALTA HTML NO TIRA EL SERVIDOR)
# =========================================================

def safe_render(template, **context):
    try:
        return render_template(template, **context)
    except TemplateNotFound:
        return f"<h2 style='color:red'>No existe el archivo: {template}</h2>"

# =========================================================
# LOGIN
# =========================================================

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        password = request.form["password"]

        user = usuarios().find_one({" hookup 
```
