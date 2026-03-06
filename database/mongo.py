from pymongo import MongoClient

MONGO_URI = "mongodb+srv://joel:CAMELLO2052@ethhsnm.mongodb.net/control_escolar?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)

db = client["control_escolar"]

usuarios = db["usuarios"]
alumnos = db["alumnos"]
grupos = db["grupos"]
materias = db["materias"]
reportes = db["reportes"]