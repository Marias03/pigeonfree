import json
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import pickle
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

def cargar_datos():
    input_path = os.path.join(os.path.dirname(__file__), "../data/palomas_validadas_v2.json")
    with open(input_path) as f:
        observaciones = json.load(f)

    print(f"Total observaciones: {len(observaciones)}")

    rows = []
    for obs in observaciones:
        if not obs.get("fecha"):
            continue
        try:
            fecha = pd.to_datetime(obs["fecha"])
            rows.append({
                "lat": obs["lat"],
                "lng": obs["lng"],
                "hora": 12,  # iNaturalist no siempre tiene hora exacta
                "dia_semana": fecha.dayofweek,
                "mes": fecha.month,
                "es_fin_de_semana": 1 if fecha.dayofweek >= 5 else 0,
                "epoca": 1 if fecha.month in [6, 7, 8] else 0,  # verano
            })
        except:
            continue

    df = pd.DataFrame(rows)
    print(f"Datos procesados: {len(df)} filas")
    return df

def entrenar_modelo(df):
    # Agregamos por zona (grid de 0.01 grados)
    df["lat_grid"] = (df["lat"] / 0.01).round() * 0.01
    df["lng_grid"] = (df["lng"] / 0.01).round() * 0.01

    zona_counts = df.groupby(["lat_grid", "lng_grid", "dia_semana", "mes", "es_fin_de_semana", "epoca"]).size().reset_index(name="count")

    features = ["lat_grid", "lng_grid", "dia_semana", "mes", "es_fin_de_semana", "epoca"]
    X = zona_counts[features]
    y = zona_counts["count"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    modelo = RandomForestRegressor(n_estimators=100, random_state=42)
    modelo.fit(X_train, y_train)

    y_pred = modelo.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    print(f"RMSE: {rmse:.2f}")
    print(f"Feature importances:")
    for feat, imp in zip(features, modelo.feature_importances_):
        print(f"  {feat}: {imp:.3f}")

    return modelo

def guardar_modelo(modelo):
    output_path = os.path.join(os.path.dirname(__file__), "../data/modelo_palomas.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(modelo, f)
    print(f"Modelo guardado en {output_path}")

if __name__ == "__main__":
    df = cargar_datos()
    modelo = entrenar_modelo(df)
    guardar_modelo(modelo)
    print("✅ Listo!")