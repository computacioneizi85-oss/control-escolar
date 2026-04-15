from pymongo import MongoClient
import os

# =========================
# CONEXIÓN A MONGO
# =========================

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise Exception("❌ ERROR: MONGO_URI no está configurado")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

db = client["control_escolar"]

# =========================
# COLECCIONES
# =========================

usuarios = db["usuarios"]
alumnos = db["alumnos"]
maestros = db["maestros"]
grupos = db["grupos"]
materias = db["materias"]
reportes = db["reportes"]
calificaciones = db["calificaciones"]

configuracion = db["configuracion"]

horarios = db["horarios"]
citatorios = db["citatorios"]

padres = db["padres"]

# =========================
# ÍNDICES
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