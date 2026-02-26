from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "control_escolar_secret_key"


# =========================
# LOGIN
# =========================

@app.route("/")
def inicio():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]

        # Usuario principal (dirección)
        if usuario == "direccion" and password == "1234":
            session["usuario"] = usuario
            session["rol"] = "direccion"
            return redirect(url_for("admin"))

        return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")


# =========================
# PANEL ADMIN
# =========================

@app.route("/admin")
def admin():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("admin.html")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================

if __name__ == "__main__":
    app.run(debug=True)