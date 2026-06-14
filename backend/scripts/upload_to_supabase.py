import json
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

input_path = os.path.join(os.path.dirname(__file__), "../data/palomas_validadas_v2.json")

with open(input_path) as f:
    observaciones = json.load(f)

print(f"Total a subir: {len(observaciones)}")

batch_size = 500
subidas = 0

for i in range(0, len(observaciones), batch_size):
    batch = observaciones[i:i + batch_size]
    rows = [
        {
            "lat": obs["lat"],
            "lng": obs["lng"],
            "fecha": obs.get("fecha"),
            "foto_url": obs.get("foto_url"),
            "score": 1,
        }
        for obs in batch
    ]
    supabase.table("pigeon_zones").insert(rows).execute()
    subidas += len(batch)
    print(f"Subidas: {subidas}/{len(observaciones)}")

print("✅ Listo!")