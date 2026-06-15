import requests
import json
import os
import time

def descargar_gbif_kazan():
    observaciones = []
    offset = 0
    limit = 300

    print("Descargando datos de GBIF para Kazán...")

    while True:
        params = {
            "taxonKey": 2495416,
            "decimalLatitude": "55.5,56.2",
            "decimalLongitude": "48.5,49.8",
            "hasCoordinate": "true",
            "hasGeospatialIssue": "false",
            "limit": limit,
            "offset": offset,
        }

        resp = requests.get(
            "https://api.gbif.org/v1/occurrence/search",
            params=params,
            headers={"User-Agent": "PigeonFree/1.0"}
        )
        data = resp.json()
        results = data.get("results", [])

        if not results:
            break

        for obs in results:
            lat = obs.get("decimalLatitude")
            lng = obs.get("decimalLongitude")
            if not lat or not lng:
                continue

            observaciones.append({
                "lat": lat,
                "lng": lng,
                "fecha": obs.get("eventDate", ""),
                "mes": obs.get("month"),
                "hora": obs.get("hour"),
                "dia": obs.get("day"),
                "especie": obs.get("species", "Columba livia"),
            })

        total = data.get("count", 0)
        print(f"  Descargadas: {len(observaciones)}/{total}")

        if offset + limit >= total or total == 0:
            break

        offset += limit
        time.sleep(0.5)

    output_path = os.path.join(os.path.dirname(__file__), "../data/palomas_gbif.json")
    with open(output_path, "w") as f:
        json.dump(observaciones, f, indent=2, ensure_ascii=False)

    print(f"\nTotal: {len(observaciones)} observaciones")
    print(f"Con hora: {sum(1 for o in observaciones if o['hora'] is not None)}")
    print(f"Guardadas en {output_path}")
    return observaciones

if __name__ == "__main__":
    descargar_gbif_kazan()