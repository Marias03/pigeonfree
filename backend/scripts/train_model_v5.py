import json
import os
import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2, pi
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss
from sklearn.preprocessing import StandardScaler
import pickle

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

def features_clima(clima):
    if not clima:
        return {"temp": 15.0, "precipitacion": 0.0, "viento": 5.0, "humedad": 70.0, "llueve": 0, "nieva": 0}
    temp = clima.get("temperatura") or 15.0
    prec = clima.get("precipitacion") or 0.0
    viento = clima.get("viento") or 5.0
    humedad = clima.get("humedad") or 70.0
    return {
        "temp": temp,
        "precipitacion": prec,
        "viento": viento,
        "humedad": humedad,
        "llueve": 1 if prec > 0.5 else 0,
        "nieva": 1 if temp < 0 and prec > 0 else 0,
    }

def cargar_urban():
    path = os.path.join(os.path.dirname(__file__), "../data/urban_features.json")
    with open(path) as f:
        return json.load(f)

def cargar_datos(urban):
    rows = []
    base = os.path.join(os.path.dirname(__file__), "../data")

    # iNaturalist sin clima
    try:
        with open(f"{base}/palomas_validadas_v2.json") as f:
            inat = json.load(f)
        for obs in inat:
            if not obs.get("fecha") or not obs.get("lat"):
                continue
            try:
                fecha = pd.to_datetime(obs["fecha"])
                lat, lng = float(obs["lat"]), float(obs["lng"])
                row = {
                    "lat": lat, "lng": lng,
                    "dia_semana": fecha.dayofweek,
                    "es_fin_de_semana": int(fecha.dayofweek >= 5),
                    "label": 1,
                    "grid": f"{round(lat/0.01)*0.01}_{round(lng/0.01)*0.01}",
                }
                row.update(features_temporales(10, fecha.month))
                row.update(features_urbanas(lat, lng, urban))
                row.update(features_clima(None))
                rows.append(row)
            except:
                continue
        print(f"iNaturalist: {len(rows)} obs")
    except Exception as e:
        print(f"Error iNaturalist: {e}")

    # eBird con clima
    try:
        with open(f"{base}/palomas_con_clima.json") as f:
            ebird = json.load(f)
        count_before = len(rows)
        for obs in ebird:
            if not obs.get("fecha") or not obs.get("lat"):
                continue
            try:
                fecha = pd.to_datetime(obs["fecha"].split(" ")[0])
                hora = obs.get("hora") or 10
                lat, lng = float(obs["lat"]), float(obs["lng"])
                row = {
                    "lat": lat, "lng": lng,
                    "dia_semana": fecha.dayofweek,
                    "es_fin_de_semana": int(fecha.dayofweek >= 5),
                    "label": 1,
                    "grid": f"{round(lat/0.01)*0.01}_{round(lng/0.01)*0.01}",
                }
                row.update(features_temporales(hora, fecha.month))
                row.update(features_urbanas(lat, lng, urban))
                row.update(features_clima(obs.get("clima")))
                rows.append(row)
            except:
                continue
        print(f"eBird con clima: {len(rows) - count_before} obs")
    except Exception as e:
        print(f"Error eBird: {e}")

    # Pseudoausencias
    try:
        with open(f"{base}/pseudoausencias.json") as f:
            negativos = json.load(f)
        count_before = len(rows)
        for obs in negativos:
            try:
                fecha = pd.to_datetime(obs["fecha"])
                hora = obs.get("hora", 12)
                lat, lng = float(obs["lat"]), float(obs["lng"])
                row = {
                    "lat": lat, "lng": lng,
                    "dia_semana": fecha.dayofweek,
                    "es_fin_de_semana": int(fecha.dayofweek >= 5),
                    "label": 0,
                    "grid": f"{round(lat/0.01)*0.01}_{round(lng/0.01)*0.01}",
                }
                row.update(features_temporales(hora, fecha.month))
                row.update(features_urbanas(lat, lng, urban))
                row.update(features_clima(None))
                rows.append(row)
            except:
                continue
        print(f"Pseudoausencias: {len(rows) - count_before} obs")
    except Exception as e:
        print(f"Error pseudoausencias: {e}")

    df = pd.DataFrame(rows)
    print(f"\nTotal: {len(df)} | Positivos: {df['label'].sum()} | Negativos: {(df['label']==0).sum()}")
    return df

def entrenar(df):
    feature_cols = [c for c in df.columns if c not in ["lat", "lng", "label", "grid"]]
    X = df[feature_cols].values
    y = df["label"].values
    groups = df["grid"].values

    print(f"\nFeatures ({len(feature_cols)}):")
    print(feature_cols)

    gkf = GroupKFold(n_splits=5)

    modelo = RandomForestClassifier(
        n_estimators=300, max_depth=12,
        random_state=42, class_weight="balanced"
    )

    aucs = []
    for train_idx, test_idx in gkf.split(X, y, groups):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        modelo.fit(X_train, y_train)
        probs = modelo.predict_proba(X_test)[:, 1]
        if len(np.unique(y_test)) > 1:
            aucs.append(roc_auc_score(y_test, probs))

    print(f"ROC-AUC GroupKFold: {np.mean(aucs):.3f}")

    modelo_calibrado = CalibratedClassifierCV(modelo, cv=3, method="isotonic")
    modelo_calibrado.fit(X, y)

    probs_all = modelo_calibrado.predict_proba(X)[:, 1]
    print(f"Brier score: {brier_score_loss(y, probs_all):.3f}")
    print(f"Log loss: {log_loss(y, probs_all):.3f}")

    print("\nFeature importances (top 10):")
    importances = sorted(zip(feature_cols, modelo.feature_importances_), key=lambda x: -x[1])
    for feat, imp in importances[:10]:
        print(f"  {feat}: {imp:.3f}")

    return modelo_calibrado, feature_cols

def guardar(modelo, features):
    base = os.path.join(os.path.dirname(__file__), "../data")
    with open(f"{base}/modelo_palomas_v5.pkl", "wb") as f:
        pickle.dump({"modelo": modelo, "features": features}, f)
    print("\nModelo v5 guardado ✅")

if __name__ == "__main__":
    print("Cargando urban features...")
    urban = cargar_urban()
    for k, v in urban.items():
        print(f"  {k}: {len(v)}")

    print("\nCargando datos...")
    df = cargar_datos(urban)

    print("\nEntrenando...")
    modelo, features = entrenar(df)
    guardar(modelo, features)
    print("✅ Listo!")