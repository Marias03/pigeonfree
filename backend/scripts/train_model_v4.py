import json
import os
import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2, pi
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, log_loss
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

def cargar_urban():
    path = os.path.join(os.path.dirname(__file__), "../data/urban_features.json")
    with open(path) as f:
        return json.load(f)

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

def cargar_datos(urban):
    rows = []
    base = os.path.join(os.path.dirname(__file__), "../data")

    # Positivos
    for fname, hora_default in [
        ("palomas_validadas_v2.json", 10),
        ("palomas_ebird.json", None),
        ("palomas_ebird_historic.json", None),
    ]:
        try:
            with open(f"{base}/{fname}") as f:
                data = json.load(f)
            for obs in data:
                if not obs.get("fecha") or not obs.get("lat"):
                    continue
                try:
                    fecha = pd.to_datetime(obs["fecha"].split(" ")[0])
                    hora = obs.get("hora") or hora_default or 10
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
                    rows.append(row)
                except:
                    continue
            print(f"{fname}: {len(rows)} acumulados")
        except Exception as e:
            print(f"Error {fname}: {e}")

    # Negativos
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
                rows.append(row)
            except:
                continue
        print(f"Negativos: {len(rows) - count_before}")
    except Exception as e:
        print(f"Error negativos: {e}")

    df = pd.DataFrame(rows)
    print(f"\nTotal: {len(df)} filas | Positivos: {df['label'].sum()} | Negativos: {(df['label']==0).sum()}")
    return df

def entrenar_y_evaluar(df):
    feature_cols = [c for c in df.columns if c not in ["lat", "lng", "label", "grid"]]
    X = df[feature_cols].values
    y = df["label"].values
    groups = df["grid"].values

    print(f"\nFeatures: {len(feature_cols)}")
    print(feature_cols)

    # GroupKFold por grid
    gkf = GroupKFold(n_splits=5)

    modelos = {
        "RandomForest": RandomForestClassifier(n_estimators=300, max_depth=12, random_state=42, class_weight="balanced"),
        "LogisticRegression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
    }

    mejor_modelo = None
    mejor_auc = 0
    mejor_nombre = ""

    for nombre, modelo in modelos.items():
        aucs = []
        for train_idx, test_idx in gkf.split(X, y, groups):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            if nombre == "LogisticRegression":
                scaler = StandardScaler()
                X_train = scaler.fit_transform(X_train)
                X_test = scaler.transform(X_test)

            modelo.fit(X_train, y_train)
            probs = modelo.predict_proba(X_test)[:, 1]
            if len(np.unique(y_test)) > 1:
                aucs.append(roc_auc_score(y_test, probs))

        auc_mean = np.mean(aucs) if aucs else 0
        print(f"\n{nombre}:")
        print(f"  ROC-AUC (GroupKFold): {auc_mean:.3f}")

        if auc_mean > mejor_auc:
            mejor_auc = auc_mean
            mejor_nombre = nombre
            mejor_modelo = modelo

    # Reentrenar el mejor con calibración
    print(f"\nMejor modelo: {mejor_nombre} (AUC={mejor_auc:.3f})")
    print("Calibrando probabilidades...")

    modelo_calibrado = CalibratedClassifierCV(mejor_modelo, cv=3, method="isotonic")
    modelo_calibrado.fit(X, y)

    probs_calibradas = modelo_calibrado.predict_proba(X)[:, 1]
    print(f"  Brier score: {brier_score_loss(y, probs_calibradas):.3f}")
    print(f"  Log loss: {log_loss(y, probs_calibradas):.3f}")

    if hasattr(mejor_modelo, "feature_importances_"):
        print("\nFeature importances (top 10):")
        importances = sorted(zip(feature_cols, mejor_modelo.feature_importances_), key=lambda x: -x[1])
        for feat, imp in importances[:10]:
            print(f"  {feat}: {imp:.3f}")

    return modelo_calibrado, feature_cols

def guardar_modelo(modelo, features):
    base = os.path.join(os.path.dirname(__file__), "../data")
    with open(f"{base}/modelo_palomas_v4.pkl", "wb") as f:
        pickle.dump({"modelo": modelo, "features": features}, f)
    print(f"\nModelo v4 guardado ✅")

if __name__ == "__main__":
    print("Cargando features urbanas...")
    urban = cargar_urban()
    for k, v in urban.items():
        print(f"  {k}: {len(v)} elementos")

    print("\nCargando datos...")
    df = cargar_datos(urban)

    print("\nEntrenando y evaluando...")
    modelo, features = entrenar_y_evaluar(df)
    guardar_modelo(modelo, features)
    print("✅ Listo!")