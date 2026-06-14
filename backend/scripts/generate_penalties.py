import json
import os
import csv
from supabase import create_client
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def generar_penalizaciones():
    print("Cargando zonas de palomas...")
    result = supabase.table("pigeon_zones").select("lat,lng,score").gte("score", 5).execute()
    zonas = result.data
    print(f"Zonas cargadas: {len(zonas)}")

    output_path = os.path.join(os.path.dirname(__file__), "../../osrm/penalties.csv")
    
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["lat", "lon", "penalty"])
        for zona in zonas:
            penalty = min(zona["score"] * 10, 100)
            writer.writerow([zona["lat"], zona["lng"], penalty])

    print(f"Penalizaciones guardadas en {output_path}")
    print(f"Total: {len(zonas)} puntos penalizados")

if __name__ == "__main__":
    generar_penalizaciones()