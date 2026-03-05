from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from datetime import date

app = Flask(__name__)
app.secret_key = "control_escolar_secret"

DATABASE = "escuela.db"


# ---------------------------------------------------------
# CONEXIÓN A BASE DE DATOS
# ---------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------
# CREAR BASE DE DATOS COMPLETA
# ---------------------------------------------------------

def init_db():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # ADMIN
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS administradores(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        password TEXT
    )
    """)

    # GRUPOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grupos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT
    )
    """)

    # ALUMNOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alumnos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        apellido TEXT,
        correo TEXT,
        grado TEXT,
        grupo TEXT
    )
    """)

    # MATERIAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materias(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT
    )
    """)

    # CALIFICACIONES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calificaciones(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alumno_id INTEGER,
        materia_id INTEGER,
        calificacion REAL
    )
    """)

    # ASISTENCIAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asistencias(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alumno_id INTEGER,
        fecha TEXT,
        estado TEXT
    )
    """)

    # CONFIGURACIÓN
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS configuracion(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        escuela TEXT,
        ciclo TEXT
    )
    """)

    # ADMIN POR DEFECTO
    cursor.execute("SELECT * FROM administradores WHERE usuario='admin'")
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO administradores(usuario,password) VALUES (?,?)",
            ("admin","1234")
        )

    conn.commit()
    conn.close()


init_db()


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

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
        (usuario,password)
    )

    admin = cursor.fetchone()
    conn.close()

    if admin:
        session['admin'] = usuario
        return redirect("/admin")

    return "Credenciales incorrectas"


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

@app.route('/admin')
def admin():

    if 'admin' not in session:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM alumnos")
    alumnos = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM grupos")
    grupos = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM materias")
    materias = cursor.fetchone()["total"]

    conn.close()

    return render_template(
        "admin.html",
        total_alumnos=alumnos,
        total_grupos=grupos,
        total_materias=materias
    )


# ---------------------------------------------------------
# GRUPOS
# ---------------------------------------------------------

@app.route('/grupos')
def grupos():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM grupos")
    grupos = cursor.fetchall()

    conn.close()

    return render_template("grupos.html", grupos=grupos)


@app.route('/crear_grupo', methods=['POST'])
def crear_grupo():

    nombre = request.form['nombre_grupo']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO grupos(nombre) VALUES (?)",
        (nombre,)
    )

    conn.commit()
    conn.close()

    return redirect("/grupos")


@app.route('/eliminar_grupo/<int:id>')
def eliminar_grupo(id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM grupos WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/grupos")


# ---------------------------------------------------------
# ALUMNOS
# ---------------------------------------------------------

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
    """,(nombre,apellido,correo,grado,grupo))

    conn.commit()
    conn.close()

    return redirect("/alumnos")


@app.route('/eliminar_alumno/<int:id>')
def eliminar_alumno(id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM alumnos WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/alumnos")


# ---------------------------------------------------------
# MATERIAS
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# CALIFICACIONES
# ---------------------------------------------------------

@app.route('/calificaciones')
def calificaciones():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()

    cursor.execute("SELECT * FROM materias")
    materias = cursor.fetchall()

    conn.close()

    return render_template(
        "calificaciones.html",
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

    return redirect("/calificaciones")


# ---------------------------------------------------------
# ASISTENCIAS
# ---------------------------------------------------------

@app.route('/asistencias')
def asistencias():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()

    conn.close()

    return render_template("asistencias.html", alumnos=alumnos)


@app.route('/guardar_asistencia', methods=['POST'])
def guardar_asistencia():

    alumno = request.form['alumno']
    estado = request.form['estado']
    fecha = date.today()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO asistencias(alumno_id,fecha,estado)
    VALUES (?,?,?)
    """,(alumno,fecha,estado))

    conn.commit()
    conn.close()

    return redirect("/asistencias")


# ---------------------------------------------------------
# KARDEX
# ---------------------------------------------------------

@app.route('/kardex/<int:id>')
def kardex(id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT materias.nombre, calificaciones.calificacion
    FROM calificaciones
    JOIN materias
    ON materias.id = calificaciones.materia_id
    WHERE alumno_id=?
    """,(id,))

    datos = cursor.fetchall()

    conn.close()

    return render_template("kardex.html", datos=datos)


# ---------------------------------------------------------
# REPORTES
# ---------------------------------------------------------

@app.route('/reportes')
def reportes():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()

    conn.close()

    return render_template("reportes.html", alumnos=alumnos)


# ---------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------

@app.route('/configuracion')
def configuracion():
    return render_template("configuracion.html")


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

@app.route('/logout')
def logout():

    session.clear()
    return redirect("/")


# ---------------------------------------------------------
# SERVIDOR
# ---------------------------------------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0", port=port)