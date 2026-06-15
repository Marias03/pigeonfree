import json
import os
import requests
import time
from datetime import datetime

def get_weather_for_date(lat, lng, date_str, hora):
    try:
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lng,
            "start_date": date_str,
            "end_date": date_str,
            "hourly": "temperature_2m,precipitation,windspeed_10m,relativehumidity_2m",
            "timezone": "Europe/Moscow",
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        hora_idx = hora if hora < len(times) else 12

        return {
            "temperatura": hourly.get("temperature_2m", [None])[hora_idx],
            "precipitacion": hourly.get("precipitation", [0])[hora_idx],
            "viento": hourly.get("windspeed_10m", [None])[hora_idx],
            "humedad": hourly.get("relativehumidity_2m", [None])[hora_idx],
        }
    except:
        return {"temperatura": None, "precipitacion": 0, "viento": None, "humedad": None}

def enriquecer_con_clima():
    base = os.path.join(os.path.dirname(__file__), "../data")
    todos = []

    for fname in ["palomas_ebird.json", "palomas_ebird_historic.json"]:
        try:
            with open(f"{base}/{fname}") as f:
                data = json.load(f)
            for obs in data:
                if obs.get("fecha") and obs.get("lat"):
                    obs["fuente"] = fname
                    todos.append(obs)
        except:
            continue

    print(f"Total observaciones a enriquecer: {len(todos)}")

    enriquecidas = []
    for i, obs in enumerate(todos):
        fecha_str = obs["fecha"].split(" ")[0]
        hora = obs.get("hora") or 10

        try:
            datetime.strptime(fecha_str, "%Y-%m-%d")
        except:
            continue

        clima = get_weather_for_date(obs["lat"], obs["lng"], fecha_str, hora)
        obs["clima"] = clima
        enriquecidas.append(obs)

        if (i + 1) % 20 == 0:
            print(f"  Procesadas: {i+1}/{len(todos)}")
            time.sleep(0.5)

    output_path = f"{base}/palomas_con_clima.json"
    with open(output_path, "w") as f:
        json.dump(enriquecidas, f, indent=2)

    print(f"\nGuardadas {len(enriquecidas)} observaciones con clima en {output_path}")

if __name__ == "__main__":
    enriquecer_con_clima()