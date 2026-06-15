import json
import os
import random
import pandas as pd
from math import radians, sin, cos, sqrt, atan2

def distancia_km(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def generar_pseudoausencias():
    base = os.path.join(os.path.dirname(__file__), "../data")

    # Cargar positivos
    positivos = []
    for fname in ["palomas_validadas_v2.json", "palomas_ebird.json", "palomas_ebird_historic.json"]:
        try:
            with open(f"{base}/{fname}") as f:
                data = json.load(f)
                for obs in data:
                    if obs.get("lat") and obs.get("lng"):
                        positivos.append((obs["lat"], obs["lng"]))
        except:
            continue

    print(f"Positivos cargados: {len(positivos)}")

    # Bounding box de Kazán
    LAT_MIN, LAT_MAX = 55.65, 56.05
    LNG_MIN, LNG_MAX = 48.85, 49.45

    # Generar pseudoausencias — puntos aleatorios lejos de positivos
    negativos = []
    intentos = 0
    radio_exclusion_km = 0.2  # al menos 200m de un positivo

    while len(negativos) < len(positivos) * 2 and intentos < 50000:
        intentos += 1
        lat = random.uniform(LAT_MIN, LAT_MAX)
        lng = random.uniform(LNG_MIN, LNG_MAX)

        # Verificar que está lejos de todos los positivos
        demasiado_cerca = any(
            distancia_km(lat, lng, plat, plng) < radio_exclusion_km
            for plat, plng in positivos
        )

        if not demasiado_cerca:
            # Fecha aleatoria de los últimos 3 años
            fecha = pd.Timestamp("2022-01-01") + pd.Timedelta(days=random.randint(0, 1095))
            hora = random.randint(0, 23)
            negativos.append({
                "lat": lat,
                "lng": lng,
                "fecha": fecha.strftime("%Y-%m-%d"),
                "hora": hora,
                "cantidad": 0,  # negativo = 0 palomas
                "es_negativo": True,
            })

    print(f"Pseudoausencias generadas: {len(negativos)}")

    output_path = f"{base}/pseudoausencias.json"
    with open(output_path, "w") as f:
        json.dump(negativos, f, indent=2)

    print(f"Guardadas en {output_path}")
    return negativos

if __name__ == "__main__":
    generar_pseudoausencias()