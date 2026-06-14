from ultralytics import YOLO
import requests
from PIL import Image
from io import BytesIO
import json
import os

def validar_con_yolo():
    input_path = os.path.join(os.path.dirname(__file__), "../data/palomas_kazan.json")
    output_path = os.path.join(os.path.dirname(__file__), "../data/palomas_validadas.json")

    with open(input_path) as f:
        observaciones = json.load(f)

    print(f"Total a validar: {len(observaciones)}")
    print("Descargando modelo YOLOv8 (primera vez tarda un poco)...")

    modelo = YOLO("yolov8n.pt")

    validadas = []
    errores = 0

    for i, obs in enumerate(observaciones):
        print(f"[{i+1}/{len(observaciones)}] Validando {obs['id']}...", end=" ")

        try:
            resp = requests.get(obs["foto_url"], timeout=10)
            img = Image.open(BytesIO(resp.content)).convert("RGB")

            resultados = modelo(img, verbose=False)

            detecta_pajaro = False
            for r in resultados:
                for cls in r.boxes.cls.tolist():
                    if int(cls) == 14:
                        detecta_pajaro = True
                        break

            if detecta_pajaro:
                validadas.append(obs)
                print("✓ confirmada")
            else:
                print("✗ descartada")

        except Exception as e:
            print(f"! error: {e}")
            errores += 1

        if (i + 1) % 100 == 0:
            with open(output_path, "w") as f:
                json.dump(validadas, f, indent=2, ensure_ascii=False)
            print(f"--- checkpoint: {len(validadas)} validadas hasta ahora ---")

    with open(output_path, "w") as f:
        json.dump(validadas, f, indent=2, ensure_ascii=False)

    print(f"\nValidadas: {len(validadas)} de {len(observaciones)}")
    print(f"Errores: {errores}")
    print(f"Guardadas en {output_path}")

if __name__ == "__main__":
    validar_con_yolo()