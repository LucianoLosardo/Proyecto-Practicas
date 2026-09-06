import os
import json
import cv2
from pathlib import Path
from speciesnet import SpeciesNet, DEFAULT_MODEL
from speciesnet.utils import prepare_instances_dict, load_partial_predictions

# -------------------------------------------------------------------------
# Configuración de Rutas y Parámetros
# -------------------------------------------------------------------------
VIDEOS_DIR = Path("./FotoTrampeo")
JSONS_DIR = Path("./jsons")
TEMP_FRAMES_DIR = Path("./temp_frames")
OUTPUT_JSON = "especies_resultados_finales.json"
COUNTRY_CODE = "ARG"

def extract_key(path: Path) -> str:
    """
    Extrae la clave única basada en (SL---, fecha, nombre_video/carpeta)
    recorriendo los padres de la ruta.
    Ejemplo: FotoTrampeo/SL000/20250607/DCMI/IMG_0005.mp4 -> 'SL000/20250607/IMG_0005'
    """
    parts = path.parts
    sl_part = None
    fecha_part = None
    
    # Buscar las carpetas que representan el SL--- y la fecha dentro de la ruta
    for i, part in enumerate(parts):
        if part.startswith("SL"):
            sl_part = part
            if i + 1 < len(parts):
                fecha_part = parts[i + 1]
            break
            
    if not sl_part or not fecha_part:
        return None

    # Si es un archivo .mp4 tomamos el stem (sin extension), si es un json tomamos el nombre del directorio padre
    item_name = path.stem if path.suffix.lower() in [".mp4", ".m4v"] else path.parent.name
    
    return f"{sl_part}/{fecha_part}/{item_name}"

def index_videos(base_path: Path) -> dict:
    """Busca todos los mp4/m4v y los mapea usando la clave única (SL/fecha/video)."""
    video_map = {}
    for ext in ["*.mp4", "*.m4v"]:
        for path in base_path.rglob(ext):
            key = extract_key(path)
            if key:
                video_map[key] = path
    return video_map

def process_video_and_json(video_path: Path, json_path: Path, temp_dir: Path, key_prefix: str):
    """Extrae frames del video e ingresa las detecciones formateadas."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    category_map = data.get("detection_categories", {})
    cap = cv2.VideoCapture(str(video_path))
    processed_filepaths = []
    formatted_detections = {}

    temp_dir.mkdir(parents=True, exist_ok=True)

    for item in data.get("images", []):
        file_name = item["file"]  # ej: "frame_000000.jpg"
        
        try:
            frame_idx = int(file_name.replace("frame_", "").replace(".jpg", ""))
        except ValueError:
            continue

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()

        if ret:
            # Prefijo sanitized para evitar conflictos en nombres de archivo guardados
            safe_prefix = key_prefix.replace("/", "_")
            frame_out_path = temp_dir / f"{safe_prefix}_{file_name}"
            cv2.imwrite(str(frame_out_path), frame)
            
            filepath_str = str(frame_out_path.resolve())
            processed_filepaths.append(filepath_str)

            det_list = []
            for d in item.get("detections", []):
                cat_name = category_map.get(str(d.get("category")), "animal")
                det_list.append({
                    "label": cat_name,
                    "conf": d.get("conf", 0.0),
                    "bbox": d.get("bbox", [])
                })

            formatted_detections[filepath_str] = {"detections": det_list}

    cap.release()
    return processed_filepaths, formatted_detections

def main():
    print("1. Indexando archivos de video con claves compuestas (SL/fecha/video)...")
    video_map = index_videos(VIDEOS_DIR)
    print(f"Total de videos indexados: {len(video_map)}")
    
    all_filepaths = []
    combined_detections = {}

    print("2. Vinculando JSONs con sus respectivos videos...")
    matched_count = 0
    
    # Búsqueda flexible de archivos JSON de detecciones
    json_files = list(JSONS_DIR.rglob("*.json"))
    print(f"Archivos JSON encontrados en la carpeta: {len(json_files)}")

    for json_file in json_files:
        if "detection" not in json_file.name.lower():
            continue

        json_key = extract_key(json_file)
        
        if json_key and json_key in video_map:
            matched_count += 1
            video_path = video_map[json_key]
            filepaths, detections = process_video_and_json(
                video_path, json_file, TEMP_FRAMES_DIR, json_key
            )
            all_filepaths.extend(filepaths)
            combined_detections.update(detections)

    print(f"Coincidencias encontradas y procesadas: {matched_count}")

    if not all_filepaths:
        raise RuntimeError(
            f"No se pudo extraer ningún frame. Revisa que las carpetas "
            f"'{VIDEOS_DIR.resolve()}' y '{JSONS_DIR.resolve()}' existan y coincidan en sus rutas."
        )

    # -------------------------------------------------------------------------
    # Guardar detecciones con el esquema exacto de SpeciesNet
    # -------------------------------------------------------------------------
    temp_detections_json = "temp_detections.json"
    
    predictions_list = []
    for filepath, det_data in combined_detections.items():
        predictions_list.append({
            "filepath": filepath,
            "detections": det_data.get("detections", [])
        })

    wrapped_detections = {
        "predictions": predictions_list
    }

    with open(temp_detections_json, "w", encoding="utf-8") as f:
        json.dump(wrapped_detections, f, ensure_ascii=False, indent=4)

    print("3. Preparando mapa de instancias e iniciando SpeciesNet...")
    instances_dict = prepare_instances_dict(
        filepaths=all_filepaths,
        country=COUNTRY_CODE
    )

    detections_dict, _ = load_partial_predictions(
        temp_detections_json,
        instances_dict["instances"]
    )

    model = SpeciesNet(DEFAULT_MODEL, components="classifier", geofence=True)
    
    model.classify(
        instances_dict=instances_dict,
        detections_dict=detections_dict,
        run_mode="multi_thread",
        batch_size=8,
        progress_bars=True,
        predictions_json=OUTPUT_JSON
    )

    print(f"\n¡Proceso finalizado con éxito! Predicciones guardadas en: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()