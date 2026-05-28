from flask import Blueprint
from flask import render_template

@pagos_bp.route("/admin/pagos")
def pagos_admin():

    return render_template(
        "pagos_admin.html"
    )

pagos_bp = Blueprint(
    "pagos",
    __name__
)