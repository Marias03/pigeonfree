import csv
import os
import requests

OSRM_URL = "http://127.0.0.1:5001"
penalties_path = os.path.join(os.path.dirname(__file__), "../../osrm/penalties.csv")
output_path = os.path.join(os.path.dirname(__file__), "../../osrm/segment_speeds.csv")

with open(penalties_path) as f:
    reader = csv.DictReader(f)
    zonas = list(reader)

print(f"Procesando {len(zonas)} zonas...")

with open(output_path, "w", newline="") as out:
    writer = csv.writer(out)
  # Sin header — OSRM no lo acepta

    for zona in zonas:
        lat = float(zona["lat"])
        lng = float(zona["lon"])

        # Buscar el nodo más cercano en OSRM
        resp = requests.get(f"{OSRM_URL}/nearest/v1/foot/{lng},{lat}?number=3")
        data = resp.json()

        if data.get("code") != "Ok":
            continue

        for waypoint in data.get("waypoints", []):
            node_id = waypoint.get("nodes", [None, None])
            if node_id[0] and node_id[1]:
                writer.writerow([node_id[0], node_id[1], 1])
                writer.writerow([node_id[1], node_id[0], 1])

print(f"Guardado en {output_path}")