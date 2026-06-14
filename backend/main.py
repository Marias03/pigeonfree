from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from dotenv import load_dotenv
import httpx
import os

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    waypoints = [{"lat": c[1], "lng": c[0]} for c in coords]

    result = supabase.table("pigeon_zones").select("lat,lng,score").gte("score", 5).execute()
    zonas_peligrosas = result.data

    zonas_cruzadas = 0
    for wp in waypoints[::5]:
        for zona in zonas_peligrosas:
            if abs(wp["lat"] - zona["lat"]) < 0.002 and abs(wp["lng"] - zona["lng"]) < 0.002:
                zonas_cruzadas += 1
                break

    nivel_riesgo = "alto" if zonas_cruzadas >= 5 else "medio" if zonas_cruzadas >= 2 else "bajo"

    return {
        "waypoints": waypoints,
        "zonas_cruzadas": zonas_cruzadas,
        "nivel_riesgo": nivel_riesgo,
        "distancia_m": osrm_data["routes"][0]["distance"],
        "duracion_s": osrm_data["routes"][0]["duration"],
    }

@app.get("/health")
async def health():
    return {"status": "ok"}