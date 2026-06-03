from datetime import datetime

from flask import send_file

from pdf.generador import (
    generar_recibo_pago_pdf,
    generar_corte_caja_pdf,
    generar_morosos_pdf
)

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
    movimientos_pagos,
    config_recargos
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

    lista_pagos = pagos.find({
        "activo": {
            "$ne": False
        }
    })

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

            "estatus": "pendiente",

            "observaciones": "",

            "beca": 0,

            "descuento": 0

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

        if monto > pago["saldo_restante"]:

            flash(
                "El monto excede el saldo pendiente"
            )

            return redirect(
                url_for(
                    "pagos.registrar_abono",
                    id=id
                )
            )

        concepto = request.form["concepto"]

        folio_recibo = (
            "REC-" +
            datetime.now().strftime(
                "%Y%m%d%H%M%S"
            )
        )

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

            "folio": folio_recibo,

            "concepto": concepto,

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
        )


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

    }).sort("_id", -1)

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
                    ),

                    "beca": float(
                        request.form.get(
                            "beca",
                            0
                        )
                    ),

                    "descuento": float(
                        request.form.get(
                            "descuento",
                            0
                        )
                    ),

                    "observaciones": request.form.get(
                        "observaciones",
                        ""
                    )

                }
            }


        )

        pago_actualizado = pagos.find_one({
            "_id": ObjectId(id)
        })

        mensualidad = pago_actualizado["mensualidad"]

        meses = pago_actualizado["meses_totales"]

        beca = pago_actualizado.get(
            "beca",
            0
        )

        descuento = pago_actualizado.get(
            "descuento",
            0
        )

        total = mensualidad * meses

        if beca > 0:

            total = total - (
                total * (beca / 100)
            )

        total = total - descuento

        if total < 0:
            total = 0

        pagos.update_one(

            {
                "_id": ObjectId(id)
            },

            {
                "$set": {

                    "total_debe": total

                }

            }

        )
        recalcular_pago(
            pago_actualizado["_id"]
        )

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

    pagos.update_one(

        {
            "_id": ObjectId(id)
        },

        {
            "$set": {
                "activo": False
            }
        }

    )

    flash("Pago desactivado")

    return redirect(
        url_for("pagos.pagos_admin")
    )

@pagos_bp.route(
    "/admin/recibo_pago/<id>"
)
def recibo_pago(id):

    movimiento = movimientos_pagos.find_one({

        "_id": ObjectId(id)

    })

    if not movimiento:

        flash("Movimiento no encontrado")

        return redirect(
            url_for("pagos.pagos_admin")
        )

    pdf = generar_recibo_pago_pdf(
        movimiento
    )

    return send_file(

        pdf,

        as_attachment=False,

        download_name=(
            movimiento.get(
                "folio",
                "recibo"
            ) + ".pdf"
        ),

        mimetype="application/pdf"

    )

@pagos_bp.route("/admin/morosos")
def morosos():

    lista = pagos.find({

        "saldo_restante": {
            "$gt": 0
        },

        "activo": {
            "$ne": False
        }

    })

    return render_template(

        "morosos.html",

        pagos_db=lista

    )

@pagos_bp.route("/admin/corte_caja")
def corte_caja():

    hoy = datetime.now().strftime(
        "%d/%m/%Y"
    )

    movimientos = list(

        movimientos_pagos.find({

            "fecha_pago": hoy,

            "estatus": "activo"

        })

    )

    total = sum(
        m.get("monto",0)
        for m in movimientos
    )

    return render_template(

        "corte_caja.html",

        movimientos=movimientos,

        total=total,

        fecha=hoy

    )

@pagos_bp.route(
    "/admin/corte_caja_pdf"
)
def corte_caja_pdf():

    hoy = datetime.now().strftime(
        "%d/%m/%Y"
    )

    movimientos = list(

        movimientos_pagos.find({

            "fecha_pago": hoy,

            "estatus": "activo"

        })

    )

    total = sum(

        m.get("monto", 0)

        for m in movimientos

    )

    pdf = generar_corte_caja_pdf(

        movimientos,

        hoy,

        total

    )

    return send_file(

        pdf,

        mimetype="application/pdf",

        as_attachment=False,

        download_name=(
            f"corte_caja_{hoy}.pdf"
        )

    )

@pagos_bp.route(
    "/admin/morosos_pdf"
)
def morosos_pdf():

    lista = list(

        pagos.find({

            "saldo_restante": {
                "$gt": 0
            },

            "activo": {
                "$ne": False
            }

        })

    )

    pdf = generar_morosos_pdf(
        lista
    )

    return send_file(

        pdf,

        mimetype="application/pdf",

        as_attachment=False,

        download_name="morosos.pdf"

    )

@pagos_bp.route("/admin/dashboard_financiero")
def dashboard_financiero():

    total_contratado = 0
    total_cobrado = 0
    total_pendiente = 0

    for p in pagos.find({

        "activo": {
            "$ne": False
        }

    }):

        total_contratado += p.get(
            "total_debe",
            0
        )

        total_cobrado += p.get(
            "total_pagado",
            0
        )

        total_pendiente += p.get(
            "saldo_restante",
            0
        )

    morosos = pagos.count_documents({

        "saldo_restante": {
            "$gt": 0
        },

        "activo": {
            "$ne": False
        }

    })

    hoy = datetime.now().strftime(
        "%d/%m/%Y"
    )

    ingresos_hoy = 0

    for m in movimientos_pagos.find({

        "fecha_pago": hoy,

        "estatus": "activo"

    }):

        ingresos_hoy += m.get(
            "monto",
            0
        )

    return render_template(

        "dashboard_financiero.html",

        total_contratado=total_contratado,

        total_cobrado=total_cobrado,

        total_pendiente=total_pendiente,

        morosos=morosos,

        ingresos_hoy=ingresos_hoy

    )

@pagos_bp.route(
    "/admin/config_recargos",
    methods=["GET", "POST"]
)
def config_recargos_admin():

if request.method == "POST":

    config_recargos.delete_many({})

    config_recargos.insert_one({

        "activo":
            "activo" in request.form,

        "dia_limite":
            int(
                request.form["dia_limite"]
            ),

        "porcentaje":
            float(
                request.form["porcentaje"]
            ),

        "aplicar_mensual":
            "aplicar_mensual"
            in request.form,

        "fecha_creacion":
            datetime.now(),

        "fecha_actualizacion":
            datetime.now()

    })

    flash(
        "Configuración guardada"
    )

    return redirect(
        "/admin/config_recargos"
    )

    config = config_recargos.find_one()

    return render_template(

        "config_recargos.html",

        config=config

    )