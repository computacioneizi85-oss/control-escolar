from flask import Flask, session, redirect, request, url_for
import os

# =========================
# CREAR APP PRIMERO 🔥
# =========================
app = Flask(__name__)

# =========================
# 🔐 CLAVE SEGURA
# =========================
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# =========================
# IMPORTAR BLUEPRINTS
# =========================
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.maestro_routes import maestro_bp
from routes.backup_routes import backup_bp

# =========================
# REGISTRAR BLUEPRINTS 🔥
# =========================
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(maestro_bp)
app.register_blueprint(backup_bp)


# =========================
# PROTEGER RUTAS (CORREGIDO 🔥)
# =========================

@app.before_request
def proteger_rutas():

    rutas_publicas = ["/", "/login"]

    # permitir archivos estáticos
    if request.path.startswith("/static"):
        return

    # permitir rutas públicas
    if request.path in rutas_publicas:
        return

    # 🔥 permitir rutas admin si hay sesión
    if request.path.startswith("/admin"):
        if "usuario" in session:
            return
        else:
            return redirect(url_for("auth.login"))

    # 🔥 permitir rutas maestro si hay sesión
    if request.path.startswith("/panel_maestro"):
        if "usuario" in session:
            return
        else:
            return redirect(url_for("auth.login"))

    # 🔥 evitar errores internos de Flask
    if request.endpoint is None:
        return

    # 🔥 protección general
    if "usuario" not in session:
        return redirect(url_for("auth.login"))


# =========================
# EJECUTAR APP
# =========================

if __name__ == "__main__":
    app.run(debug=True)