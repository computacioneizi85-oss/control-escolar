from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = "control_escolar_ultra_secret_key"

# =========================
# CONEXION SEGURA A MONGODB
# =========================

MONGO_URI = os.environ.get("MONGO_URI")

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=5000
)

# NO BLOQUEAR EL ARRANQUE DEL SERVIDOR
try:
    client.admin.command('ping')
    print("✅ MongoDB conectado")
except Exception as e:
    print("⚠️ MongoDB no respondió al iniciar, pero el servidor continuará:", e)

db = client["control_escolar"]

# =========================
# LOGIN
# =========================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo")
        password = request.form.get("password")

        usuario = db.usuarios.find_one({"correo": correo, "password": password})

        if usuario:
            session["usuario"] = correo
            session["tipo"] = usuario.get("tipo")

            if usuario.get("tipo") == "admin":
                return redirect("/admin")
            elif usuario.get("tipo") == "maestro":
                return redirect("/maestro")

        return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")


# =========================
# PANEL ADMIN
# =========================

@app.route("/admin")
def admin():
    if "usuario" not in session:
        return redirect("/")

    alumnos = list(db.alumnos.find())
    maestros = list(db.maestros.find())
    grupos = list(db.grupos.find())

    return render_template(
        "admin.html",
        alumnos=alumnos,
        maestros=maestros,
        grupos=grupos
    )


# =========================
# PANEL MAESTRO
# =========================

@app.route("/maestro")
def maestro():
    if "usuario" not in session:
        return redirect("/")
    return render_template("maestro.html")


# =========================
# ASISTENCIAS
# =========================

@app.route("/asistencias")
def asistencias():
    registros = list(db.asistencias.find())
    return render_template("asistencia.html", registros=registros)


# =========================
# PARTICIPACIONES
# =========================

@app.route("/participaciones")
def participaciones():
    registros = list(db.participaciones.find())
    return render_template("participaciones.html", registros=registros)


# =========================
# CALIFICACIONES
# =========================

@app.route("/calificaciones")
def calificaciones():
    registros = list(db.calificaciones.find())
    return render_template("reporte_calificaciones.html", registros=registros)


# =========================
# REPORTES DISCIPLINARIOS
# =========================

@app.route("/reportes")
def reportes():
    registros = list(db.reportes.find())
    return render_template("reportes_admin.html", registros=registros)


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# =========================
# PARA RENDER (CRITICO)
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)