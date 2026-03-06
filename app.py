from flask import Flask, render_template, session, redirect
from config import MONGO_URI
from database.mongo import init_db

# BLUEPRINTS
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp

# CREAR APP
app = Flask(__name__)

app.secret_key = "control_escolar_secret_key"

# INICIAR BASE DE DATOS
init_db(MONGO_URI)

# REGISTRAR RUTAS
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)


# -----------------------
# PAGINA PRINCIPAL
# -----------------------

@app.route("/")
def index():

    if "rol" in session:

        if session["rol"] == "admin":
            return redirect("/admin")

        if session["rol"] == "maestro":
            return redirect("/maestro")

    return render_template("login.html")


# -----------------------
# LOGOUT
# -----------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# -----------------------
# ARRANQUE LOCAL
# -----------------------

if __name__ == "__main__":
    app.run(debug=True)