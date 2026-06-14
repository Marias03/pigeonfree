from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime
import httpx
import os
import pickle
import pandas as pd

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

modelo_path = os.path.join(os.path.dirname(__file__), "data/modelo_palomas.pkl")
try:
    with open(modelo_path, "rb") as f:
        modelo_palomas = pickle.load(f)
    print("✅ Modelo ML cargado")
except:
    modelo_palomas = None
    print("⚠️ Modelo ML no encontrado")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    result = supabase.table("pigeon_zones").select("lat,lng,score").gte("score", 10).execute()
    zonas_peligrosas = result.data

    def distancia(lat1, lng1, lat2, lng2):
        return ((lat1 - lat2) ** 2 + (lng1 - lng2) ** 2) ** 0.5

    def punto_en_zona(lat, lng, radio=0.003):
        for zona in zonas_peligrosas:
            if distancia(lat, lng, zona["lat"], zona["lng"]) < radio:
                return zona
        return None

    def punto_seguro_alrededor(zona, lat_dir, lng_dir):
        radio = 0.004
        candidatos = [
            (zona["lat"] + radio, zona["lng"]),
            (zona["lat"] - radio, zona["lng"]),
            (zona["lat"], zona["lng"] + radio),
            (zona["lat"], zona["lng"] - radio),
            (zona["lat"] + radio, zona["lng"] + radio),
            (zona["lat"] - radio, zona["lng"] - radio),
            (zona["lat"] + radio, zona["lng"] - radio),
            (zona["lat"] - radio, zona["lng"] + radio),
        ]
        mejor = None
        mejor_dist = float("inf")
        for c in candidatos:
            if punto_en_zona(c[0], c[1]):
                continue
            d = distancia(c[0], c[1], lat_dir, lng_dir)
            if d < mejor_dist:
                mejor_dist = d
                mejor = c
        return mejor

    waypoints_coords = [(from_lat, from_lng)]
    pasos = 10
    zonas_vistas = set()

    for i in range(1, pasos):
        t = i / pasos
        lat = from_lat + t * (to_lat - from_lat)
        lng = from_lng + t * (to_lng - from_lng)

        zona = punto_en_zona(lat, lng)
        if zona:
            zona_id = (round(zona["lat"], 4), round(zona["lng"], 4))
            if zona_id not in zonas_vistas:
                zonas_vistas.add(zona_id)
                desvio = punto_seguro_alrededor(zona, to_lat, to_lng)
                if desvio:
                    waypoints_coords.append(desvio)

    waypoints_coords.append((to_lat, to_lng))

    coords_str = ";".join([f"{lng},{lat}" for lat, lng in waypoints_coords])
    osrm_url = f"http://127.0.0.1:5001/route/v1/foot/{coords_str}"
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

    zonas_cruzadas = 0
    for wp in route_waypoints[::5]:
        if punto_en_zona(wp["lat"], wp["lng"]):
            zonas_cruzadas += 1

    nivel_riesgo = "alto" if zonas_cruzadas >= 5 else "medio" if zonas_cruzadas >= 2 else "bajo"

    if modelo_palomas:
        ahora = datetime.now()
        features_list = []
        for wp in route_waypoints[::10]:
            features_list.append({
                "lat_grid": round(wp["lat"] / 0.01) * 0.01,
                "lng_grid": round(wp["lng"] / 0.01) * 0.01,
                "dia_semana": ahora.weekday(),
                "mes": ahora.month,
                "es_fin_de_semana": 1 if ahora.weekday() >= 5 else 0,
                "epoca": 1 if ahora.month in [6, 7, 8] else 0,
            })
        if features_list:
            df = pd.DataFrame(features_list)
            scores = modelo_palomas.predict(df)
            riesgo_ml = float(scores.mean())
            nivel_riesgo = "alto" if riesgo_ml >= 3 else "medio" if riesgo_ml >= 1.5 else "bajo"

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
    features = pd.DataFrame([{
        "lat_grid": round(lat / 0.01) * 0.01,
        "lng_grid": round(lng / 0.01) * 0.01,
        "dia_semana": ahora.weekday(),
        "mes": ahora.month,
        "es_fin_de_semana": 1 if ahora.weekday() >= 5 else 0,
        "epoca": 1 if ahora.month in [6, 7, 8] else 0,
    }])

    score = float(modelo_palomas.predict(features)[0])
    nivel = "alto" if score >= 3 else "medio" if score >= 1.5 else "bajo"

    return {
        "lat": lat,
        "lng": lng,
        "score_predicho": round(score, 2),
        "nivel": nivel,
        "hora": ahora.hour,
        "dia": ahora.strftime("%A"),
    }

@app.get("/health")
async def health():
    return {"status": "ok"}