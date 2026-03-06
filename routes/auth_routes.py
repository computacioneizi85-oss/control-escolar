@auth_bp.route("/login", methods=["POST"])
def login():

    usuario = request.form.get("usuario")
    password = request.form.get("password")

    print("USUARIO RECIBIDO:", usuario)
    print("PASSWORD RECIBIDO:", password)

    user = usuarios.find_one({
        "usuario": usuario,
        "password": password
    })

    print("USUARIO ENCONTRADO EN MONGO:", user)

    if user:

        session["usuario"] = usuario
        session["rol"] = user["rol"]

        if user["rol"] == "admin":
            return redirect("/admin")

        if user["rol"] == "maestro":
            return redirect("/maestro")

    return redirect("/")