from pymongo import MongoClient

MONGO_URI = "mongodb+srv://joel:CAMELLO2052@ethhsnm.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)

db = client["control_escolar"]

usuarios = db["usuarios"]