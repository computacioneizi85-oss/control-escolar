from flask import Flask
from flask_session import Session
from config import SECRET_KEY

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.maestro_routes import maestro_bp

app = Flask(__name__)

app.secret_key = SECRET_KEY

app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Registrar rutas
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(maestro_bp)

if __name__ == "__main__":
    app.run()