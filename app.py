from flask import Flask, session, redirect, request, url_for
from datetime import timedelta
import os

# =========================
# CREAR APP
# =========================
app = Flask(__name__)

# =========================
# 🔐 CLAVE SEGURA (IMPORTANTE)
# =========================
app.secret_key = os.environ.get("SECRET_KEY") or "control_escolar_2026_seguro_fijo"

# =========================
# 🔒 TIEMPO DE SESIÓN (30 MIN)
# =========================
app.permanent_session_lifetime = timedelta(minutes=30)


# =========================
# IMPORTAR BLUEPRINTS
# =========================
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.maestro_routes import maestro_bp
from routes.backup_routes import backup_bp
from routes.alumno_routes import alumno_bp
from routes.padre_routes import padre_bp


# =========================
# REGISTRAR BLUEPRINTS
# =========================
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(maestro_bp)
app.register_blueprint(backup_bp)
app.register_blueprint(alumno_bp)
app.register_blueprint(padre_bp)


# =========================
# 🔐 PROTECCIÓN TOTAL DE RUTAS
# =========================
@app.before_request
def proteger_rutas():

    rutas_publicas = ["/", "/login"]

    # ✅ permitir archivos estáticos
    if request.path.startswith("/static"):
        return

    # ✅ permitir login
    if request.path in rutas_publicas:
        return

    # 🔴 CORRECCIÓN CLAVE
    if request.endpoint is None:
        return redirect(url_for("auth.login"))

    # 🔥 SI NO HAY SESIÓN
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    # 🔒 mantener sesión activa
    session.permanent = True

    rol = session.get("rol")

    # =========================
    # 🔴 ADMIN
    # =========================
    if request.path.startswith("/admin"):
        if rol != "admin":
            return redirect(url_for("auth.login"))

    # =========================
    # 🔵 MAESTRO
    # =========================
    if request.path.startswith("/panel_maestro"):
        if rol != "maestro":
            return redirect(url_for("auth.login"))

    # =========================
    # 🟢 ALUMNO
    # =========================
    if request.path.startswith("/panel_alumno"):
        if rol != "alumno":
            return redirect(url_for("auth.login"))

    # =========================
    # 🟣 PADRE
    # =========================
    if request.path.startswith("/panel_padre"):
        if rol != "padre":
            return redirect(url_for("auth.login"))

    return


# =========================
# 🔒 EVITAR CACHE
# =========================
@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# =========================
# EJECUCIÓN
# =========================
if __name__ == "__main__":
    app.run(debug=True)