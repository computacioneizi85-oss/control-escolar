from flask import Blueprint, render_template, request, redirect, session

from database.mongo import usuarios


auth_bp = Blueprint("auth", __name__)


# =========================
# LOGIN
# =========================

@auth_bp.route("/")
def login():

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

        # ADMIN
        if user["rol"] == "admin":
            return redirect("/admin")

        # MAESTRO
        if user["rol"] == "maestro":
            return redirect("/panel_maestro")

    return redirect("/")


# =========================
# LOGOUT
# =========================

@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/")