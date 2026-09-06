import os
import json
from collections import defaultdict

def transform_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    new_images = []

    for item in data.get("images", []):
        frames_processed = item.get("frames_processed", [])
        detections = item.get("detections", [])

        # Agrupar las detecciones por frame_number
        detections_by_frame = defaultdict(list)
        for det in detections:
            frame_num = det.get("frame_number")
            
            # Copiar la detección omitiendo la clave "frame_number"
            det_clean = {k: v for k, v in det.items() if k != "frame_number"}
            detections_by_frame[frame_num].append(det_clean)

        # Generar la entrada en "images" usando directamente el número de frame
        for frame_num in frames_processed:
            frame_filename = f"frame_{int(frame_num):06d}.jpg"
            frame_detections = detections_by_frame.get(frame_num, [])

            new_images.append({
                "file": frame_filename,
                "detections": frame_detections
            })

    # Construir la nueva estructura
    new_data = {
        "images": new_images,
        "detection_categories": data.get("detection_categories", {
            "1": "animal",
            "2": "person",
            "3": "vehicle"
        }),
        "info": data.get("info", {})
    }

    # Sobrescribir el archivo original (in-place)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)


def process_directory(directory_path):
    # Recorre la carpeta raíz y todas sus subcarpetas
    for root, dirs, files in os.walk(directory_path):
        for filename in files:
            if filename.endswith(".json"):
                full_path = os.path.join(root, filename)
                print(f"Procesando: {full_path}...")
                try:
                    transform_json_file(full_path)
                    print(f"✓ Listo: {filename}")
                except Exception as e:
                    print(f"✗ Error al procesar {full_path}: {e}")

if __name__ == "__main__":
    FOLDER_PATH = "./jsons"
    process_directory(FOLDER_PATH)