from flask import Flask, render_template, request, redirect, session, send_file
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from functools import wraps
import os, random, string
from datetime import timedelta, datetime

# PDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# ---------------- APP ----------------
app = Flask(__name__)
app.secret_key = "CONTROL_ESCOLAR_2026_ULTRA"
app.permanent_session_lifetime = timedelta(hours=12)

# ---------------- MONGODB ----------------
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
mongo = PyMongo(app)

# ---------------- UTILIDADES ----------------
def generar_password(n=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(n))

def login_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user" not in session:
                return redirect("/")
            if session.get("role") != role:
                return "Acceso denegado"
            return f(*args, **kwargs)
        return decorated
    return wrapper

# ---------------- ADMIN AUTOMATICO ----------------
if not mongo.db.usuarios.find_one({"correo":"admin@escuela.com"}):
    mongo.db.usuarios.insert_one({
        "correo":"admin@escuela.com",
        "password":generate_password_hash("admin123"),
        "role":"admin"
    })

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        correo=request.form["correo"].lower()
        password=request.form["password"]

        user=mongo.db.usuarios.find_one({"correo":correo})
        if not user or not check_password_hash(user["password"],password):
            return render_template("login.html", error="Usuario o contraseña incorrectos")

        session["user"]=correo
        session["role"]=user["role"]

        if user["role"]=="admin":
            return redirect("/admin")
        if user["role"]=="maestro":
            return redirect("/maestro")

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- PANEL ADMIN ----------------
@app.route("/admin")
@login_required("admin")
def admin():

    grupo = request.args.get("grupo")

    if grupo:
        alumnos = list(mongo.db.alumnos.find({"grupo":grupo}))
        maestros = list(mongo.db.maestros.find({"grupo":grupo}))
    else:
        alumnos = list(mongo.db.alumnos.find())
        maestros = list(mongo.db.maestros.find())

    grupos = list(mongo.db.grupos.find())

    return render_template("admin.html", alumnos=alumnos, maestros=maestros, grupos=grupos)

# ---------------- CREAR GRUPOS ----------------
@app.route("/grupos", methods=["GET","POST"])
@login_required("admin")
def grupos():
    if request.method=="POST":
        nombre=request.form["nombre"]
        if nombre:
            mongo.db.grupos.insert_one({"nombre":nombre})
    grupos=list(mongo.db.grupos.find())
    return render_template("grupos.html", grupos=grupos)

# ---------------- NUEVO ALUMNO ----------------
@app.route("/nuevo_alumno")
@login_required("admin")
def nuevo_alumno():
    grupos=list(mongo.db.grupos.find())
    return render_template("nuevo_alumno.html", grupos=grupos)

@app.route("/guardar_alumno", methods=["POST"])
@login_required("admin")
def guardar_alumno():
    nombre=request.form["nombre"]
    correo=request.form["correo"].lower()
    grupo=request.form["grupo"]
    password=request.form.get("password") or generar_password()

    mongo.db.alumnos.insert_one({"nombre":nombre,"correo":correo,"grupo":grupo,"calificacion":""})

    mongo.db.usuarios.insert_one({
        "correo":correo,
        "password":generate_password_hash(password),
        "role":"alumno"
    })
    return redirect("/admin")

# ---------------- NUEVO MAESTRO ----------------
@app.route("/nuevo_maestro")
@login_required("admin")
def nuevo_maestro():
    grupos=list(mongo.db.grupos.find())
    return render_template("nuevo_maestro.html", grupos=grupos)

@app.route("/guardar_maestro", methods=["POST"])
@login_required("admin")
def guardar_maestro():
    nombre=request.form["nombre"]
    correo=request.form["correo"].lower()
    grupo=request.form["grupo"]
    password=request.form.get("password") or generar_password()

    mongo.db.maestros.insert_one({"nombre":nombre,"correo":correo,"grupo":grupo})

    mongo.db.usuarios.insert_one({
        "correo":correo,
        "password":generate_password_hash(password),
        "role":"maestro"
    })
    return redirect("/admin")

# ---------------- ASIGNAR GRUPO ----------------
@app.route("/asignar_grupos", methods=["GET","POST"])
@login_required("admin")
def asignar_grupos():
    if request.method=="POST":
        maestro_id=request.form["maestro"]
        grupo=request.form["grupo"]
        mongo.db.maestros.update_one({"_id":ObjectId(maestro_id)},{"$set":{"grupo":grupo}})
        return redirect("/asignar_grupos")

    maestros=list(mongo.db.maestros.find())
    grupos=list(mongo.db.grupos.find())
    return render_template("asignar_grupos.html", maestros=maestros, grupos=grupos)

# ---------------- PANEL MAESTRO ----------------
@app.route("/maestro")
@login_required("maestro")
def maestro():
    correo=session["user"]
    maestro=mongo.db.maestros.find_one({"correo":correo})
    alumnos=list(mongo.db.alumnos.find({"grupo":maestro["grupo"]}))
    return render_template("maestro.html", alumnos=alumnos, grupo=maestro["grupo"])

# ---------------- RESET PASSWORD ----------------
@app.route("/reset_password/<correo>")
@login_required("admin")
def reset_password(correo):

    correo = correo.lower().strip()
    nueva = generar_password()

    mongo.db.usuarios.update_one(
        {"correo":correo},
        {"$set":{"password":generate_password_hash(nueva)}}
    )

    return f"<h2>Nueva contraseña:</h2><h3>{nueva}</h3><a href='/admin'>Volver</a>"

# ---------------- ELIMINAR ----------------
@app.route("/eliminar_alumno/<id>")
@login_required("admin")
def eliminar_alumno(id):
    alumno=mongo.db.alumnos.find_one({"_id":ObjectId(id)})
    mongo.db.usuarios.delete_one({"correo":alumno["correo"]})
    mongo.db.alumnos.delete_one({"_id":ObjectId(id)})
    return redirect("/admin")

@app.route("/eliminar_maestro/<id>")
@login_required("admin")
def eliminar_maestro(id):
    maestro=mongo.db.maestros.find_one({"_id":ObjectId(id)})
    mongo.db.usuarios.delete_one({"correo":maestro["correo"]})
    mongo.db.maestros.delete_one({"_id":ObjectId(id)})
    return redirect("/admin")

# ---------------- KARDEX PDF ----------------
@app.route("/kardex/<id>")
@login_required("admin")
def kardex(id):

    alumno = mongo.db.alumnos.find_one({"_id": ObjectId(id)})

    asistencias = list(mongo.db.asistencias.find({"alumno": alumno["nombre"]}))
    participaciones = list(mongo.db.participaciones.find({"alumno": alumno["nombre"]}))

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    pdf.setFont("Helvetica-Bold",18)
    pdf.drawString(190,750,"KARDEX ESCOLAR")

    pdf.setFont("Helvetica",11)
    pdf.drawString(50,720,f"Alumno: {alumno['nombre']}")
    pdf.drawString(50,700,f"Correo: {alumno['correo']}")
    pdf.drawString(50,680,f"Grupo: {alumno['grupo']}")
    pdf.drawString(50,660,f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")

    y=620
    pdf.setFont("Helvetica-Bold",13)
    pdf.drawString(50,y,"Asistencias")
    y-=20
    pdf.setFont("Helvetica",10)

    for a in asistencias[:20]:
        pdf.drawString(60,y,f"{a.get('fecha','')} - {a.get('estado','')}")
        y-=15

    y-=20
    pdf.setFont("Helvetica-Bold",13)
    pdf.drawString(50,y,"Participaciones")
    y-=20
    pdf.setFont("Helvetica",10)

    for p in participaciones[:20]:
        pdf.drawString(60,y,f"{p.get('fecha','')} - {p.get('puntos','')} pts")
        y-=15

    y-=30
    pdf.setFont("Helvetica-Bold",13)
    pdf.drawString(50,y,"Calificación Final")
    y-=20
    pdf.drawString(60,y,f"{alumno.get('calificacion','No registrada')}")

    pdf.line(80,120,260,120)
    pdf.drawString(120,105,"Firma Director")

    pdf.line(340,120,520,120)
    pdf.drawString(380,105,"Firma Padre/Tutor")

    pdf.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name=f"Kardex_{alumno['nombre']}.pdf",
                     mimetype="application/pdf")

# ---------------- RUN ----------------
if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)