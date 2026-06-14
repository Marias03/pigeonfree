from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")

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
        "geocode": q,
        "format": "json",
        "lang": "ru_RU",
        "bbox": "48.8,55.6~49.4,56.0",
        "rspn": 1,
        "results": 1,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
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


@app.get("/debug")
async def debug():
    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": YANDEX_API_KEY,
        "geocode": "Казанский вокзал Казань",
        "format": "json",
        "lang": "ru_RU",
        "results": 1,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        return resp.json()

@app.get("/health")
async def health():
    return {"status": "ok"}