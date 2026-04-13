from flask import Blueprint, render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash

from database.mongo import usuarios, maestros, alumnos, padres

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

    # 🔐 LIMPIAR SESIÓN
    session.clear()

    # =========================
    # 1️⃣ ADMIN
    # =========================
    admin = usuarios.find_one({"usuario": usuario})

    if admin:

        password_db = admin.get("password", "")

        if password_db.startswith("pbkdf2"):
            if check_password_hash(password_db, password):

                session["usuario"] = admin["usuario"]
                session["rol"] = "admin"

                return redirect(url_for("admin.admin_dashboard"))

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

        if password_db.startswith("pbkdf2"):
            if check_password_hash(password_db, password):

                session["usuario"] = maestro["usuario"]
                session["rol"] = "maestro"

                return redirect(url_for("maestro.panel_maestro"))

        elif password_db == password:

            session["usuario"] = maestro["usuario"]
            session["rol"] = "maestro"

            return redirect(url_for("maestro.panel_maestro"))

    # =========================
    # 3️⃣ ALUMNO (YA REAL)
    # =========================
    alumno = alumnos.find_one({"usuario": usuario})

    if alumno:

        password_db = alumno.get("password", "")

        # 🔐 CON HASH
        if password_db.startswith("pbkdf2"):
            if check_password_hash(password_db, password):

                session["usuario"] = alumno["usuario"]
                session["rol"] = "alumno"
                session["alumno"] = alumno["nombre"]

                return redirect(url_for("alumno.panel_alumno"))

        # 🔓 COMPATIBILIDAD (si aún no tiene hash)
        elif password_db == password:

            session["usuario"] = alumno["usuario"]
            session["rol"] = "alumno"
            session["alumno"] = alumno["nombre"]

            return redirect(url_for("alumno.panel_alumno"))

    # =========================
    # 4️⃣ PADRE (YA REAL)
    # =========================
    padre = padres.find_one({"usuario": usuario})

    if padre:

        password_db = padre.get("password", "")

        # 🔐 CON HASH
        if password_db.startswith("pbkdf2"):
            if check_password_hash(password_db, password):

                session["usuario"] = padre["usuario"]
                session["rol"] = "padre"
                session["alumno"] = padre["alumno"]

                return redirect(url_for("padre.panel_padre"))

        # 🔓 COMPATIBILIDAD
        elif password_db == password:

            session["usuario"] = padre["usuario"]
            session["rol"] = "padre"
            session["alumno"] = padre["alumno"]

            return redirect(url_for("padre.panel_padre"))

    # =========================
    # ⚠️ COMPATIBILIDAD ANTIGUA (NO BORRAR)
    # =========================

    # Alumno por nombre (viejo sistema)
    alumno = alumnos.find_one({"nombre": usuario})

    if alumno:

        session["usuario"] = alumno["nombre"]
        session["rol"] = "alumno"
        session["alumno"] = alumno["nombre"]

        return redirect(url_for("alumno.panel_alumno"))

    # Padre formato antiguo
    if usuario.startswith("padre_"):

        nombre_alumno = usuario.replace("padre_", "")

        alumno = alumnos.find_one({"nombre": nombre_alumno})

        if alumno:

            session["usuario"] = usuario
            session["rol"] = "padre"
            session["alumno"] = nombre_alumno

            return redirect(url_for("padre.panel_padre"))

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