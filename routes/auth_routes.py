from flask import Blueprint, render_template, request, redirect, session
from database.mongo import usuarios, maestros

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

    # 1️⃣ BUSCAR ADMIN
    admin = usuarios.find_one({
        "usuario": usuario,
        "password": password
    })

    if admin:

        session["usuario"] = admin["usuario"]
        session["rol"] = "admin"

        return redirect("/admin")

    # 2️⃣ BUSCAR MAESTRO
    maestro = maestros.find_one({
        "usuario": usuario,
        "password": password
    })

    if maestro:

        session["usuario"] = maestro["usuario"]
        session["rol"] = "maestro"

        return redirect("/panel_maestro")

    return redirect("/")


# =========================
# LOGOUT
# =========================

@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/")