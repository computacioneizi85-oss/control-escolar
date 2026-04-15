from flask import Blueprint, render_template, session, redirect, request
from bson.objectid import ObjectId

from database.mongo import alumnos, citatorios

padre_bp = Blueprint("padre", __name__)


def verificar_padre():
    return session.get("rol") == "padre"


# ================= PANEL =================
@padre_bp.route("/panel_padre")
def panel_padre():

    if not verificar_padre():
        return redirect("/")

    alumno_nombre = session.get("alumno")

    alumno = alumnos.find_one({"nombre": alumno_nombre})

    # 🔥 NUEVO: obtener citatorios del alumno
    lista_citatorios = list(
        citatorios.find({"alumno": alumno_nombre})
    )

    return render_template(
        "panel_padre.html",
        alumno=alumno,
        citatorios=lista_citatorios
    )


# ================= ENTERADO CALIFICACIONES =================
@padre_bp.route("/enterado", methods=["POST"])
def marcar_enterado():

    if not verificar_padre():
        return redirect("/")

    alumnos.update_one(
        {
            "nombre": request.form.get("alumno"),
            "calificaciones.materia": request.form.get("materia")
        },
        {
            "$set": {"calificaciones.$.enterado": True}
        }
    )

    return redirect("/panel_padre")


# ================= 🔥 ENTERADO CITATORIOS =================
@padre_bp.route("/enterado_citatorio/<id>")
def enterado_citatorio(id):

    if not verificar_padre():
        return redirect("/")

    citatorios.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"enterado": True}}
    )

    return redirect("/panel_padre")