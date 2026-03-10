from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)

db = client["control_escolar"]

# COLECCIONES

usuarios = db["usuarios"]
alumnos = db["alumnos"]
grupos = db["grupos"]
maestros = db["maestros"]
materias = db["materias"]
reportes = db["reportes"]
calificaciones = db["calificaciones"]

# NUEVA COLECCION
configuracion = db["configuracion"]

horarios = db["horarios"]