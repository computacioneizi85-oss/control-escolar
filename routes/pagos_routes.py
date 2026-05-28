from flask import Blueprint, render_template

pagos_bp = Blueprint(
    "pagos",
    __name__
)

@pagos_bp.route("/admin/pagos")
def pagos_admin():

    return render_template(
        "pagos_admin.html"
    )