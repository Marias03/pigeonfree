import requests
import json
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

EBIRD_API_KEY = os.getenv("EBIRD_API_KEY")

def descargar_ebird_kazan():
    observaciones = []
    
    print("Descargando datos de eBird para Kazán...")

    # eBird usa región codes — RU-TA es Tatarstan
    url = "https://api.ebird.org/v2/data/obs/RU-TA/recent"
    params = {
        "speciesCode": "rocpig",  # Rock Pigeon = paloma común
        "back": 30,  # últimos 30 días
        "maxResults": 10000,
        "includeProvisional": "true",
        "hotspot": "false",
    }
    headers = {
        "X-eBirdApiToken": EBIRD_API_KEY,
    }

    resp = requests.get(url, params=params, headers=headers)
    data = resp.json()

    print(f"Respuesta: {resp.status_code}")

    if isinstance(data, list):
        for obs in data:
            lat = obs.get("lat")
            lng = obs.get("lng")
            if not lat or not lng:
                continue

            obs_dt = obs.get("obsDt", "")
            hora = None
            if " " in obs_dt:
                try:
                    hora = int(obs_dt.split(" ")[1].split(":")[0])
                except:
                    pass

            observaciones.append({
                "lat": lat,
                "lng": lng,
                "fecha": obs_dt,
                "hora": hora,
                "cantidad": obs.get("howMany", 1),
                "lugar": obs.get("locName", ""),
            })

    output_path = os.path.join(os.path.dirname(__file__), "../data/palomas_ebird.json")
    with open(output_path, "w") as f:
        json.dump(observaciones, f, indent=2, ensure_ascii=False)

    print(f"\nTotal: {len(observaciones)} observaciones")
    print(f"Con hora: {sum(1 for o in observaciones if o['hora'] is not None)}")
    print(f"Guardadas en {output_path}")
    return observaciones

if __name__ == "__main__":
    descargar_ebird_kazan()