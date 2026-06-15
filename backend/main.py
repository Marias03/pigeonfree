from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2, pi
import httpx
import os
import pickle
import json
import pandas as pd
import numpy as np

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

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

modelo_path = os.path.join(os.path.dirname(__file__), "data/modelo_palomas_v5.pkl")
try:
    with open(modelo_path, "rb") as f:
        modelo_data = pickle.load(f)
        modelo_palomas = modelo_data["modelo"]
        modelo_features = modelo_data["features"]
    print("✅ Modelo ML v5 cargado")
except Exception as e:
    modelo_palomas = None
    modelo_features = []
    print(f"⚠️ Modelo ML no encontrado: {e}")

urban_path = os.path.join(os.path.dirname(__file__), "data/urban_features.json")
try:
    with open(urban_path) as f:
        urban_features = json.load(f)
    print("✅ Features urbanas cargadas")
except:
    urban_features = {}
    print("⚠️ Features urbanas no encontradas")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

clima_cache = {"data": None, "timestamp": None}

async def get_clima_actual():
    ahora = datetime.now()
    if clima_cache["timestamp"] and (ahora - clima_cache["timestamp"]).seconds < 1800:
        return clima_cache["data"]

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": 55.8304,
                    "longitude": 49.0661,
                    "current": "temperature_2m,precipitation,rain,snowfall,windspeed_10m,relativehumidity_2m",
                    "timezone": "Europe/Moscow",
                },
                timeout=10,
            )
            data = resp.json()
        current = data.get("current", {})
        clima = {
            "temperatura": current.get("temperature_2m", 15.0),
            "precipitacion": current.get("precipitation", 0.0),
            "lluvia": current.get("rain", 0.0),
            "nieve": current.get("snowfall", 0.0),
            "viento": current.get("windspeed_10m", 5.0),
            "humedad": current.get("relativehumidity_2m", 70.0),
        }
        clima_cache["data"] = clima
        clima_cache["timestamp"] = ahora
        return clima
    except:
        return {"temperatura": 15.0, "precipitacion": 0.0, "lluvia": 0.0, "nieve": 0.0, "viento": 5.0, "humedad": 70.0}

def predecir_riesgo(lat, lng, hora, mes, dia_semana, clima=None):
    if not modelo_palomas:
        return 0.5, "medio"

    if not clima:
        clima = {"temperatura": 15.0, "precipitacion": 0.0, "viento": 5.0, "humedad": 70.0}

    temp = clima.get("temperatura") or 15.0
    prec = clima.get("precipitacion") or 0.0
    viento = clima.get("viento") or 5.0
    humedad = clima.get("humedad") or 70.0

    feats = {
        "dia_semana": dia_semana,
        "es_fin_de_semana": int(dia_semana >= 5),
        "temp": temp,
        "precipitacion": prec,
        "viento": viento,
        "humedad": humedad,
        "llueve": 1 if prec > 0.5 else 0,
        "nieva": 1 if temp < 0 and prec > 0 else 0,
    }
    feats.update(features_temporales(hora, mes))
    feats.update(features_urbanas(lat, lng, urban_features))

    df = pd.DataFrame([feats])[modelo_features]
    prob = float(modelo_palomas.predict_proba(df)[0][1])
    nivel = "alto" if prob >= 0.6 else "medio" if prob >= 0.35 else "bajo"
    return prob, nivel

@app.get("/geocode")
async def geocode(q: str, lang: str = "es"):
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": YANDEX_API_KEY,
        "geocode": f"{q}, Казань",
        "format": "json",
        "lang": "ru_RU",
        "ll": "49.1,55.8",
        "spn": "0.5,0.3",
        "results": 1,
    }
    headers = {"User-Agent": "PigeonFree/1.0", "Accept-Language": lang}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, headers=headers)
        data = resp.json()

    try:
        members = data["response"]["GeoObjectCollection"]["featureMember"]
        if not members:
            return {"error": "No se encontró la dirección"}
        pos = members[0]["GeoObject"]["Point"]["pos"]
        lng, lat = map(float, pos.split())
        name = members[0]["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["text"]
        return {"lat": lat, "lng": lng, "display_name": name}
    except Exception as e:
        return {"error": str(e)}

@app.get("/zones")
async def get_zones():
    all_zones = []
    page_size = 1000
    offset = 0

    while True:
        result = supabase.table("pigeon_zones").select("lat,lng,score").range(offset, offset + page_size - 1).execute()
        batch = result.data
        if not batch:
            break
        all_zones.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size

    ahora = datetime.now()
    clima = await get_clima_actual()
    zones = []
    for z in all_zones:
        prob, nivel = predecir_riesgo(
            z["lat"], z["lng"],
            ahora.hour, ahora.month, ahora.weekday(),
            clima
        )
        zones.append({
            "lat": z["lat"],
            "lng": z["lng"],
            "score": z["score"],
            "nivel": nivel,
            "probabilidad": round(prob, 3),
        })
    return {"zones": zones}

@app.get("/route")
async def get_route(
    from_lat: float,
    from_lng: float,
    to_lat: float,
    to_lng: float,
):
    osrm_url = f"http://127.0.0.1:5001/route/v1/foot/{from_lng},{from_lat};{to_lng},{to_lat}"
    params = {"overview": "full", "geometries": "geojson", "steps": "false"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(osrm_url, params=params, timeout=10)
        osrm_data = resp.json()

    if osrm_data.get("code") != "Ok":
        return {"error": "No se pudo calcular la ruta"}

    coords = osrm_data["routes"][0]["geometry"]["coordinates"]
    route_waypoints = [{"lat": c[1], "lng": c[0]} for c in coords]

    ahora = datetime.now()
    clima = await get_clima_actual()
    probs = []
    for wp in route_waypoints[::5]:
        prob, _ = predecir_riesgo(wp["lat"], wp["lng"], ahora.hour, ahora.month, ahora.weekday(), clima)
        probs.append(prob)

    prob_media = float(np.mean(probs)) if probs else 0.5
    nivel_riesgo = "alto" if prob_media >= 0.6 else "medio" if prob_media >= 0.35 else "bajo"

    return {
        "waypoints": route_waypoints,
        "probabilidad_media": round(prob_media, 3),
        "nivel_riesgo": nivel_riesgo,
        "distancia_m": osrm_data["routes"][0]["distance"],
        "duracion_s": osrm_data["routes"][0]["duration"],
    }

@app.get("/predict")
async def predict_risk(lat: float, lng: float):
    ahora = datetime.now()
    clima = await get_clima_actual()
    prob, nivel = predecir_riesgo(lat, lng, ahora.hour, ahora.month, ahora.weekday(), clima)
    urban = features_urbanas(lat, lng, urban_features)
    temporal = features_temporales(ahora.hour, ahora.month)

    return {
        "lat": lat,
        "lng": lng,
        "probabilidad": round(prob, 3),
        "nivel": nivel,
        "hora": ahora.hour,
        "dia": ahora.strftime("%A"),
        "mes": ahora.month,
        "hora_sin": round(temporal["hora_sin"], 3),
        "hora_cos": round(temporal["hora_cos"], 3),
        "restaurantes_1km": urban.get("restaurantes_1000m", 0),
        "estaciones_1km": urban.get("estaciones_1000m", 0),
        "basura_1km": urban.get("basura_1000m", 0),
        "parques_1km": urban.get("parques_1000m", 0),
        "clima": clima,
    }

@app.get("/weather")
async def get_weather():
    return await get_clima_actual()

@app.get("/health")
async def health():
    return {"status": "ok"}