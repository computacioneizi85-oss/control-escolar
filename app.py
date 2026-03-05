from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "control_escolar"

DATABASE = "/var/data/database.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
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
    CREATE TABLE IF NOT EXISTS grupos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT
    )
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO usuarios(id,usuario,password,rol)
    VALUES(1,'admin','1234','admin')
    """)

    conn.commit()
    conn.close()


init_db()

# =========================
# LOGIN
# =========================

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


# =========================
# PANEL ADMIN
# =========================

@app.route('/admin')
def admin():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()

    cursor.execute("SELECT * FROM grupos")
    grupos = cursor.fetchall()

    conn.close()

    return render_template("admin.html",
                           alumnos=alumnos,
                           grupos=grupos)


# =========================
# CREAR ALUMNO
# =========================

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
    VALUES(?,?,?,?)
    """,(nombre,apellido,correo,grupo))

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# CREAR GRUPO
# =========================

@app.route('/crear_grupo', methods=['POST'])
def crear_grupo():

    nombre = request.form['nombre']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO grupos(nombre) VALUES(?)",(nombre,))

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# CREAR MAESTRO
# =========================

@app.route('/crear_maestro', methods=['POST'])
def crear_maestro():

    usuario = request.form['usuario']
    password = request.form['password']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO usuarios(usuario,password,rol)
    VALUES(?,?,?)
    """,(usuario,password,"maestro"))

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# PANEL MAESTRO
# =========================

@app.route('/panel_maestro')
def panel_maestro():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alumnos")
    alumnos = cursor.fetchall()

    conn.close()

    return render_template("panel_maestro.html",
                           alumnos=alumnos)


# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")


# =========================
# RUN
# =========================

if __name__ == "__main__":

    port = int(os.environ.get("PORT",10000))

    app.run(
        host="0.0.0.0",
        port=port
    )