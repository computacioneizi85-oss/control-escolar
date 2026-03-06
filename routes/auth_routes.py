from flask import Blueprint, render_template, request, redirect, session
from database.mongo import usuarios

# Crear blueprint
auth_bp = Blueprint("auth", __name__)

# Página de login
@auth_bp.route("/")
def login_page():
    return render_template("login.html")


# Procesar login
@auth_bp.route("/login", methods=["POST"])
def login():

    usuario = request.form.get("usuario")
    password = request.form.get("password")

    user = usuarios.find_one({
        "usuario": usuario,
        "password": password
    })

    if user:

        session["usuario"] = usuario
        session["rol"] = user["rol"]

        if user["rol"] == "admin":
            return redirect("/admin")

        if user["rol"] == "maestro":
            return redirect("/maestro")

    return redirect("/")


# Logout
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")