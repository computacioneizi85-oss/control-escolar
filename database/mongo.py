from pymongo import MongoClient
import os

# =========================
# CONEXIÓN A MONGO
# =========================

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)

db = client["control_escolar"]


# =========================
# COLECCIONES PRINCIPALES
# =========================

usuarios = db["usuarios"]        # admin
alumnos = db["alumnos"]
maestros = db["maestros"]
grupos = db["grupos"]
materias = db["materias"]
reportes = db["reportes"]
calificaciones = db["calificaciones"]


# =========================
# CONFIGURACIÓN
# =========================

configuracion = db["configuracion"]


# =========================
# OPERACIÓN ESCOLAR
# =========================

horarios = db["horarios"]
citatorios = db["citatorios"]


# =========================
# 🆕 NUEVAS COLECCIONES
# =========================

padres = db["padres"]   # 🔥 LOGIN DE PADRES


# =========================
# ÍNDICES (MEJOR RENDIMIENTO)
# =========================

try:
    alumnos.create_index("usuario", unique=True)
except:
    pass

try:
    maestros.create_index("usuario", unique=True)
except:
    pass

try:
    usuarios.create_index("usuario", unique=True)
except:
    pass

try:
    padres.create_index("usuario", unique=True)
except:
    pass