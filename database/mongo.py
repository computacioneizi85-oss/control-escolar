import os
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI")

client = MongoClient(MONGO_URI)

db = client["control_escolar"]

usuarios = db["usuarios"]
alumnos = db["alumnos"]
grupos = db["grupos"]
materias = db["materias"]
calificaciones = db["calificaciones"]
reportes = db["reportes"]