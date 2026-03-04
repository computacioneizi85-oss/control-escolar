from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import io
import os
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "control_escolar_secret"

DATABASE = "escuela.db"


# ---------------------------
# CREAR BASE DE DATOS
# ---------------------------

def init_db():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alumnos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS maestros(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS administradores(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materias(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calificaciones(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alumno_id INTEGER,
        materia_id INTEGER,
        calificacion INTEGER
    )
    """)

    # ---------------------------
    # USUARIOS POR DEFECTO
    # ---------------------------

    cursor.execute("SELECT * FROM maestros WHERE usuario='maestro'")
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO maestros (usuario,password) VALUES (?,?)",
            ("maestro","1234")
        )

    cursor.execute("SELECT * FROM administradores WHERE usuario='admin'")
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO administradores (usuario,password) VALUES (?,?)",
            ("admin","1234")
        )

    conn.commit()
    conn.close()


init_db()


# ---------------------------
# CONEXION DB
# ---------------------------

def get_db():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------
# PAGINA PRINCIPAL (LOGIN)
# ---------------------------

@app.route('/')
def index():
    return render_template("index.html")


# ---------------------------
# LOGIN ADMIN
# ---------------------------

@app.route('/login_admin', methods=['POST'])
def login_admin():

    usuario = request.form['usuario']
    password = request.form['password']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM administradores WHERE usuario=? AND password=?",
        (usuario,password)
    )

    admin = cursor.fetchone()
    conn.close()

    if admin:
        session['admin'] = usuario
        return redirect("/panel_admin")
    else:
        return "Credenciales incorrectas"


# ---------------------------
# LOGIN MAESTRO
# ---------------------------

@app.route('/login_maestro', methods=['POST'])
def login_maestro():

    usuario = request.form['usuario']
    password = request.form['password']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM maestros WHERE usuario=? AND password=?",
        (usuario,password)
    )

    maestro = cursor.fetchone()
    conn.close()

    if maestro:
        session['maestro'] = usuario
        return redirect("/panel_maestro")
    else:
        return "Credenciales incorrectas"


# ---------------------------
# PANEL ADMIN
# ---------------------------

@app.route('/panel_admin')
def panel_admin():

    if 'admin' not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()

    conn.close()

    return render_template("panel_admin.html", alumnos=alumnos)


# ---------------------------
# PANEL MAESTRO
# ---------------------------

@app.route('/panel_maestro')
def panel_maestro():

    if 'maestro' not in session:
        return redirect("/")

    try:

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM alumnos")
        alumnos = cursor.fetchall()

        conn.close()

        if alumnos is None:
            alumnos = []

        return render_template("panel_maestro.html", alumnos=alumnos)

    except Exception as e:

        return f"Error en panel maestro: {str(e)}"


# ---------------------------
# KARDEX
# ---------------------------

@app.route('/kardex/<int:alumno_id>')
def kardex(alumno_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT materias.nombre, calificaciones.calificacion
    FROM calificaciones
    JOIN materias ON calificaciones.materia_id = materias.id
    WHERE alumno_id = ?
    """, (alumno_id,))

    datos = cursor.fetchall()
    conn.close()

    return render_template("kardex.html", datos=datos)


# ---------------------------
# REPORTE PDF
# ---------------------------

@app.route('/reporte_pdf/<int:alumno_id>')
def reporte_pdf(alumno_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT materias.nombre, calificaciones.calificacion
    FROM calificaciones
    JOIN materias ON calificaciones.materia_id = materias.id
    WHERE alumno_id = ?
    """, (alumno_id,))

    datos = cursor.fetchall()
    conn.close()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.drawString(200,800,"Reporte de Calificaciones")

    y = 750

    for materia,calificacion in datos:
        texto = f"{materia}: {calificacion}"
        pdf.drawString(100,y,texto)
        y -= 30

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="reporte.pdf",
        mimetype="application/pdf"
    )


# ---------------------------
# CONFIGURACION
# ---------------------------

@app.route('/configuracion')
def configuracion():
    return render_template("configuracion.html")


# ---------------------------
# LOGOUT
# ---------------------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")


# ---------------------------
# RUN SERVER
# ---------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port)