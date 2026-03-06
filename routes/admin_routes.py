from flask import Blueprint, render_template, session, redirect

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
def admin_panel():

    if "rol" not in session:
        return redirect("/")

    if session["rol"] != "admin":
        return redirect("/")

    return render_template("admin.html")