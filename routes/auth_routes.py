from flask import Blueprint, render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash

from database.mongo import usuarios, maestros, alumnos, padres

from datetime import datetime

from database.mongo import (
    usuarios,
    maestros,
    alumnos,
    padres,
    admins_secundarios,
    auditoria
)

auth_bp = Blueprint("auth", __name__)


# =========================
# LOGIN (VISTA)
# =========================
@auth_bp.route("/")
def login():
    return render_template("login.html")


# =========================
# FUNCIÓN UNIVERSAL DE VALIDACIÓN
# =========================
def validar_password(password_db, password_input):

    if not password_db:
        return False

    # 🔐 Detecta hash moderno (pbkdf2 o scrypt)
    if password_db.startswith("pbkdf2") or password_db.startswith("scrypt"):
        return check_password_hash(password_db, password_input)

    # 🔓 compatibilidad antigua
    return password_db == password_input


# =========================
# PROCESAR LOGIN
# =========================
@auth_bp.route("/login", methods=["POST"])
def procesar_login():

    session.clear()

    ip = request.remote_addr

    usuario = request.form.get("usuario")
    password = request.form.get("password")

    # =========================
    # SUPERADMIN
    # =========================

    admin = usuarios.find_one({"usuario": usuario})

    if admin and validar_password(admin.get("password"), password):

        session["usuario"] = admin["usuario"]
        session["rol"] = admin.get("rol", "superadmin")
        session["escuela"] = admin.get("escuela", "GLOBAL")

        auditoria.insert_one({
            "usuario": usuario,
            "rol": session["rol"],
            "evento": "login",
            "ip": ip,
            "fecha": datetime.now()
        })

        return redirect(url_for("admin.admin_dashboard"))

    # =========================
    # ADMIN SECUNDARIO
    # =========================

    admin_sec = admins_secundarios.find_one({
        "usuario": usuario,
        "activo": True
    })

    if admin_sec and validar_password(admin_sec.get("password"), password):

        session["usuario"] = admin_sec["usuario"]
        session["rol"] = "admin"
        session["escuela"] = admin_sec.get("escuela", "")
        session["admin_secundario"] = True

        auditoria.insert_one({
            "usuario": usuario,
            "rol": "admin_secundario",
            "evento": "login",
            "ip": ip,
            "fecha": datetime.now()
        })

        return redirect(url_for("admin.admin_dashboard"))

    # =========================
    # MAESTRO
    # =========================

    maestro = maestros.find_one({"usuario": usuario})

    if maestro and validar_password(maestro.get("password"), password):

        session["usuario"] = maestro["usuario"]
        session["rol"] = "maestro"

        auditoria.insert_one({
            "usuario": usuario,
            "rol": "maestro",
            "evento": "login",
            "ip": ip,
            "fecha": datetime.now()
        })

        return redirect(url_for("maestro.panel_maestro"))

    # =========================
    # ALUMNO
    # =========================

    alumno = alumnos.find_one({"usuario": usuario})

    if alumno and validar_password(alumno.get("password"), password):

        session["usuario"] = alumno["usuario"]
        session["rol"] = "alumno"
        session["alumno"] = alumno["nombre"]

        auditoria.insert_one({
            "usuario": usuario,
            "rol": "alumno",
            "evento": "login",
            "ip": ip,
            "fecha": datetime.now()
        })

        return redirect(url_for("alumno.panel_alumno"))

    # =========================
    # PADRE
    # =========================

    padre = padres.find_one({"usuario": usuario})

    if padre and validar_password(padre.get("password"), password):

        session["usuario"] = padre["usuario"]
        session["rol"] = "padre"
        session["alumno"] = padre["alumno"]

        auditoria.insert_one({
            "usuario": usuario,
            "rol": "padre",
            "evento": "login",
            "ip": ip,
            "fecha": datetime.now()
        })

        return redirect(url_for("padre.panel_padre"))

    return redirect(url_for("auth.login"))

# =========================
# LOGOUT
# =========================
@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("auth.login"))