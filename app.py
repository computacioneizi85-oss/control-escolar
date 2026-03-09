from flask import Flask, render_template, session, redirect

# BLUEPRINTS
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp

app = Flask(__name__)

app.secret_key = "control_escolar_secret"


# Registrar blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)


@app.route("/")
def index():

    if "rol" in session:

        if session["rol"] == "admin":
            return redirect("/admin")

        if session["rol"] == "maestro":
            return redirect("/maestro")

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)