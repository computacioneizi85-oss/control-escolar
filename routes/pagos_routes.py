from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from bson.objectid import ObjectId

from database.mongo import (
    pagos,
    alumnos,
    movimientos_pagos
)


pagos_bp = Blueprint(
    "pagos",
    __name__
)

def recalcular_pago(pago_id):

    movimientos = list(

        movimientos_pagos.find({

            "pago_id": str(pago_id),

            "estatus": "activo"

        })

    )

    pago = pagos.find_one({

        "_id": ObjectId(pago_id)

    })

    if not pago:
        return

    total_pagado = sum(
        m.get("monto", 0)
        for m in movimientos
    )

    meses_pagados = len(movimientos)

    saldo_restante = max(
        pago["total_debe"] - total_pagado,
        0
    )

    if saldo_restante == 0:

        estatus = "pagado"

    elif total_pagado > 0:

        estatus = "parcial"

    else:

        estatus = "pendiente"

    pagos.update_one(

        {
            "_id": ObjectId(pago_id)
        },

        {
            "$set": {

                "total_pagado": total_pagado,

                "saldo_restante": saldo_restante,

                "meses_pagados": meses_pagados,

                "estatus": estatus

            }

        }

    )


# =========================
# PANEL PAGOS
# =========================
@pagos_bp.route("/admin/pagos")
def pagos_admin():

    lista_pagos = pagos.find()

    return render_template(
        "pagos_admin.html",
        pagos_db=lista_pagos
    )


# =========================
# NUEVO CONTROL
# =========================
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

            "estatus": "pendiente"

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


# =========================
# REGISTRAR ABONO
# =========================
@pagos_bp.route(
    "/admin/abonar/<id>",
    methods=["GET", "POST"]
)
def registrar_abono(id):

    pago = pagos.find_one({
        "_id": ObjectId(id)
    })

    if not pago:

        flash("Pago no encontrado")

        return redirect(
            url_for("pagos.pagos_admin")
        )

    if request.method == "POST":

        monto = float(
            request.form["monto"]
        )

        metodo = request.form["metodo"]

        mes_cubierto = request.form["mes_cubierto"]

        nuevo_total_pagado = (
            pago["total_pagado"] + monto
        )

        nuevo_saldo = (
            pago["saldo_restante"] - monto
        )

        nuevos_meses_pagados = (
            pago["meses_pagados"] + 1
        )

        # =========================
        # MOVIMIENTO FINANCIERO
        # =========================
        movimientos_pagos.insert_one({

            "pago_id": str(pago["_id"]),

            "alumno": pago["alumno"],

            "grupo": pago.get("grupo", ""),

            "monto": monto,

            "metodo": metodo,

            "mes_cubierto": mes_cubierto,

            "ciclo_escolar": session.get(
                "ciclo_escolar",
                "2025-2026"
            ),

            "fecha_pago": datetime.now().strftime(
                "%d/%m/%Y"
            ),

            "hora_pago": datetime.now().strftime(
                "%H:%M"
            ),

            "capturado_por": session.get(
                "usuario",
                "admin"
            ),

            "estatus": "activo"

        })

        recalcular_pago(
            pago["_id"]
        ),

    "hora_pago": datetime.now().strftime("%H:%M"),

    "capturado_por": session.get(
        "usuario",
        "admin"
    ),

    "estatus": "activo"

})

        # =========================
        # ESTATUS
        # =========================
        if nuevo_saldo <= 0:

            estatus = "pagado"

            nuevo_saldo = 0

        else:

            estatus = "parcial"

        # =========================
        # ACTUALIZAR CONTROL
        # =========================
        pagos.update_one(

            {
                "_id": ObjectId(id)
            },

            {
                "$set": {

                    "total_pagado": nuevo_total_pagado,

                    "saldo_restante": nuevo_saldo,

                    "meses_pagados": nuevos_meses_pagados,

                    "estatus": estatus

                }
            }

        )

        flash("Abono registrado")

        return redirect(
            url_for("pagos.pagos_admin")
        )

    return render_template(
        "registrar_abono.html",
        pago=pago
    )


# =========================
# EXPEDIENTE FINANCIERO
# =========================
@pagos_bp.route("/admin/expediente_pago/<id>")
def expediente_pago(id):

    pago = pagos.find_one({
        "_id": ObjectId(id)
    })

    movimientos = movimientos_pagos.find({

        "pago_id": str(id)

    })

    return render_template(

        "expediente_pago.html",

        pago=pago,

        movimientos=movimientos

    )

@pagos_bp.route(
    "/admin/editar_movimiento/<id>",
    methods=["GET","POST"]
)
def editar_movimiento(id):

    movimiento = movimientos_pagos.find_one({
        "_id": ObjectId(id)
    })

    if request.method == "POST":

        movimientos_pagos.update_one(

            {
                "_id": ObjectId(id)
            },

            {
                "$set": {

                    "monto": float(
                        request.form["monto"]
                    ),

                    "metodo":
                    request.form["metodo"],

                    "mes_cubierto":
                    request.form["mes_cubierto"]

                }
            }

        )

        recalcular_pago(
            movimiento["pago_id"]
        )

        flash("Movimiento actualizado")

        return redirect(
            url_for(
                "pagos.expediente_pago",
                id=movimiento["pago_id"]
            )
        )

    return render_template(
        "editar_movimiento.html",
        movimiento=movimiento
    )

@pagos_bp.route(
    "/admin/eliminar_movimiento/<id>",
    methods=["POST"]
)
def eliminar_movimiento(id):

    movimiento = movimientos_pagos.find_one({
        "_id": ObjectId(id)
    })

    if movimiento:

        movimientos_pagos.update_one(

            {
                "_id": ObjectId(id)
            },

            {
                "$set": {
                    "estatus": "cancelado"
                }
            }

        )

        recalcular_pago(
            movimiento["pago_id"]
        )

    flash("Movimiento eliminado")

    return redirect(
        url_for(
            "pagos.expediente_pago",
            id=movimiento["pago_id"]
        )
    )

@pagos_bp.route(
    "/admin/editar_pago/<id>",
    methods=["GET", "POST"]
)
def editar_pago(id):

    pago = pagos.find_one({
        "_id": ObjectId(id)
    })

    if not pago:
        flash("Pago no encontrado")
        return redirect(url_for("pagos.pagos_admin"))

    if request.method == "POST":

        pagos.update_one(

            {
                "_id": ObjectId(id)
            },

            {
                "$set": {

                    "mensualidad": float(
                        request.form["mensualidad"]
                    ),

                    "meses_totales": int(
                        request.form["meses_totales"]
                    )

                }
            }

        )

        pago_actualizado = pagos.find_one({
            "_id": ObjectId(id)
        })

        pagos.update_one(
            {
                "_id": ObjectId(id)
            },
            {
                "$set": {
                    "total_debe":
                    pago_actualizado["mensualidad"] *
                    pago_actualizado["meses_totales"]
                }
            }
        )

        recalcular_pago(id)

        flash("Pago actualizado")

        return redirect(
            url_for("pagos.pagos_admin")
        )

    return render_template(
        "editar_pago.html",
        pago=pago
    )

@pagos_bp.route(
    "/admin/eliminar_pago/<id>",
    methods=["POST"]
)
def eliminar_pago(id):

    pagos.delete_one({
        "_id": ObjectId(id)
    })

    movimientos_pagos.delete_many({
        "pago_id": str(id)
    })

    flash("Pago eliminado")

    return redirect(
        url_for("pagos.pagos_admin")
    )