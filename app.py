```python
from flask import Flask, render_template, request, redirect, session, send_file
from pymongo import MongoClient
import os
import hashlib
from bson.objectid import ObjectId
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "control_escolar_secret_key"

# ---------------- CONEXION REAL Y ESTABLE ----------------

MONGO_URI = os.environ.get("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["control_escolar"]

# ---------------------------------------------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ================= LOGIN =================

@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        password = hash_password(request.form['password'])

        user = db.usuarios.find_one({
            "correo": correo,
            "password": password
        })

        if user:
            session['user_id'] = str(user['_id'])
            session['tipo'] = user['tipo']

            if user['tipo'] == 'admin':
                return redirect('/admin')
            if user['tipo'] == 'maestro':
                return redirect('/maestro')
            if user['tipo'] == 'alumno':
                return redirect('/alumno')

    return render_template('login.html')

# ================= LOGOUT =================

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ================= ADMIN =================

@app.route('/admin')
def admin():
    if 'tipo' not in session or session['tipo'] != 'admin':
        return redirect('/')

    alumnos = list(db.usuarios.find({"tipo":"alumno"}))
    maestros = list(db.usuarios.find({"tipo":"maestro"}))
    grupos = list(db.grupos.find())

    return render_template("admin.html",
                           alumnos=alumnos,
                           maestros=maestros,
                           grupos=grupos)

# ================= CREAR GRUPO =================

@app.route('/crear_grupo', methods=['POST'])
def crear_grupo():
    if 'tipo' not in session:
        return redirect('/')

    nombre = request.form['nombre']

    if not db.grupos.find_one({"nombre": nombre}):
        db.grupos.insert_one({"nombre": nombre})

    return redirect('/admin')

# ================= ASIGNAR GRUPO A MAESTRO =================

@app.route('/asignar_grupo', methods=['POST'])
def asignar_grupo():
    maestro_id = request.form['maestro']
    grupo = request.form['grupo']

    db.usuarios.update_one(
        {"_id": ObjectId(maestro_id)},
        {"$set":{"grupo": grupo}}
    )

    return redirect('/admin')

# ================= REGISTRAR ALUMNO =================

@app.route('/registrar_alumno', methods=['POST'])
def registrar_alumno():
    nombre = request.form['nombre']
    correo = request.form['correo']
    grupo = request.form['grupo']
    password = request.form['password']

    if password == "":
        password = "123456"

    db.usuarios.insert_one({
        "nombre": nombre,
        "correo": correo,
        "grupo": grupo,
        "tipo":"alumno",
        "password": hash_password(password)
    })

    return redirect('/admin')

# ================= REGISTRAR MAESTRO =================

@app.route('/registrar_maestro', methods=['POST'])
def registrar_maestro():
    nombre = request.form['nombre']
    correo = request.form['correo']
    grupo = request.form['grupo']
    password = request.form['password']

    if password == "":
        password = "123456"

    db.usuarios.insert_one({
        "nombre": nombre,
        "correo": correo,
        "grupo": grupo,
        "tipo":"maestro",
        "password": hash_password(password)
    })

    return redirect('/admin')

# ================= ASISTENCIAS =================

@app.route('/asistencias')
def asistencias():
    if 'tipo' not in session:
        return redirect('/')

    registros = list(db.asistencias.find())

    for r in registros:
        alumno = db.usuarios.find_one({"_id":ObjectId(r['alumno_id'])})
        if alumno:
            r['nombre'] = alumno['nombre']
            r['grupo'] = alumno.get('grupo','')

    return render_template("asistencias.html", registros=registros)

# ================= PARTICIPACIONES =================

@app.route('/participaciones')
def participaciones():
    registros = list(db.participaciones.find())

    for r in registros:
        alumno = db.usuarios.find_one({"_id":ObjectId(r['alumno_id'])})
        if alumno:
            r['nombre'] = alumno['nombre']
            r['grupo'] = alumno.get('grupo','')

    return render_template("participaciones.html", registros=registros)

# ================= CALIFICACIONES =================

@app.route('/calificaciones')
def calificaciones():
    registros = list(db.calificaciones.find())

    for r in registros:
        alumno = db.usuarios.find_one({"_id":ObjectId(r['alumno_id'])})
        if alumno:
            r['nombre'] = alumno['nombre']
            r['grupo'] = alumno.get('grupo','')

    return render_template("calificaciones.html", registros=registros)

# ================= REPORTES DISCIPLINARIOS =================

@app.route('/reportes')
def reportes():
    registros = list(db.reportes.find())

    for r in registros:
        alumno = db.usuarios.find_one({"_id":ObjectId(r['alumno_id'])})
        if alumno:
            r['nombre'] = alumno['nombre']
            r['grupo'] = alumno.get('grupo','')

    return render_template("reportes_admin.html", registros=registros)

# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)
```
