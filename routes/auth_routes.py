from flask import Blueprint, render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash

from database.mongo import usuarios, maestros

auth_bp = Blueprint("auth", __name__)


# =========================
# LOGIN (VISTA)
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

    # 🔐 LIMPIAR SESIÓN ANTES (IMPORTANTE)
    session.clear()

    # =========================
    # 1️⃣ ADMIN
    # =========================
    admin = usuarios.find_one({"usuario": usuario})

    if admin:

        password_db = admin.get("password", "")

        # 🔐 PASSWORD ENCRIPTADO
        if password_db.startswith("pbkdf2"):
            if check_password_hash(password_db, password):

                session["usuario"] = admin["usuario"]
                session["rol"] = "admin"

                return redirect(url_for("admin.admin_dashboard"))

        # 🔓 PASSWORD NORMAL (compatibilidad)
        elif password_db == password:

            session["usuario"] = admin["usuario"]
            session["rol"] = "admin"

            return redirect(url_for("admin.admin_dashboard"))

    # =========================
    # 2️⃣ MAESTRO
    # =========================
    maestro = maestros.find_one({"usuario": usuario})

    if maestro:

        password_db = maestro.get("password", "")

        # 🔐 PASSWORD ENCRIPTADO
        if password_db.startswith("pbkdf2"):
            if check_password_hash(password_db, password):

                session["usuario"] = maestro["usuario"]
                session["rol"] = "maestro"

                # 🔥 usar endpoint correcto si tienes blueprint
                return redirect(url_for("maestro.panel_maestro"))

        # 🔓 PASSWORD NORMAL
        elif password_db == password:

            session["usuario"] = maestro["usuario"]
            session["rol"] = "maestro"

            return redirect(url_for("maestro.panel_maestro"))

    # =========================
    # ❌ LOGIN FALLIDO
    # =========================
    return redirect(url_for("auth.login"))


# =========================
# LOGOUT
# =========================
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))