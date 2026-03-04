from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
import io
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "control_escolar_secret"


# -------------------------------
# CONEXION BASE DE DATOS
# -------------------------------

def get_db():
    conn = sqlite3.connect("escuela.db")
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------------
# INICIO
# -------------------------------

@app.route('/')
def index():
    return render_template("index.html")


# -------------------------------
# LOGIN ADMIN
# -------------------------------

@app.route('/login_admin', methods=['POST'])
def login_admin():

    usuario = request.form['usuario']
    password = request.form['password']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM administradores WHERE usuario=? AND password=?",
        (usuario, password)
    )

    admin = cursor.fetchone()
    conn.close()

    if admin:
        session['admin'] = usuario
        return redirect(url_for('panel_admin'))
    else:
        return "Credenciales incorrectas"


# -------------------------------
# LOGIN MAESTRO
# -------------------------------

@app.route('/login_maestro', methods=['POST'])
def login_maestro():

    usuario = request.form['usuario']
    password = request.form['password']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM maestros WHERE usuario=? AND password=?",
        (usuario, password)
    )

    maestro = cursor.fetchone()
    conn.close()

    if maestro:
        session['maestro'] = usuario
        return redirect(url_for('panel_maestro'))
    else:
        return "Credenciales incorrectas"


# -------------------------------
# PANEL ADMIN
# -------------------------------

@app.route('/panel_admin')
def panel_admin():

    if 'admin' not in session:
        return redirect(url_for('index'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()

    conn.close()

    return render_template("panel_admin.html", alumnos=alumnos)


# -------------------------------
# PANEL MAESTRO
# -------------------------------

@app.route('/panel_maestro')
def panel_maestro():

    if 'maestro' not in session:
        return redirect(url_for('index'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()

    conn.close()

    return render_template("panel_maestro.html", alumnos=alumnos)


# -------------------------------
# KARDEX ALUMNO
# -------------------------------

@app.route('/kardex/<int:alumno_id>')
def kardex(alumno_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT materias.nombre, calificaciones.calificacion
    FROM calificaciones
    JOIN materias ON calificaciones.materia_id = materias.id
    WHERE calificaciones.alumno_id = ?
    """, (alumno_id,))

    datos = cursor.fetchall()
    conn.close()

    return render_template("kardex.html", datos=datos)


# -------------------------------
# REPORTE PDF
# -------------------------------

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
    p = canvas.Canvas(buffer)

    p.drawString(200, 800, "REPORTE DE CALIFICACIONES")

    y = 750

    for materia, calificacion in datos:
        texto = f"{materia} : {calificacion}"
        p.drawString(100, y, texto)
        y -= 30

    p.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="reporte_calificaciones.pdf",
        mimetype="application/pdf"
    )


# -------------------------------
# CONFIGURACION INSTITUCIONAL
# -------------------------------

@app.route('/configuracion')
def configuracion():

    if 'admin' not in session:
        return redirect(url_for('index'))

    return render_template("configuracion.html")


# -------------------------------
# CERRAR SESION
# -------------------------------

@app.route('/logout')
def logout():

    session.clear()
    return redirect(url_for('index'))


# -------------------------------
# RUN APP
# -------------------------------

if __name__ == "__main__":
    app.run(debug=True)