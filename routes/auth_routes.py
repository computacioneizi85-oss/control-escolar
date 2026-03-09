from flask import Blueprint, render_template, request, redirect, session
from database.mongo import usuarios

auth_bp = Blueprint("auth", __name__)


# =========================
# PÁGINA LOGIN
# =========================
@auth_bp.route("/")
def login():

    if "rol" in session:

        if session["rol"] == "admin":
            return redirect("/admin")

        if session["rol"] == "maestro":
            return redirect("/panel_maestro")

    return render_template("login.html")


# =========================
# PROCESAR LOGIN
# =========================
@auth_bp.route("/login", methods=["POST"])
def procesar_login():

    usuario = request.form.get("usuario")
    password = request.form.get("password")

    user = usuarios.find_one({
        "usuario": usuario,
        "password": password
    })

    if user:

        session["usuario"] = user["usuario"]
        session["rol"] = user["rol"]

        if user["rol"] == "admin":
            return redirect("/admin")

        if user["rol"] == "maestro":
            return redirect("/panel_maestro")

    return redirect("/")


# =========================
# CERRAR SESIÓN
# =========================
@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/")