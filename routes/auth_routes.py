from flask import Blueprint, render_template, request, redirect, session
from database.mongo import usuarios

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def login_page():

    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def login():

    usuario = request.form.get("usuario")
    password = request.form.get("password")

    print("Usuario:", usuario)
    print("Password:", password)

    user = usuarios.find_one({
        "usuario": usuario,
        "password": password
    })

    print("Mongo:", user)

    if user:

        session["usuario"] = usuario
        session["rol"] = user["rol"]

        if user["rol"] == "admin":
            return redirect("/admin/dashboard")

        if user["rol"] == "maestro":
            return redirect("/maestro/dashboard")

    return redirect("/")