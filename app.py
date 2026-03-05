from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import os
import io
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "control_escolar_secret"

DATABASE = "database.db"


# =============================
# CONEXION DB
# =============================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =============================
# CREAR BASE DE DATOS
# =============================

def init_db():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        password TEXT,
        rol TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alumnos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        apellido TEXT,
        correo TEXT,
        grupo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS maestros(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        correo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grupos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materias(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grupo_materias(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grupo TEXT,
        materia_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calificaciones(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alumno_id INTEGER,
        materia_id INTEGER,
        calificacion REAL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reportes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alumno_id INTEGER,
        descripcion TEXT,
        aprobado INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO usuarios(id,usuario,password,rol)
    VALUES (1,'admin','1234','admin')
    """)

    conn.commit()
    conn.close()


init_db()


# =============================
# LOGIN
# =============================

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=['POST'])
def login():

    usuario = request.form['usuario']
    password = request.form['password']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM usuarios
    WHERE usuario=? AND password=?
    """,(usuario,password))

    user = cursor.fetchone()
    conn.close()

    if user:

        session['usuario'] = usuario
        session['rol'] = user["rol"]

        if user["rol"] == "admin":
            return redirect("/admin")

        if user["rol"] == "maestro":
            return redirect("/panel_maestro")

    return "Credenciales incorrectas"


# =============================
# PANEL ADMIN
# =============================

@app.route('/admin')
def admin():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()

    cursor.execute("SELECT * FROM grupos")
    grupos = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        alumnos=alumnos,
        grupos=grupos
    )


# =============================
# REGISTRAR ALUMNO
# =============================

@app.route('/crear_alumno', methods=['POST'])
def crear_alumno():

    nombre = request.form['nombre']
    apellido = request.form['apellido']
    correo = request.form['correo']
    grupo = request.form['grupo']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO alumnos(nombre,apellido,correo,grupo)
    VALUES (?,?,?,?)
    """,(nombre,apellido,correo,grupo))

    conn.commit()
    conn.close()

    return redirect("/admin")


# =============================
# GRUPOS
# =============================

@app.route('/grupos')
def grupos():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM grupos")
    grupos = cursor.fetchall()

    conn.close()

    return render_template("grupos.html",grupos=grupos)


@app.route('/crear_grupo', methods=['POST'])
def crear_grupo():

    nombre = request.form['nombre']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO grupos(nombre) VALUES (?)",(nombre,))

    conn.commit()
    conn.close()

    return redirect("/grupos")


# =============================
# MATERIAS
# =============================

@app.route('/materias')
def materias():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM materias")
    materias = cursor.fetchall()

    conn.close()

    return render_template("materias.html",materias=materias)


@app.route('/crear_materia', methods=['POST'])
def crear_materia():

    nombre = request.form['nombre']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO materias(nombre) VALUES (?)",(nombre,))

    conn.commit()
    conn.close()

    return redirect("/materias")


# =============================
# CAPTURAR CALIFICACIONES
# =============================

@app.route('/capturar_calificaciones')
def capturar_calificaciones():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()

    cursor.execute("SELECT * FROM materias")
    materias = cursor.fetchall()

    conn.close()

    return render_template(
        "capturar_calificaciones.html",
        alumnos=alumnos,
        materias=materias
    )


@app.route('/guardar_calificacion', methods=['POST'])
def guardar_calificacion():

    alumno = request.form['alumno']
    materia = request.form['materia']
    calificacion = request.form['calificacion']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO calificaciones(alumno_id,materia_id,calificacion)
    VALUES (?,?,?)
    """,(alumno,materia,calificacion))

    conn.commit()
    conn.close()

    return redirect("/capturar_calificaciones")


# =============================
# KARDEX
# =============================

@app.route('/kardex/<int:id>')
def kardex(id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT materias.nombre, calificaciones.calificacion
    FROM calificaciones
    JOIN materias ON materias.id = calificaciones.materia_id
    WHERE alumno_id=?
    """,(id,))

    datos = cursor.fetchall()

    conn.close()

    return render_template("kardex.html",datos=datos)


# =============================
# BOLETA PDF
# =============================

@app.route('/boleta_pdf/<int:id>')
def boleta_pdf(id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT materias.nombre, calificaciones.calificacion
    FROM calificaciones
    JOIN materias ON materias.id = calificaciones.materia_id
    WHERE alumno_id=?
    """,(id,))

    datos = cursor.fetchall()

    promedio = 0
    total = 0

    for d in datos:
        promedio += d["calificacion"]
        total += 1

    if total > 0:
        promedio = promedio / total

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)

    y = 800

    pdf.drawString(200,820,"BOLETA ESCOLAR")

    for d in datos:

        texto = f"{d['nombre']} : {d['calificacion']}"
        pdf.drawString(100,y,texto)

        y -= 25

    pdf.drawString(100,y-20,f"Promedio final: {round(promedio,2)}")

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="boleta.pdf",
        mimetype='application/pdf'
    )


# =============================
# PANEL MAESTRO
# =============================

@app.route('/panel_maestro')
def panel_maestro():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()

    conn.close()

    return render_template(
        "panel_maestro.html",
        alumnos=alumnos
    )


# =============================
# LOGOUT
# =============================

@app.route('/logout')
def logout():

    session.clear()
    return redirect("/")


# =============================
# RUN SERVER
# =============================

if __name__ == "__main__":

    port = int(os.environ.get("PORT",10000))

    app.run(
        host="0.0.0.0",
        port=port
    )