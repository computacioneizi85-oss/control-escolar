from flask import Blueprint, render_template, session, redirect

maestro_bp = Blueprint("maestro", __name__)


@maestro_bp.route("/maestro")
def maestro_panel():

    if "rol" not in session:
        return redirect("/")

    if session["rol"] != "maestro":
        return redirect("/")

    return render_template("maestro.html")