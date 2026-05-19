import os
import json
import time
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

    # 🔥 REINTENTOS PARA RENDER SLEEP
    for intento in range(5):

        try:

            response = requests.post(

                f"{LICENSE_SERVER}/validar",

                json={
                    "license_key": LICENSE_KEY,
                    "install_id": INSTALL_ID
                },

                timeout=15
            )

            data = response.json()

            # =========================
            # LICENCIA VÁLIDA
            # =========================
            if data.get("valida"):

                data["ultima_validacion"] = datetime.now().isoformat()

                guardar_cache(data)

                return True, data

            return False, data.get("mensaje")

        except Exception:

            # 🔥 Espera entre reintentos
            time.sleep(3)

    # =========================
    # FALLÓ SERVIDOR
    # =========================
    cache = leer_cache()

    if not cache:

        return False, "Sin conexión y sin caché"

    try:

        ultima = datetime.fromisoformat(
            cache["ultima_validacion"]
        )

    except:

        return False, "Cache corrupto"

    # 🔥 TOLERANCIA OFFLINE
    dias = cache.get("offline_dias", 7)

    if datetime.now() - ultima <= timedelta(days=dias):

        return True, cache

    return False, "Licencia expirada sin conexión"


# =========================
# VALIDAR SOLO 1 VEZ AL DÍA
# =========================
def licencia_activa():

    cache = leer_cache()

    # =========================
    # USAR CACHE SI ES RECIENTE
    # =========================
    if cache:

        try:

            ultima = datetime.fromisoformat(
                cache["ultima_validacion"]
            )

            # 🔥 24 HORAS SIN CONSULTAR
            if datetime.now() - ultima < timedelta(hours=24):

                return cache.get("valida", False)

        except:

            pass

    # =========================
    # VALIDAR ONLINE
    # =========================
    valido, _ = validar_online()

    return valido