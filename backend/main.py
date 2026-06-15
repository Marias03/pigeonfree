from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
import httpx
import os
import pickle
import json
import pandas as pd

def distancia_km(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def contar_cercanos(lat, lng, elementos, radio_km=0.3):
    return sum(1 for el in elementos if distancia_km(lat, lng, el["lat"], el["lng"]) < radio_km)

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

modelo_path = os.path.join(os.path.dirname(__file__), "data/modelo_palomas_v3.pkl")
try:
    with open(modelo_path, "rb") as f:
        modelo_data = pickle.load(f)
        modelo_palomas = modelo_data["modelo"]
        modelo_features = modelo_data["features"]
    print("✅ Modelo ML v3 cargado")
except:
    modelo_palomas = None
    modelo_features = []
    print("⚠️ Modelo ML no encontrado")

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

def get_urban_counts(lat, lng):
    return {
        "parques_cercanos": contar_cercanos(lat, lng, urban_features.get("parques", [])),
        "restaurantes_cercanos": contar_cercanos(lat, lng, urban_features.get("restaurantes", [])),
        "estaciones_cercanas": contar_cercanos(lat, lng, urban_features.get("estaciones", [])),
        "plazas_cercanas": contar_cercanos(lat, lng, urban_features.get("plazas", [])),
        "basura_cercana": contar_cercanos(lat, lng, urban_features.get("basura", [])),
        "mercados_cercanos": contar_cercanos(lat, lng, urban_features.get("mercados", [])),
    }

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
    headers = {
        "User-Agent": "PigeonFree/1.0",
        "Accept-Language": lang,
    }

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

    zones = []
    for z in all_zones:
        score = z["score"]
        if score >= 10:
            nivel = "alto"
        elif score >= 3:
            nivel = "medio"
        else:
            nivel = "bajo"
        zones.append({**z, "nivel": nivel})
    return {"zones": zones}

@app.get("/route")
async def get_route(
    from_lat: float,
    from_lng: float,
    to_lat: float,
    to_lng: float,
):
    osrm_url = f"http://127.0.0.1:5001/route/v1/foot/{from_lng},{from_lat};{to_lng},{to_lat}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(osrm_url, params=params, timeout=10)
        osrm_data = resp.json()

    if osrm_data.get("code") != "Ok":
        return {"error": "No se pudo calcular la ruta"}

    coords = osrm_data["routes"][0]["geometry"]["coordinates"]
    route_waypoints = [{"lat": c[1], "lng": c[0]} for c in coords]

    result = supabase.table("pigeon_zones").select("lat,lng,score").gte("score", 5).execute()
    zonas_peligrosas = result.data

    zonas_cruzadas = 0
    for wp in route_waypoints[::5]:
        for zona in zonas_peligrosas:
            if abs(wp["lat"] - zona["lat"]) < 0.002 and abs(wp["lng"] - zona["lng"]) < 0.002:
                zonas_cruzadas += 1
                break

    nivel_riesgo = "bajo"
    if modelo_palomas:
        ahora = datetime.now()
        hora = ahora.hour
        hora_cat = 0 if hora < 7 else 1 if hora < 12 else 2 if hora < 17 else 3 if hora < 21 else 4

        features_list = []
        for wp in route_waypoints[::10]:
            urban = get_urban_counts(wp["lat"], wp["lng"])
            features_list.append({
                "lat_grid": round(wp["lat"] / 0.005) * 0.005,
                "lng_grid": round(wp["lng"] / 0.005) * 0.005,
                "hora_categoria": hora_cat,
                "dia_semana": ahora.weekday(),
                "mes": ahora.month,
                "es_fin_de_semana": 1 if ahora.weekday() >= 5 else 0,
                "es_verano": 1 if ahora.month in [6, 7, 8] else 0,
                **urban,
            })

        if features_list:
            df = pd.DataFrame(features_list)[modelo_features]
            scores = modelo_palomas.predict(df)
            riesgo_ml = float(scores.mean())
            nivel_riesgo = "alto" if riesgo_ml >= 3 else "medio" if riesgo_ml >= 1.5 else "bajo"
    else:
        nivel_riesgo = "alto" if zonas_cruzadas >= 5 else "medio" if zonas_cruzadas >= 2 else "bajo"

    return {
        "waypoints": route_waypoints,
        "zonas_cruzadas": zonas_cruzadas,
        "nivel_riesgo": nivel_riesgo,
        "distancia_m": osrm_data["routes"][0]["distance"],
        "duracion_s": osrm_data["routes"][0]["duration"],
    }

@app.get("/predict")
async def predict_risk(lat: float, lng: float):
    if not modelo_palomas:
        return {"error": "Modelo no disponible"}

    ahora = datetime.now()
    hora = ahora.hour
    hora_cat = 0 if hora < 7 else 1 if hora < 12 else 2 if hora < 17 else 3 if hora < 21 else 4

    urban = get_urban_counts(lat, lng)

    features = pd.DataFrame([{
        "lat_grid": round(lat / 0.005) * 0.005,
        "lng_grid": round(lng / 0.005) * 0.005,
        "hora_categoria": hora_cat,
        "dia_semana": ahora.weekday(),
        "mes": ahora.month,
        "es_fin_de_semana": 1 if ahora.weekday() >= 5 else 0,
        "es_verano": 1 if ahora.month in [6, 7, 8] else 0,
        **urban,
    }])[modelo_features]

    score = float(modelo_palomas.predict(features)[0])
    nivel = "alto" if score >= 3 else "medio" if score >= 1.5 else "bajo"

    return {
        "lat": lat,
        "lng": lng,
        "score_predicho": round(score, 2),
        "nivel": nivel,
        "hora": hora,
        "hora_categoria": hora_cat,
        "dia": ahora.strftime("%A"),
        "es_verano": ahora.month in [6, 7, 8],
        **urban,
    }

@app.get("/health")
async def health():
    return {"status": "ok"}