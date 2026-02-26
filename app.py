from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# ------------------------
# LOGIN
# ------------------------

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def do_login():
    usuario = request.form.get("usuario")
    password = request.form.get("password")

    # acceso direccion
    if usuario == "direccion" and password == "1234":
        return redirect(url_for("admin"))

    return redirect(url_for("login"))

# ------------------------
# PANEL ADMIN
# ------------------------

@app.route("/admin")
def admin():
    return render_template("admin.html")

# ------------------------
# ALUMNOS
# ------------------------

@app.route("/nuevo_alumno")
def nuevo_alumno():
    return render_template("nuevo_alumno.html")

@app.route("/alumno")
def alumno():
    return render_template("alumno.html")

# ------------------------
# MAESTROS
# ------------------------

@app.route("/nuevo_maestro")
def nuevo_maestro():
    return render_template("nuevo_maestro.html")

@app.route("/maestro")
def maestro():
    return render_template("maestro.html")

# ------------------------

if __name__ == "__main__":
    app.run(debug=True)