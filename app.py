from flask import Flask
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.maestro_routes import maestro_bp
from routes.pdf_routes import pdf_bp

app = Flask(__name__)

app.secret_key = "control_escolar_secret"

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(maestro_bp)
app.register_blueprint(pdf_bp)

if __name__ == "__main__":
    app.run()