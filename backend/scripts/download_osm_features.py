import requests
import json
import os

OVERPASS_URL = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"

def descargar_features_kazan():
    print("Descargando features urbanas de Kazán desde OSM...")
    
    # Bounding box de Kazán
    bbox = "55.6,48.8,56.1,49.5" # sur,oeste,norte,este — correcto para Overpass
    
    queries = {
        "parques": f"""
            [out:json][timeout:30];
            (
              way["leisure"="park"]({bbox});
              relation["leisure"="park"]({bbox});
            );
            out center;
        """,
        "restaurantes": f"""
            [out:json][timeout:30];
            (
              node["amenity"="restaurant"]({bbox});
              node["amenity"="cafe"]({bbox});
              node["amenity"="fast_food"]({bbox});
            );
            out center;
        """,
        "estaciones": f"""
            [out:json][timeout:30];
            (
              node["public_transport"="station"]({bbox});
              node["railway"="station"]({bbox});
              node["highway"="bus_stop"]({bbox});
            );
            out center;
        """,
        "plazas": f"""
            [out:json][timeout:30];
            (
              way["place"="square"]({bbox});
              node["place"="square"]({bbox});
            );
            out center;
        """,
        "basura": f"""
            [out:json][timeout:30];
            (
              node["amenity"="waste_basket"]({bbox});
              node["amenity"="waste_disposal"]({bbox});
            );
            out center;
        """,
        "mercados": f"""
            [out:json][timeout:30];
            (
              node["amenity"="marketplace"]({bbox});
              way["amenity"="marketplace"]({bbox});
            );
            out center;
        """,
    }

    features = {}
    
    for nombre, query in queries.items():
        print(f"  Descargando {nombre}...")
        try:
            resp = requests.post(OVERPASS_URL, data=query, timeout=60)
            data = resp.json()
            elementos = []
            for el in data.get("elements", []):
                if el.get("type") == "node":
                    elementos.append({"lat": el["lat"], "lng": el["lon"]})
                elif el.get("center"):
                    elementos.append({"lat": el["center"]["lat"], "lng": el["center"]["lon"]})
            features[nombre] = elementos
            print(f"    → {len(elementos)} elementos")
        except Exception as e:
            print(f"    Error: {e}")
            features[nombre] = []

    output_path = os.path.join(os.path.dirname(__file__), "../data/urban_features.json")
    with open(output_path, "w") as f:
        json.dump(features, f, indent=2)

    print(f"\nGuardado en {output_path}")
    total = sum(len(v) for v in features.values())
    print(f"Total elementos: {total}")
    return features

if __name__ == "__main__":
    descargar_features_kazan()