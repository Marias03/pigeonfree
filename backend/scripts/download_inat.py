import requests
import json
import time
import os

def descargar_palomas_kazan():
    observaciones = []
    page = 1
    per_page = 200

    while True:
        print(f"Descargando página {page}...")

        params = {
            "taxon_name": "Columba livia",
            "per_page": per_page,
            "page": page,
            "photos": "true",
            "geo": "true",
            "order": "desc",
            "order_by": "created_at",
            "nelat": 56.1,
            "nelng": 49.5,
            "swlat": 55.6,
            "swlng": 48.8,
        }

        resp = requests.get("https://api.inaturalist.org/v1/observations", params=params)
        data = resp.json()

        resultados = data.get("results", [])
        if not resultados:
            break

        for obs in resultados:
            if not obs.get("geojson"):
                continue

            coords = obs["geojson"]["coordinates"]
            lat = coords[1]
            lng = coords[0]

            if not (55.6 <= lat <= 56.1 and 48.8 <= lng <= 49.5):
                continue

            fotos = obs.get("photos", [])
            if fotos:
                observaciones.append({
                    "id": obs["id"],
                    "lat": lat,
                    "lng": lng,
                    "fecha": obs.get("observed_on"),
                    "foto_url": fotos[0]["url"].replace("square", "medium")
                })

        print(f"  → {len(resultados)} en esta página, {len(observaciones)} válidas hasta ahora")

        if len(resultados) < per_page:
            break

        page += 1
        time.sleep(1)

    output_path = os.path.join(os.path.dirname(__file__), "../data/palomas_kazan_v2.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(observaciones, f, indent=2, ensure_ascii=False)

    print(f"\nTotal en Kazán: {len(observaciones)}")
    print(f"Guardadas en {output_path}")
    return observaciones

if __name__ == "__main__":
    descargar_palomas_kazan()