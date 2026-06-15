import osmnx as ox
import networkx as nx
import pickle
import os
import json
import pandas as pd
from math import radians, sin, cos, sqrt, atan2, pi
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

def distancia_km(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def contar_cercanos(lat, lng, elementos, radio_km):
    return sum(1 for el in elementos if distancia_km(lat, lng, el["lat"], el["lng"]) < radio_km)

def features_urbanas(lat, lng, urban):
    feats = {}
    for tipo in ["parques", "restaurantes", "estaciones", "plazas", "basura", "mercados"]:
        elementos = urban.get(tipo, [])
        for radio in [0.1, 0.3, 0.5, 1.0]:
            feats[f"{tipo}_{int(radio*1000)}m"] = contar_cercanos(lat, lng, elementos, radio)
    return feats

def features_temporales(hora, mes):
    return {
        "hora_sin": sin(2 * pi * hora / 24),
        "hora_cos": cos(2 * pi * hora / 24),
        "mes_sin": sin(2 * pi * mes / 12),
        "mes_cos": cos(2 * pi * mes / 12),
    }

def build_graph():
    base = os.path.join(os.path.dirname(__file__), "../data")

    print("Cargando modelo ML y features urbanas...")
    with open(f"{base}/modelo_palomas_v5.pkl", "rb") as f:
        modelo_data = pickle.load(f)
        modelo = modelo_data["modelo"]
        features = modelo_data["features"]

    with open(f"{base}/urban_features.json") as f:
        urban = json.load(f)

    print("Descargando grafo de calles peatonales de Kazán...")
    G = ox.graph_from_place("Казань, Россия", network_type="walk")
    print(f"Grafo descargado: {len(G.nodes)} nodos, {len(G.edges)} aristas")

    print("Calculando riesgo ML para cada segmento...")
    from datetime import datetime
    ahora = datetime.now()
    hora = ahora.hour
    hora_cat = 0 if hora < 7 else 1 if hora < 12 else 2 if hora < 17 else 3 if hora < 21 else 4
    mes = ahora.month
    dia = ahora.weekday()

    clima_default = {
        "temp": 15.0, "precipitacion": 0.0,
        "viento": 5.0, "humedad": 70.0,
        "llueve": 0, "nieva": 0,
    }

    procesados = 0
    for u, v, data in G.edges(data=True):
        lat_u = G.nodes[u]["y"]
        lng_u = G.nodes[u]["x"]
        lat_v = G.nodes[v]["y"]
        lng_v = G.nodes[v]["x"]

        lat_mid = (lat_u + lat_v) / 2
        lng_mid = (lng_u + lng_v) / 2

        feats = {
            "dia_semana": dia,
            "es_fin_de_semana": int(dia >= 5),
            **clima_default,
        }
        feats.update(features_temporales(hora, mes))
        feats.update(features_urbanas(lat_mid, lng_mid, urban))

        df = pd.DataFrame([feats])[features]
        prob = float(modelo.predict_proba(df)[0][1])

        tiempo_base = data.get("length", 1) / 1.4  # velocidad peatonal ~1.4 m/s

        data["pigeon_risk"] = prob
        data["tiempo_base"] = tiempo_base
        data["coste_balanced"] = tiempo_base * (1 + 0.5 * prob)
        data["coste_pigeon_free"] = tiempo_base * (1 + 3.0 * prob)

        procesados += 1
        if procesados % 1000 == 0:
            print(f"  Procesados: {procesados}/{len(G.edges())}")

    output_path = f"{base}/kazan_pigeon_graph.pkl"
    with open(output_path, "wb") as f:
        pickle.dump(G, f)

    print(f"\nGrafo guardado en {output_path}")
    print(f"Total segmentos procesados: {procesados}")
    return G

if __name__ == "__main__":
    build_graph()
    print("✅ Listo!")