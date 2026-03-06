import os

MONGO_URI = "mongodb+srv://joel:CAMELLO2052@cluster0.ethhsnm.mongodb.net/control_escolar?retryWrites=true&w=majority"

SECRET_KEY = "control_escolar_pro"

PORT = int(os.environ.get("PORT", 10000))