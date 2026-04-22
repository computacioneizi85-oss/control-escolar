from flask import Flask, session, redirect, request, url_for
from config import Config
from extensions import mongo
from datetime import timedelta


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 🔐 sesión
    app.permanent_session_lifetime = timedelta(minutes=30)

    mongo.init_app(app)

    # =========================
    # IMPORTAR BLUEPRINTS
    # =========================
    from admin.importador import importador_bp
    from admin.alumnos import alumnos_bp
    from admin.dashboard import dashboard_bp

    # 🔥 TUS ROUTES REALES
    from routes.auth_routes import auth_bp
    from routes.admin_routes import admin_bp
    from routes.maestro_routes import maestro_bp
    from routes.alumno_routes import alumno_bp
    from routes.padre_routes import padre_bp
    from routes.backup_routes import backup_bp

    # =========================
    # REGISTRAR BLUEPRINTS
    # =========================
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(importador_bp)
    app.register_blueprint(alumnos_bp)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(maestro_bp)
    app.register_blueprint(alumno_bp)
    app.register_blueprint(padre_bp)
    app.register_blueprint(backup_bp)

    # =========================
    # 🔐 PROTECCIÓN DE RUTAS
    # =========================
    @app.before_request
    def proteger_rutas():

        rutas_publicas = ["/", "/login"]

        if request.path.startswith("/static"):
            return

        if request.path in rutas_publicas:
            return

        if "usuario" not in session:
            return redirect(url_for("auth.login"))

        session.permanent = True
        rol = session.get("rol")

        # ADMIN
        if request.path.startswith("/admin"):
            if rol != "admin":
                return redirect(url_for("auth.login"))

        # MAESTRO
        if (
            request.path.startswith("/panel_maestro") or
            request.path.startswith("/horario") or
            request.path.startswith("/descargar_horario") or
            request.path.startswith("/citatorios") or
            request.path.startswith("/avisos_maestro") or
            request.path.startswith("/guardar_asistencia_ajax") or
            request.path.startswith("/guardar_calificaciones_ajax") or
            request.path.startswith("/crear_reporte") or
            request.path.startswith("/enviar_reportes_maestro")
        ):
            if rol != "maestro":
                return redirect(url_for("auth.login"))

        # ALUMNO
        if request.path.startswith("/panel_alumno"):
            if rol != "alumno":
                return redirect(url_for("auth.login"))

        # PADRE
        if request.path.startswith("/panel_padre"):
            if rol != "padre":
                return redirect(url_for("auth.login"))

        return

    # =========================
    # 🚫 NO CACHE
    # =========================
    @app.after_request
    def no_cache(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return app


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)