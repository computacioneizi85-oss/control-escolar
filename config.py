import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "clave_super_segura_2026"

    # 🔥 Mongo Atlas
    MONGO_URI = os.environ.get("MONGO_URI") or "mongodb://localhost:27017/control_escolar"

    # opcional
    DEBUG = False