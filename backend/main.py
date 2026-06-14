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
    result = supabase.table("pigeon_zones").select("lat,lng,score").execute()
    zones = []
    for z in result.data:
        score = z["score"]
        if score >= 10:
            nivel = "alto"
        elif score >= 3:
            nivel = "medio"
        else:
            nivel = "bajo"
        zones.append({**z, "nivel": nivel})
    return {"zones": zones}

@app.get("/health")
async def health():
    return {"status": "ok"}