from flask import Flask, session, redirect, request
import os

# BLUEPRINTS
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.maestro_routes import maestro_bp

app = Flask(__name__)

# =========================
# 🔐 CLAVE SEGURA
# =========================
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))


# =========================
# REGISTRAR BLUEPRINTS
# =========================

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(maestro_bp)


# =========================
# PROTEGER RUTAS (FIX 🔥)
# =========================

@app.before_request
def proteger_rutas():

    # rutas públicas
    rutas_publicas = ["/", "/login"]

    # permitir archivos estáticos
    if request.path.startswith("/static"):
        return

    # permitir login
    if request.path in rutas_publicas:
        return

    # 🔥 permitir rutas internas de flask (muy importante en producción)
    if request.endpoint is None:
        return

    # si no hay sesión → redirigir
    if "usuario" not in session:
        return redirect("/")


# =========================
# EJECUTAR APP
# =========================

if __name__ == "__main__":
    app.run(debug=True)