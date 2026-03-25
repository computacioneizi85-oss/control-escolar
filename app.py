from flask import Flask, session, redirect, request, url_for
import os

# =========================
# CREAR APP
# =========================
app = Flask(__name__)

# =========================
# 🔐 CLAVE SEGURA (MEJORADA)
# =========================
app.secret_key = os.environ.get("SECRET_KEY", "control_escolar_2026_seguro")


# =========================
# IMPORTAR BLUEPRINTS
# =========================
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.maestro_routes import maestro_bp
from routes.backup_routes import backup_bp


# =========================
# REGISTRAR BLUEPRINTS
# =========================
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(maestro_bp)
app.register_blueprint(backup_bp)


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

    # evitar errores internos de Flask
    if request.endpoint is None:
        return

    # 🔥 si no hay sesión → bloquear
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    # 🔥 validar rol (CLAVE)
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

    # todo correcto → continuar
    return


# =========================
# 🔒 EVITAR CACHE (SEGURIDAD)
# =========================
@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


# =========================
# EJECUCIÓN
# =========================
if __name__ == "__main__":
    app.run(debug=True)