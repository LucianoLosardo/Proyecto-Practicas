
import gc
import json
import os
import cv2
import numpy as np
import torch

try:
    from speciesnet import SpeciesNet
except ImportError:
    print(
        "❌ No se encontró la librería 'speciesnet'. Ejecuta el script con: uv run process_speciesnet.py"
    )

INPUT_DIR = "/mnt/disco/ProyectoJabali/jsons_filtrados"
OUTPUT_DIR = "/mnt/disco/ProyectoJabali/Resultado_SpeciesNet"
MODEL_PATH = "/mnt/disco/ProyectoJabali/SpeciesNet"

def load_classifier():
    """Carga el modelo SpeciesNet de Google."""
    print("⏳ Cargando modelo SpeciesNet...")
    model = SpeciesNet(model_name=MODEL_PATH)
    print("✅ Modelo SpeciesNet cargado correctamente.")
    return model


def crop_bbox(frame, bbox):
    """Corta la región indicada por el Bounding Box [xmin, ymin, xmax, ymax]."""
    h, w, _ = frame.shape
    xmin, ymin, xmax, ymax = bbox

    xmin = max(0, min(int(xmin), w - 1))
    ymin = max(0, min(int(ymin), h - 1))
    xmax = max(xmin + 1, min(int(xmax), w))
    ymax = max(ymin + 1, min(int(ymax), h))

    return frame[ymin:ymax, xmin:xmax]


def process_video_species(video_data, model):
    """Abre el video, extrae los recortes de cada fotograma detectado y ejecuta SpeciesNet."""
    video_path = video_data.get("filepath")
    if not video_path or not os.path.exists(video_path):
        print(f"⚠️ Video no encontrado: {video_path}")
        return video_data

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Error al abrir el video: {video_path}")
        return video_data

    species_summary = {}

    for frame_det in video_data.get("frame_detections", []):
        frame_num = frame_det.get("frame")

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num - 1)
        ret, frame = cap.read()
        if not ret:
            continue

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        for det in frame_det.get("detections", []):
            if det.get("label") == "animal":
                bbox = det.get("bbox")
                crop = crop_bbox(frame_rgb, bbox)

                if crop.size == 0:
                    continue

                try:
                    predictions = model.predict(crop)

                    if isinstance(predictions, list) and len(predictions) > 0:
                        pred = predictions[0]
                    else:
                        pred = predictions

                    species_name = pred.get("prediction", "Desconocido")
                    scientific_name = pred.get("scientific_name", "N/A")
                    species_conf = round(float(pred.get("confidence", 0.0)), 4)

                except Exception as e:
                    species_name = "Error en Clasificación"
                    scientific_name = str(e)
                    species_conf = 0.0

                det["species_prediction"] = species_name
                det["scientific_name"] = scientific_name
                det["species_confidence"] = species_conf

                species_summary[species_name] = (
                    species_summary.get(species_name, 0) + 1
                )

    cap.release()
    video_data["summary"]["species_counts"] = species_summary
    return video_data


def main():
    if not os.path.exists(INPUT_DIR):
        print(f"❌ La carpeta de entrada {INPUT_DIR} no existe.")
        return

    # 🔍 Búsqueda RECURSIVA de archivos .json
    json_files = []
    for root, _, files in os.walk(INPUT_DIR):
        for file in files:
            if file.lower().endswith(".json"):
                json_files.append(os.path.join(root, file))

    if not json_files:
        print(
            f"⚠️ No se encontraron archivos JSON en {INPUT_DIR} ni en sus subcarpetas."
        )
        return

    print(
        f"📂 Se encontraron {len(json_files)} archivo(s) JSON en total. Procesando con SpeciesNet..."
    )
    model = load_classifier()

    for idx, input_path in enumerate(sorted(json_files), 1):
        # 📁 Replicar la estructura de subcarpetas en el directorio de salida
        rel_path = os.path.relpath(input_path, INPUT_DIR)
        output_path = os.path.join(OUTPUT_DIR, rel_path)

        # Crear subcarpetas si no existen
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        print(f"\n[{idx}/{len(json_files)}] Procesando: {rel_path}")

        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "metadata" in data:
            data["metadata"]["species_model"] = "Google SpeciesNet"

        videos = data.get("videos", [])
        for v_idx, video_data in enumerate(videos, 1):
            print(
                f"   └─ Video {v_idx}/{len(videos)}: {video_data.get('file')}"
            )
            process_video_species(video_data, model)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"   💾 Guardado en: {output_path}")

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

    print(
        f"\n🎉 ¡Proceso completado! Todos los archivos procesados se encuentran en:\n👉 {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()