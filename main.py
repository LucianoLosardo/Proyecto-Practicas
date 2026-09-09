#el main:
#   - configura las instancias para que matcheen con los archivos que permanecen en la carpeta temp_frames
#   - corre el Species Net

import os
import json
from pathlib import Path
from speciesnet import SpeciesNet, DEFAULT_MODEL
from speciesnet.utils import prepare_instances_dict

# -------------------------------------------------------------------------
# Configuración
# -------------------------------------------------------------------------
OUTPUT_JSON = "especies_resultados_finales.json"
COUNTRY_CODE = "ARG"
TEMP_DETECTIONS_JSON = "temp_detections.json"

def main():   
    json_path = Path(TEMP_DETECTIONS_JSON)
    print("preparacion de instancias y carga de archivos")
    if not json_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {TEMP_DETECTIONS_JSON}")

    # 1. Cargar el JSON temporal
    print("1. Leyendo detecciones temporales...")
    with open(json_path, "r", encoding="utf-8") as f:
        raw_json_data = json.load(f)

    predictions_data = raw_json_data.get("predictions", [])

    # 2. Extraer rutas y filtrar solo las que EXISTEN en disco actualmente
    all_filepaths = []
    filtered_detections_dict = {}

    for item in predictions_data:
        fp = item.get("filepath")
        if fp and os.path.isfile(fp):  # Verifica que la imagen no se haya movido/borrado (IMPORTANTE)
            all_filepaths.append(fp)
            filtered_detections_dict[fp] = {"detections": item.get("detections", [])}

    if not all_filepaths:
        raise RuntimeError("No se encontraron imágenes válidas en el disco que coincidan con el JSON.")

   # print(f"instancias a procesar: {len(all_filepaths)}")

    # 3. Preparar mapa de instancias
    instances_dict = prepare_instances_dict(
        filepaths=all_filepaths,
        country=COUNTRY_CODE
    )

    # 4. Clasificación
    model = SpeciesNet(DEFAULT_MODEL, components="classifier", geofence=True)

    print("arranca a clasificar")    
    model.classify(
        instances_dict=instances_dict,
        detections_dict=filtered_detections_dict,
        run_mode="multi_thread",
        batch_size=8,
        progress_bars=True,
        predictions_json=OUTPUT_JSON
    )

    print(f"\n¡Proceso finalizado con éxito! Predicciones guardadas en: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()