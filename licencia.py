import os
import json
import requests
from datetime import datetime, timedelta

LICENSE_SERVER = os.getenv("LICENSE_SERVER")

LICENSE_KEY = os.getenv("LICENSE_KEY")
INSTALL_ID = os.getenv("INSTALL_ID")

CACHE_FILE = "licencia_cache.json"


# =========================
# GUARDAR CACHE
# =========================
def guardar_cache(data):

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


# =========================
# LEER CACHE
# =========================
def leer_cache():

    if not os.path.exists(CACHE_FILE):
        return None

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None


# =========================
# VALIDAR ONLINE
# =========================
def validar_online():

    if not LICENSE_SERVER:
        return False, "Servidor de licencias no configurado"

    try:

        response = requests.post(
            f"{LICENSE_SERVER}/validar",
            json={
                "license_key": LICENSE_KEY,
                "install_id": INSTALL_ID
            },
            timeout=10
        )

        data = response.json()

        if data.get("valida"):

            data["ultima_validacion"] = datetime.now().isoformat()

            guardar_cache(data)

            return True, data

        return False, data.get("mensaje")

    except Exception as e:

        cache = leer_cache()

        if not cache:
            return False, "Sin conexión y sin caché"

        ultima = datetime.fromisoformat(cache["ultima_validacion"])

        dias = cache.get("offline_dias", 7)

        if datetime.now() - ultima <= timedelta(days=dias):
            return True, cache

        return False, "Licencia expirada sin conexión"


# =========================
# MODO RESTRINGIDO
# =========================
def licencia_activa():

    valido, _ = validar_online()

    return valido