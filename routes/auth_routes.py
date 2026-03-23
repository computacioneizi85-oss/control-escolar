from flask import Blueprint, render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash

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

    # =========================
    # 1️⃣ ADMIN
    # =========================

    admin = usuarios.find_one({"usuario": usuario})

    if admin:

        if "password" in admin and admin["password"].startswith("pbkdf2"):
            if check_password_hash(admin["password"], password):

                session["usuario"] = admin["usuario"]
                session["rol"] = "admin"

                return redirect(url_for("admin.admin_dashboard"))

        elif admin.get("password") == password:

            session["usuario"] = admin["usuario"]
            session["rol"] = "admin"

            return redirect(url_for("admin.admin_dashboard"))

    # =========================
    # 2️⃣ MAESTRO
    # =========================

    maestro = maestros.find_one({"usuario": usuario})

    if maestro:

        if "password" in maestro and maestro["password"].startswith("pbkdf2"):
            if check_password_hash(maestro["password"], password):

                session["usuario"] = maestro["usuario"]
                session["rol"] = "maestro"

                return redirect("/panel_maestro")

        elif maestro.get("password") == password:

            session["usuario"] = maestro["usuario"]
            session["rol"] = "maestro"

            return redirect("/panel_maestro")

    return redirect(url_for("auth.login"))


# =========================
# LOGOUT
# =========================

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))