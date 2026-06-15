import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

EBIRD_API_KEY = os.getenv("EBIRD_API_KEY")

def descargar_historico():
    observaciones = []
    headers = {"X-eBirdApiToken": EBIRD_API_KEY}
    
    # Descargar por cada mes de los últimos 2 años
    meses = []
    for year in [2023, 2024, 2025]:
        for month in range(1, 13):
            meses.append((year, month))

    print(f"Descargando {len(meses)} meses de datos históricos...")

    for year, month in meses:
        url = f"https://api.ebird.org/v2/data/obs/RU-TA/historic/{year}/{month}/1"
        params = {
            "speciesCode": "rocpig",
            "maxResults": 10000,
            "includeProvisional": "true",
        }

        try:
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"  {year}/{month:02d} — error {resp.status_code}")
                continue

            data = resp.json()
            if not isinstance(data, list):
                continue

            mes_obs = 0
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
                    "cantidad": obs.get("howMany") or 1,
                    "lugar": obs.get("locName", ""),
                    "year": year,
                    "month": month,
                })
                mes_obs += 1

            print(f"  {year}/{month:02d} — {mes_obs} observaciones")
            time.sleep(0.3)

        except Exception as e:
            print(f"  {year}/{month:02d} — error: {e}")

    output_path = os.path.join(os.path.dirname(__file__), "../data/palomas_ebird_historic.json")
    with open(output_path, "w") as f:
        json.dump(observaciones, f, indent=2, ensure_ascii=False)

    print(f"\nTotal: {len(observaciones)} observaciones históricas")
    print(f"Con hora: {sum(1 for o in observaciones if o['hora'] is not None)}")
    print(f"Guardadas en {output_path}")
    return observaciones

if __name__ == "__main__":
    descargar_historico()