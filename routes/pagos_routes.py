from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from bson.objectid import ObjectId

from database.mongo import pagos, alumnos


pagos_bp = Blueprint(
    "pagos",
    __name__
)


@pagos_bp.route("/admin/pagos")
def pagos_admin():

    lista_pagos = pagos.find()

    return render_template(
        "pagos_admin.html",
        pagos_db=lista_pagos
    )


@pagos_bp.route(
    "/admin/nuevo_pago",
    methods=["GET", "POST"]
)
def nuevo_pago():

    if request.method == "POST":

        alumno_id = request.form["alumno_id"]

        mensualidad = float(
            request.form["mensualidad"]
        )

        meses_totales = int(
            request.form["meses_totales"]
        )

        alumno = alumnos.find_one({
            "_id": ObjectId(alumno_id)
        })

        total_debe = mensualidad * meses_totales

        pagos.insert_one({

            "alumno_id": str(alumno["_id"]),

            "alumno": alumno["nombre"],

            "grupo": alumno.get("grupo", ""),

            "concepto": "Colegiatura",

            "mensualidad": mensualidad,

            "meses_totales": meses_totales,

            "meses_pagados": 0,

            "total_debe": total_debe,

            "total_pagado": 0,

            "saldo_restante": total_debe,

            "estatus": "pendiente",

            "historial": []

        })

        flash("Pago creado correctamente")

        return redirect(
            url_for("pagos.pagos_admin")
        )

    lista_alumnos = alumnos.find()

    return render_template(
        "nuevo_pago.html",
        alumnos=lista_alumnos
    )