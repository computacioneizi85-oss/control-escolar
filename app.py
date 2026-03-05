from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "control_escolar_secret"

DATABASE = "escuela.db"


# ---------------------------------
# CONEXIÓN A BASE DE DATOS
# ---------------------------------
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------
# INICIALIZAR BASE DE DATOS
# ---------------------------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Tabla administradores
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS administradores(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        password TEXT
    )
    """)

    # Tabla grupos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grupos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT
    )
    """)

    # Tabla alumnos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alumnos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        apellido TEXT,
        correo TEXT,
        grado TEXT,
        grupo TEXT,
        password TEXT
    )
    """)

    # Tabla asistencias
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asistencias(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alumno_id INTEGER,
        fecha TEXT,
        estado TEXT
    )
    """)

    # Crear admin por defecto si no existe
    cursor.execute("SELECT * FROM administradores WHERE usuario='admin'")
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO administradores (usuario,password) VALUES (?,?)",
            ("admin", "1234")
        )

    conn.commit()
    conn.close()


init_db()


# ---------------------------------
# LOGIN
# ---------------------------------
@app.route('/')
def index():
    return render_template("index.html")


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
        return redirect("/admin")
    else:
        return "Credenciales incorrectas"


# ---------------------------------
# DASHBOARD ADMIN
# ---------------------------------
@app.route('/admin')
def admin():

    if 'admin' not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM grupos")
    grupos = cursor.fetchall()

    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        grupos=grupos,
        alumnos=alumnos
    )


# ---------------------------------
# CREAR GRUPO
# ---------------------------------
@app.route('/crear_grupo', methods=['POST'])
def crear_grupo():

    if 'admin' not in session:
        return redirect("/")

    nombre = request.form['nombre_grupo']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO grupos (nombre) VALUES (?)",
        (nombre,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# ---------------------------------
# ELIMINAR GRUPO
# ---------------------------------
@app.route('/eliminar_grupo/<int:id>')
def eliminar_grupo(id):

    if 'admin' not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM grupos WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin")


# ---------------------------------
# CREAR ALUMNO
# ---------------------------------
@app.route('/crear_alumno', methods=['POST'])
def crear_alumno():

    if 'admin' not in session:
        return redirect("/")

    nombre = request.form['nombre']
    apellido = request.form['apellido']
    correo = request.form['correo']
    grado = request.form['grado']
    grupo = request.form['grupo']
    password = request.form['password']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO alumnos
        (nombre,apellido,correo,grado,grupo,password)
        VALUES (?,?,?,?,?,?)
    """, (nombre, apellido, correo, grado, grupo, password))

    conn.commit()
    conn.close()

    return redirect("/admin")


# ---------------------------------
# ELIMINAR ALUMNO
# ---------------------------------
@app.route('/eliminar_alumno/<int:id>')
def eliminar_alumno(id):

    if 'admin' not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM alumnos WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin")


# ---------------------------------
# CONFIGURACIÓN INSTITUCIONAL
# ---------------------------------
@app.route('/configuracion')
def configuracion():

    if 'admin' not in session:
        return redirect("/")

    return render_template("configuracion.html")


# ---------------------------------
# ASISTENCIAS
# ---------------------------------
@app.route('/asistencias')
def asistencias():

    if 'admin' not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()

    conn.close()

    return render_template("asistencias.html", alumnos=alumnos)


# ---------------------------------
# REPORTES
# ---------------------------------
@app.route('/reportes')
def reportes():

    if 'admin' not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()

    conn.close()

    return render_template("reportes.html", alumnos=alumnos)


# ---------------------------------
# LOGOUT
# ---------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")


# ---------------------------------
# SERVIDOR (RENDER)
# ---------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)