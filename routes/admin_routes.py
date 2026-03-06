from flask import Blueprint, render_template, session, redirect
from database.mongo import alumnos, maestros, grupos

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
def dashboard():

    if session.get("rol") != "admin":
        return redirect("/")

    total_alumnos = alumnos.count_documents({})
    total_maestros = maestros.count_documents({})
    total_grupos = grupos.count_documents({})

    return render_template(
        "admin/dashboard.html",
        alumnos=total_alumnos,
        maestros=total_maestros,
        grupos=total_grupos
    )