from flask import Flask
from pymongo import MongoClient
import os

app = Flask(__name__)

# =========================
# CONEXION A MONGODB ATLAS
# =========================

MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["control_escolar"]
    client.server_info()  # fuerza conexión real
    conexion_mongo = True
except Exception as e:
    print("ERROR CONECTANDO A MONGODB:")
    print(e)
    conexion_mongo = False


# =========================
# RUTA PRINCIPAL
# =========================

@app.route("/")
def inicio():
    if conexion_mongo:
        return """
        <h1 style='color:green'>SERVIDOR FUNCIONANDO CORRECTAMENTE</h1>
        <h2>Flask: OK</h2>
        <h2>Gunicorn: OK</h2>
        <h2>MongoDB Atlas: CONECTADO</h2>
        """
    else:
        return """
        <h1 style='color:red'>SERVIDOR ARRANCO PERO</h1>
        <h2>MongoDB NO CONECTA</h2>
        <p>Revisa tu MONGO_URI en Render → Environment</p>
        """

# =========================
# RUTA TEST
# =========================

@app.route("/ping")
def ping():
    return "PONG - El servidor responde"

# =========================
# IMPORTANTE PARA RENDER
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)