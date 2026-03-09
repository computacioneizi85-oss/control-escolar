from flask import Flask, session, redirect, request

# BLUEPRINTS
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.maestro_routes import maestro_bp

app = Flask(__name__)

# clave para sesiones
app.secret_key = "control_escolar_secret"


# =========================
# REGISTRAR BLUEPRINTS
# =========================

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(maestro_bp)


# =========================
# PROTEGER RUTAS
# =========================

@app.before_request
def proteger_rutas():

    rutas_publicas = ["/", "/login"]

    if request.path.startswith("/static"):
        return

    if request.path in rutas_publicas:
        return

    if "usuario" not in session:
        return redirect("/")


# =========================
# EJECUTAR APP
# =========================

if __name__ == "__main__":
    app.run(debug=True)