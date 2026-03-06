from flask import Blueprint, render_template, session, redirect

maestro_bp = Blueprint("maestro", __name__)

@maestro_bp.route("/maestro/dashboard")
def maestro_dashboard():

    if "rol" not in session:
        return redirect("/")

    if session["rol"] != "maestro":
        return redirect("/")

    return render_template("maestro.html")