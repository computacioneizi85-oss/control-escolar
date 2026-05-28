from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# =========================
# VARIABLES SaaS
# =========================

MONGO_URI = os.getenv("MONGO_URI")

LICENSE_KEY = os.getenv("LICENSE_KEY")
INSTALL_ID = os.getenv("INSTALL_ID")

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
avisos = db["avisos"]

configuracion = db["configuracion"]

horarios = db["horarios"]
citatorios = db["citatorios"]

pagos = db["pagos"]

padres = db["padres"]

# =========================
# NUEVAS COLECCIONES
# =========================

admins_secundarios = db["admins_secundarios"]
bitacora = db["bitacora"]
auditoria = db["auditoria"]

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

try:
    admins_secundarios.create_index("usuario", unique=True)
except:
    pass