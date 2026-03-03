from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os
import random
import string

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

app = Flask(__name__)
app.secret_key = "control_escolar_secret_key"

# ===============================
# CONEXIÓN A MONGO
# ===============================
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise Exception("MONGO_URI no configurado en Render")

client = MongoClient(MONGO_URI)
db = client["control_escolar"]

# ===============================
# UTILIDADES
# ===============================
def generar_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# ===============================
# LOGIN DIRECCIÓN
# ===============================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["usuario"] == "direccion" and request.form["password"] == "1234":
            session.clear()
            session["direccion"] = True
            return redirect("/admin")
        return render_template("login.html", error="Credenciales incorrectas")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ===============================
# PANEL DIRECCIÓN
# ===============================
@app.route("/admin")
def admin():
    if "direccion" not in session:
        return redirect("/")

    alumnos = list(db.alumnos.find())
    maestros = list(db.maestros.find())
    grupos = list(db.grupos.find())
    mensaje_password = session.pop("nueva_password", None)

    return render_template(
        "admin.html",
        alumnos=alumnos,
        maestros=maestros,
        grupos=grupos,
        nueva_password=mensaje_password
    )

# ===============================
# ALUMNOS
# ===============================
@app.route("/registrar_alumno", methods=["POST"])
def registrar_alumno():
    password = request.form.get("password") or generar_password()

    db.alumnos.insert_one({
        "nombre": request.form["nombre"],
        "apellido": request.form["apellido"],
        "correo": request.form["correo"],
        "grado": request.form["grado"],
        "grupo": request.form["grupo"],
        "password": password
    })

    session["nueva_password"] = f"Contraseña del alumno: {password}"
    return redirect("/admin")

@app.route("/eliminar_alumno/<id>")
def eliminar_alumno(id):
    db.alumnos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

@app.route("/reset_password_alumno/<id>")
def reset_password_alumno(id):
    nueva = generar_password()
    db.alumnos.update_one({"_id": ObjectId(id)}, {"$set": {"password": nueva}})
    session["nueva_password"] = f"Nueva contraseña del alumno: {nueva}"
    return redirect("/admin")

# ===============================
# MAESTROS
# ===============================
@app.route("/registrar_maestro", methods=["POST"])
def registrar_maestro():
    password = request.form.get("password") or generar_password()

    db.maestros.insert_one({
        "nombre": request.form["nombre"],
        "correo": request.form["correo"],
        "materia": request.form["materia"],
        "grupo": request.form["grupo"],
        "password": password
    })

    session["nueva_password"] = f"Contraseña del maestro: {password}"
    return redirect("/admin")

@app.route("/eliminar_maestro/<id>")
def eliminar_maestro(id):
    db.maestros.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

@app.route("/reset_password_maestro/<id>")
def reset_password_maestro(id):
    nueva = generar_password()
    db.maestros.update_one({"_id": ObjectId(id)}, {"$set": {"password": nueva}})
    session["nueva_password"] = f"Nueva contraseña del maestro: {nueva}"
    return redirect("/admin")

# ===============================
# GRUPOS
# ===============================
@app.route("/crear_grupo", methods=["POST"])
def crear_grupo():
    nombre = request.form.get("nombre_grupo")
    if not db.grupos.find_one({"nombre": nombre}):
        db.grupos.insert_one({"nombre": nombre})
    return redirect("/admin")

@app.route("/eliminar_grupo/<id>")
def eliminar_grupo(id):
    db.grupos.delete_one({"_id": ObjectId(id)})
    return redirect("/admin")

# ===============================
# LOGIN MAESTRO
# ===============================
@app.route("/login_maestro", methods=["GET", "POST"])
def login_maestro():
    if request.method == "POST":
        correo = request.form.get("correo")
        password = request.form.get("password")

        maestro = db.maestros.find_one({
            "correo": correo,
            "password": password
        })

        if maestro:
            session.clear()
            session["maestro_id"] = str(maestro["_id"])
            return redirect("/panel_maestro")

        return render_template("login_maestro.html", error="Credenciales incorrectas")

    return render_template("login_maestro.html")

@app.route("/logout_maestro")
def logout_maestro():
    session.clear()
    return redirect("/login_maestro")

# ===============================
# PANEL MAESTRO
# ===============================
@app.route("/panel_maestro")
def panel_maestro():
    maestro = db.maestros.find_one({"_id": ObjectId(session["maestro_id"])})
    alumnos = list(db.alumnos.find({"grupo": maestro.get("grupo")}))
    return render_template("panel_maestro.html", maestro=maestro, alumnos=alumnos)

# ===============================
# ASISTENCIAS
# ===============================
@app.route("/guardar_asistencia", methods=["POST"])
def guardar_asistencia():
    maestro = db.maestros.find_one({"_id": ObjectId(session["maestro_id"])})
    fecha = datetime.now().strftime("%Y-%m-%d")

    for key in request.form:
        if key.startswith("alumno_"):
            alumno_id = key.replace("alumno_", "")
            estado = request.form.get(key)
            alumno = db.alumnos.find_one({"_id": ObjectId(alumno_id)})

            db.asistencias.insert_one({
                "alumno_id": alumno_id,
                "nombre_alumno": alumno["nombre"] + " " + alumno["apellido"],
                "grupo": maestro["grupo"],
                "fecha": fecha,
                "estado": estado,
                "maestro_id": session["maestro_id"]
            })

    return redirect("/panel_maestro")

@app.route("/asistencias_admin")
def asistencias_admin():
    asistencias = list(db.asistencias.find())
    grupos = list(db.grupos.find())
    return render_template("asistencias_admin.html", asistencias=asistencias, grupos=grupos)

# ===============================
# REPORTES DISCIPLINARIOS
# ===============================
@app.route("/crear_reporte", methods=["POST"])
def crear_reporte():
    maestro = db.maestros.find_one({"_id": ObjectId(session["maestro_id"])})
    alumno_id = request.form["alumno_id"]
    alumno = db.alumnos.find_one({"_id": ObjectId(alumno_id)})

    db.reportes.insert_one({
        "alumno_id": alumno_id,
        "nombre_alumno": alumno["nombre"] + " " + alumno["apellido"],
        "grupo": maestro["grupo"],
        "maestro_id": session["maestro_id"],
        "motivo": request.form["motivo"],
        "consecuencia": request.form["consecuencia"],
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "estado": "Pendiente"
    })

    return redirect("/panel_maestro")

@app.route("/reportes_admin")
def reportes_admin():
    reportes = list(db.reportes.find())
    return render_template("reportes_admin.html", reportes=reportes)

@app.route("/autorizar_reporte/<id>")
def autorizar_reporte(id):
    reporte = db.reportes.find_one({"_id": ObjectId(id)})
    db.reportes.update_one({"_id": ObjectId(id)}, {"$set": {"estado": "Aprobado"}})
    generar_pdf_reporte(reporte)
    return redirect("/reportes_admin")

# ===============================
# PDF REPORTE
# ===============================
def generar_pdf_reporte(reporte):
    if not os.path.exists("static"):
        os.makedirs("static")

    ruta = f"static/reporte_{reporte['_id']}.pdf"
    doc = SimpleDocTemplate(ruta, pagesize=A4)
    elementos = []
    styles = getSampleStyleSheet()

    elementos.append(Paragraph("<b>REPORTE DISCIPLINARIO</b>", styles["Title"]))
    elementos.append(Spacer(1, 20))

    datos = [
        ["Alumno:", reporte["nombre_alumno"]],
        ["Grupo:", reporte["grupo"]],
        ["Fecha:", reporte["fecha"]],
        ["Motivo:", reporte["motivo"]],
        ["Consecuencia:", reporte["consecuencia"]],
    ]

    tabla = Table(datos)
    tabla.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.grey)]))

    elementos.append(tabla)
    elementos.append(Spacer(1, 50))
    elementos.append(Paragraph("Firma del Padre o Tutor: ____________________________", styles["Normal"]))

    doc.build(elementos)

# ===============================
# KARDEX COMPLETO
# ===============================
@app.route("/kardex/<id>")
def generar_kardex(id):

    alumno = db.alumnos.find_one({"_id": ObjectId(id)})
    asistencias = list(db.asistencias.find({"alumno_id": id}))
    reportes = list(db.reportes.find({"alumno_id": id, "estado": "Aprobado"}))

    if not os.path.exists("static"):
        os.makedirs("static")

    ruta = f"static/kardex_{id}.pdf"
    doc = SimpleDocTemplate(ruta, pagesize=A4)
    elementos = []
    styles = getSampleStyleSheet()

    elementos.append(Paragraph("<b>KARDEX ACADÉMICO</b>", styles["Title"]))
    elementos.append(Spacer(1, 20))

    datos_generales = [
        ["Nombre:", alumno["nombre"] + " " + alumno["apellido"]],
        ["Correo:", alumno["correo"]],
        ["Grado:", alumno["grado"]],
        ["Grupo:", alumno["grupo"]],
    ]

    tabla_datos = Table(datos_generales)
    tabla_datos.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.grey)]))

    elementos.append(tabla_datos)
    elementos.append(Spacer(1, 20))

    elementos.append(Paragraph("<b>Asistencias</b>", styles["Heading2"]))
    elementos.append(Spacer(1, 10))

    if asistencias:
        datos_asist = [["Fecha", "Estado"]]
        for a in asistencias:
            datos_asist.append([a["fecha"], a["estado"]])
        tabla_asist = Table(datos_asist)
        tabla_asist.setStyle(TableStyle([("GRID", (0,0), (-1,-1), 0.5, colors.grey)]))
        elementos.append(tabla_asist)
    else:
        elementos.append(Paragraph("Sin asistencias registradas.", styles["Normal"]))

    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph("Firma del Director: ____________________________", styles["Normal"]))
    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph("Firma del Padre o Tutor: ____________________________", styles["Normal"]))

    doc.build(elementos)

    return redirect(f"/static/kardex_{id}.pdf")

# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)