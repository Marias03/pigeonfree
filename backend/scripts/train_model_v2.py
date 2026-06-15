import json
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import pickle

def cargar_todos_los_datos():
    rows = []
    base = os.path.join(os.path.dirname(__file__), "../data")

    try:
        with open(f"{base}/palomas_validadas_v2.json") as f:
            inat = json.load(f)
        for obs in inat:
            if not obs.get("fecha"):
                continue
            try:
                fecha = pd.to_datetime(obs["fecha"])
                rows.append({
                    "lat": obs["lat"],
                    "lng": obs["lng"],
                    "hora": 10,
                    "dia_semana": fecha.dayofweek,
                    "mes": fecha.month,
                    "es_fin_de_semana": 1 if fecha.dayofweek >= 5 else 0,
                    "es_verano": 1 if fecha.month in [6, 7, 8] else 0,
                    "cantidad": 1,
                    "fuente": "inat",
                })
            except:
                continue
        print(f"iNaturalist: {len([r for r in rows if r['fuente'] == 'inat'])} obs")
    except Exception as e:
        print(f"Error iNaturalist: {e}")

    try:
        with open(f"{base}/palomas_ebird.json") as f:
            ebird = json.load(f)
        for obs in ebird:
            if not obs.get("fecha"):
                continue
            try:
                fecha_str = obs["fecha"].split(" ")[0]
                fecha = pd.to_datetime(fecha_str)
                rows.append({
                    "lat": obs["lat"],
                    "lng": obs["lng"],
                    "hora": obs.get("hora") or 10,
                    "dia_semana": fecha.dayofweek,
                    "mes": fecha.month,
                    "es_fin_de_semana": 1 if fecha.dayofweek >= 5 else 0,
                    "es_verano": 1 if fecha.month in [6, 7, 8] else 0,
                    "cantidad": obs.get("cantidad") or 1,
                    "fuente": "ebird",
                })
            except:
                continue
        print(f"eBird: {len([r for r in rows if r['fuente'] == 'ebird'])} obs")
    except Exception as e:
        print(f"Error eBird: {e}")

    df = pd.DataFrame(rows)
    print(f"\nTotal combinado: {len(df)} observaciones")
    return df

def entrenar_modelo(df):
    df["lat_grid"] = (df["lat"] / 0.005).round() * 0.005
    df["lng_grid"] = (df["lng"] / 0.005).round() * 0.005
    df["hora_categoria"] = pd.cut(df["hora"],
        bins=[0, 7, 12, 17, 21, 24],
        labels=[0, 1, 2, 3, 4],
        include_lowest=True
    ).astype(int)

    zona_counts = df.groupby([
        "lat_grid", "lng_grid", "hora_categoria",
        "dia_semana", "mes", "es_fin_de_semana", "es_verano"
    ]).agg({"cantidad": "sum"}).reset_index()

    features = ["lat_grid", "lng_grid", "hora_categoria", "dia_semana", "mes", "es_fin_de_semana", "es_verano"]
    X = zona_counts[features]
    y = zona_counts["cantidad"]

    if len(X) < 10:
        modelo = RandomForestRegressor(n_estimators=100, random_state=42)
        modelo.fit(X, y)
        print("Modelo entrenado sin split")
        return modelo

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    modelo = RandomForestRegressor(n_estimators=100, random_state=42)
    modelo.fit(X_train, y_train)

    y_pred = modelo.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    print(f"\nRMSE: {rmse:.2f}")
    print("Feature importances:")
    for feat, imp in zip(features, modelo.feature_importances_):
        print(f"  {feat}: {imp:.3f}")

    return modelo

def guardar_modelo(modelo):
    output_path = os.path.join(os.path.dirname(__file__), "../data/modelo_palomas_v2.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(modelo, f)
    print(f"\nModelo guardado en {output_path}")

if __name__ == "__main__":
    df = cargar_todos_los_datos()
    modelo = entrenar_modelo(df)
    guardar_modelo(modelo)
    print("✅ Listo!")