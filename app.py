from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import os
from datetime import date
import io
import pandas as pd
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "control_escolar_secret"

DATABASE = os.path.join(os.getcwd(), "escuela.db")


# -----------------------------------
# CONEXIÓN A BASE DE DATOS
# -----------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------------
# CREAR BASE DE DATOS
# -----------------------------------

def init_db():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    password TEXT,
    rol TEXT)
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alumnos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    apellido TEXT,
    correo TEXT,
    grado TEXT,
    grupo TEXT)
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS maestros(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    correo TEXT)
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grupos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT)
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materias(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT)
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calificaciones(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_id INTEGER,
    materia_id INTEGER,
    calificacion REAL)
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asistencias(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumno_id INTEGER,
    fecha TEXT,
    estado TEXT)
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reportes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    maestro TEXT,
    alumno TEXT,
    descripcion TEXT,
    estado TEXT)
    """)

    cursor.execute("SELECT * FROM usuarios WHERE usuario='admin'")
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO usuarios(usuario,password,rol) VALUES (?,?,?)",
            ("admin","1234","admin")
        )

    conn.commit()
    conn.close()


init_db()


# -----------------------------------
# LOGIN
# -----------------------------------

@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=['POST'])
def login():

    usuario = request.form['usuario']
    password = request.form['password']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM usuarios WHERE usuario=? AND password=?",
        (usuario, password)
    )

    user = cursor.fetchone()
    conn.close()

    if user:

        session['usuario'] = usuario
        session['rol'] = user['rol']

        if user['rol'] == 'maestro':
            return redirect("/panel_maestro")

        return redirect("/admin")

    return "Credenciales incorrectas"


# -----------------------------------
# DASHBOARD ADMIN
# -----------------------------------

@app.route('/admin')
def admin():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM alumnos")
    alumnos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM maestros")
    maestros = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM grupos")
    grupos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reportes WHERE estado='pendiente'")
    reportes = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        total_alumnos=alumnos,
        total_maestros=maestros,
        total_grupos=grupos,
        total_reportes=reportes
    )


# -----------------------------------
# ALUMNOS
# -----------------------------------

@app.route('/alumnos')
def alumnos():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()

    cursor.execute("SELECT * FROM grupos")
    grupos = cursor.fetchall()

    conn.close()

    return render_template("alumnos.html", alumnos=alumnos, grupos=grupos)


@app.route('/crear_alumno', methods=['POST'])
def crear_alumno():

    nombre = request.form['nombre']
    apellido = request.form['apellido']
    correo = request.form['correo']
    grado = request.form['grado']
    grupo = request.form['grupo']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO alumnos(nombre,apellido,correo,grado,grupo)
    VALUES (?,?,?,?,?)
    """, (nombre, apellido, correo, grado, grupo))

    conn.commit()
    conn.close()

    return redirect("/alumnos")


# -----------------------------------
# IMPORTAR ALUMNOS EXCEL
# -----------------------------------

@app.route('/importar_alumnos', methods=['POST'])
def importar_alumnos():

    archivo = request.files['archivo']
    df = pd.read_excel(archivo)

    conn = get_db()
    cursor = conn.cursor()

    for _, row in df.iterrows():

        cursor.execute("""
        INSERT INTO alumnos(nombre,apellido,correo,grado,grupo)
        VALUES (?,?,?,?,?)
        """,(
            row['nombre'],
            row['apellido'],
            row['correo'],
            row['grado'],
            row['grupo']
        ))

    conn.commit()
    conn.close()

    return redirect("/alumnos")


# -----------------------------------
# MAESTROS
# -----------------------------------

@app.route('/maestros')
def maestros():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM maestros")
    maestros = cursor.fetchall()

    conn.close()

    return render_template("maestros.html", maestros=maestros)


@app.route('/crear_maestro', methods=['POST'])
def crear_maestro():

    nombre = request.form['nombre']
    correo = request.form['correo']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO maestros(nombre,correo)
    VALUES (?,?)
    """,(nombre,correo))

    conn.commit()
    conn.close()

    return redirect("/maestros")


# -----------------------------------
# MATERIAS
# -----------------------------------

@app.route('/materias')
def materias():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM materias")
    materias = cursor.fetchall()

    conn.close()

    return render_template("materias.html", materias=materias)


@app.route('/crear_materia', methods=['POST'])
def crear_materia():

    nombre = request.form['nombre']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO materias(nombre) VALUES (?)",
        (nombre,)
    )

    conn.commit()
    conn.close()

    return redirect("/materias")


# -----------------------------------
# CALIFICACIONES
# -----------------------------------

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

    return redirect("/admin")


# -----------------------------------
# KARDEX
# -----------------------------------

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

    return render_template("kardex.html", datos=datos)


# -----------------------------------
# BOLETA PDF
# -----------------------------------

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

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)

    y = 800
    pdf.drawString(200,820,"Boleta Escolar")

    for d in datos:
        pdf.drawString(100,y,f"{d['nombre']} : {d['calificacion']}")
        y -= 30

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="boleta.pdf",
        mimetype='application/pdf'
    )


# -----------------------------------
# REPORTES DISCIPLINARIOS
# -----------------------------------

@app.route('/reportes')
def reportes():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reportes")
    reportes = cursor.fetchall()

    conn.close()

    return render_template("reportes.html", reportes=reportes)


@app.route('/crear_reporte', methods=['POST'])
def crear_reporte():

    maestro = request.form['maestro']
    alumno = request.form['alumno']
    descripcion = request.form['descripcion']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO reportes(maestro,alumno,descripcion,estado)
    VALUES (?,?,?,'pendiente')
    """,(maestro,alumno,descripcion))

    conn.commit()
    conn.close()

    return redirect("/reportes")


@app.route('/aprobar_reporte/<int:id>')
def aprobar_reporte(id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE reportes
    SET estado='aprobado'
    WHERE id=?
    """,(id,))

    conn.commit()
    conn.close()

    return redirect("/reportes")


# -----------------------------------
# REPORTE PDF
# -----------------------------------

@app.route('/reporte_pdf/<int:id>')
def reporte_pdf(id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reportes WHERE id=?", (id,))
    reporte = cursor.fetchone()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.drawString(200,800,"Reporte Disciplinario")

    pdf.drawString(100,760,"Maestro: "+reporte['maestro'])
    pdf.drawString(100,730,"Alumno: "+reporte['alumno'])
    pdf.drawString(100,700,"Descripcion: "+reporte['descripcion'])

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="reporte.pdf",
        mimetype='application/pdf'
    )


# -----------------------------------
# PANEL MAESTRO
# -----------------------------------

@app.route('/panel_maestro')
def panel_maestro():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reportes")
    reportes = cursor.fetchall()

    conn.close()

    return render_template("panel_maestro.html", reportes=reportes)


# -----------------------------------
# LOGOUT
# -----------------------------------

@app.route('/logout')
def logout():

    session.clear()

    return redirect("/")


# -----------------------------------
# RUN SERVER
# -----------------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT",10000))

    app.run(host="0.0.0.0", port=port)