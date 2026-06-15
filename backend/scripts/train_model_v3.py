import json
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error
import pickle
from math import radians, sin, cos, sqrt, atan2

def distancia_km(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def contar_cercanos(lat, lng, elementos, radio_km=0.3):
    return sum(1 for el in elementos if distancia_km(lat, lng, el["lat"], el["lng"]) < radio_km)

def cargar_features_urbanas():
    path = os.path.join(os.path.dirname(__file__), "../data/urban_features.json")
    with open(path) as f:
        return json.load(f)

def cargar_todos_los_datos(urban):
    rows = []
    base = os.path.join(os.path.dirname(__file__), "../data")

    # iNaturalist
    try:
        with open(f"{base}/palomas_validadas_v2.json") as f:
            inat = json.load(f)
        for obs in inat:
            if not obs.get("fecha"):
                continue
            try:
                fecha = pd.to_datetime(obs["fecha"])
                lat, lng = obs["lat"], obs["lng"]
                rows.append({
                    "lat": lat, "lng": lng,
                    "hora_categoria": 1,
                    "dia_semana": fecha.dayofweek,
                    "mes": fecha.month,
                    "es_fin_de_semana": 1 if fecha.dayofweek >= 5 else 0,
                    "es_verano": 1 if fecha.month in [6, 7, 8] else 0,
                    "parques_cercanos": contar_cercanos(lat, lng, urban.get("parques", [])),
                    "restaurantes_cercanos": contar_cercanos(lat, lng, urban.get("restaurantes", [])),
                    "estaciones_cercanas": contar_cercanos(lat, lng, urban.get("estaciones", [])),
                    "plazas_cercanas": contar_cercanos(lat, lng, urban.get("plazas", [])),
                    "basura_cercana": contar_cercanos(lat, lng, urban.get("basura", [])),
                    "mercados_cercanos": contar_cercanos(lat, lng, urban.get("mercados", [])),
                    "cantidad": 1,
                })
            except:
                continue
        print(f"iNaturalist: {len([r for r in rows])} obs")
    except Exception as e:
        print(f"Error iNaturalist: {e}")

    # eBird
    try:
        with open(f"{base}/palomas_ebird.json") as f:
            ebird = json.load(f)
        count_before = len(rows)
        for obs in ebird:
            if not obs.get("fecha"):
                continue
            try:
                fecha_str = obs["fecha"].split(" ")[0]
                fecha = pd.to_datetime(fecha_str)
                hora = obs.get("hora") or 10
                hora_cat = 0 if hora < 7 else 1 if hora < 12 else 2 if hora < 17 else 3 if hora < 21 else 4
                lat, lng = obs["lat"], obs["lng"]
                rows.append({
                    "lat": lat, "lng": lng,
                    "hora_categoria": hora_cat,
                    "dia_semana": fecha.dayofweek,
                    "mes": fecha.month,
                    "es_fin_de_semana": 1 if fecha.dayofweek >= 5 else 0,
                    "es_verano": 1 if fecha.month in [6, 7, 8] else 0,
                    "parques_cercanos": contar_cercanos(lat, lng, urban.get("parques", [])),
                    "restaurantes_cercanos": contar_cercanos(lat, lng, urban.get("restaurantes", [])),
                    "estaciones_cercanas": contar_cercanos(lat, lng, urban.get("estaciones", [])),
                    "plazas_cercanas": contar_cercanos(lat, lng, urban.get("plazas", [])),
                    "basura_cercana": contar_cercanos(lat, lng, urban.get("basura", [])),
                    "mercados_cercanos": contar_cercanos(lat, lng, urban.get("mercados", [])),
                    "cantidad": obs.get("cantidad") or 1,
                })
            except:
                continue
        print(f"eBird: {len(rows) - count_before} obs")
    except Exception as e:
        print(f"Error eBird: {e}")

    df = pd.DataFrame(rows)
    print(f"\nTotal: {len(df)} observaciones")
    return df

def entrenar_modelo(df):
    df["lat_grid"] = (df["lat"] / 0.005).round() * 0.005
    df["lng_grid"] = (df["lng"] / 0.005).round() * 0.005

    features = [
        "lat_grid", "lng_grid", "hora_categoria",
        "dia_semana", "mes", "es_fin_de_semana", "es_verano",
        "parques_cercanos", "restaurantes_cercanos", "estaciones_cercanas",
        "plazas_cercanas", "basura_cercana", "mercados_cercanos",
    ]

    X = df[features]
    y = df["cantidad"]

    modelo = RandomForestRegressor(n_estimators=200, random_state=42, max_depth=10)
    
    scores = cross_val_score(modelo, X, y, cv=5, scoring="neg_mean_squared_error")
    rmse_cv = np.sqrt(-scores.mean())
    print(f"RMSE cross-validation: {rmse_cv:.2f}")

    modelo.fit(X, y)
    print("\nFeature importances:")
    for feat, imp in sorted(zip(features, modelo.feature_importances_), key=lambda x: -x[1]):
        print(f"  {feat}: {imp:.3f}")

    return modelo, features

def guardar_modelo(modelo, features):
    base = os.path.join(os.path.dirname(__file__), "../data")
    with open(f"{base}/modelo_palomas_v3.pkl", "wb") as f:
        pickle.dump({"modelo": modelo, "features": features}, f)
    print(f"\nModelo v3 guardado")

if __name__ == "__main__":
    print("Cargando features urbanas...")
    urban = cargar_features_urbanas()
    for k, v in urban.items():
        print(f"  {k}: {len(v)} elementos")
    
    print("\nCargando observaciones...")
    df = cargar_todos_los_datos(urban)
    
    print("\nEntrenando modelo...")
    modelo, features = entrenar_modelo(df)
    guardar_modelo(modelo, features)
    print("✅ Listo!")