from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)

db = client["control_escolar"]

usuarios = db["usuarios"]
alumnos = db["alumnos"]
maestros = db["maestros"]
grupos = db["grupos"]
materias = db["materias"]
calificaciones = db["calificaciones"]
reportes = db["reportes"]
asistencias = db["asistencias"]