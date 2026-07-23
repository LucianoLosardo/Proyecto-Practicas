import gc
import json
import os
import time
import cv2
import torch

MODEL_NAME = "md_v5a.0.0.pt"
OUTPUT_JSON = "resultados_deteccion.json"


def load_megadetector(model_path):
    print(f"Cargando MegaDetector desde: {model_path}")
    model = torch.hub.load(
        "ultralytics/yolov5", "custom", path=model_path, trust_repo=True
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    print(f"Modelo cargado en: {device.upper()}")
    return model


def process_video(
    video_path, model, conf_threshold=0.2, frame_skip=10, img_size=640, lote=""
):
    """Procesa un video extrayendo bbox, clases, certezas y optimizando el consumo de RAM/VRAM."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error abriendo el archivo de video: {video_path}")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    filename = os.path.basename(video_path)

    video_record = {
        "file": filename,
        "filepath": video_path,
        "lote": lote,  
        "summary": {
            "detected_classes": [],
            "max_confidence": {},
            "total_detections_count": 0,
        },
        "frame_detections": [],
    }

    frame_count = 0
    total_detections = 0
    max_conf_by_class = {}

    with torch.inference_mode():
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_count % frame_skip != 0:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            results = model(frame_rgb, size=img_size)
            preds = results.pred[0]

            current_frame_dets = []

            for *box, conf, cls in preds:
                score = round(float(conf), 4)
                if score >= conf_threshold:
                    class_id = int(cls)
                    label = model.names.get(class_id, str(class_id))
                    bbox = [round(float(coord), 1) for coord in box]

                    current_frame_dets.append(
                        {
                            "class_id": class_id,
                            "label": label,
                            "confidence": score,
                            "bbox": bbox,
                        }
                    )

                    total_detections += 1
                    if (
                        label not in max_conf_by_class
                        or score > max_conf_by_class[label]
                    ):
                        max_conf_by_class[label] = score

            if current_frame_dets:
                video_record["frame_detections"].append(
                    {
                        "frame": frame_count,
                        "time_sec": round(frame_count / fps, 2),
                        "detections": current_frame_dets,
                    }
                )

            del frame, frame_rgb, results, preds

    cap.release()

    video_record["summary"]["detected_classes"] = list(max_conf_by_class.keys())
    video_record["summary"]["max_confidence"] = max_conf_by_class
    video_record["summary"]["total_detections_count"] = total_detections

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()

    return video_record


def main():
    start_time = time.time()

    data_dir = "/mnt/disco/ProyectoJabali/FotosCamarasTrampas/SL002/20240620/DCIM/100_BTCF"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, MODEL_NAME)

    if not os.path.exists(data_dir):
        print(f"Error: La carpeta {data_dir} no existe o no está montada.")
        return

    #Extraer nombre del Lote 
    parent_folder = os.path.basename(os.path.dirname(data_dir))
    curr_folder = os.path.basename(data_dir)
    lote_name = f"{parent_folder} / {curr_folder}"

    model = load_megadetector(model_path)
    video_extensions = (".mp4", ".avi", ".mov", ".mkv")

    files = [
        f for f in os.listdir(data_dir) if f.lower().endswith(video_extensions)
    ]
    print(
        f"Encontrados {len(files)} videos en Lote [{lote_name}]. Procesando..."
    )

    all_results = []

    for idx, filename in enumerate(sorted(files), 1):
        video_path = os.path.join(data_dir, filename)
        print(f"[{idx}/{len(files)}] Procesando: {filename}...")

        result = process_video(
            video_path,
            model,
            conf_threshold=0.2,
            frame_skip=10,
            img_size=640,
            lote=lote_name,
        )
        if result:
            all_results.append(result)

    #Cálculo de tiempo total
    total_elapsed = time.time() - start_time
    elapsed_seconds = round(total_elapsed, 2)

    hrs = int(total_elapsed // 3600)
    mins = int((total_elapsed % 3600) // 60)
    secs = int(total_elapsed % 60)
    time_formatted = f"{hrs:02d}:{mins:02d}:{secs:02d}"

    # Exportar JSON con metadatos de Lote y Tiempo
    json_output_path = os.path.join(base_dir, OUTPUT_JSON)
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "metadata": {
                    "model": MODEL_NAME,
                    "conf_threshold": 0.2,
                    "frame_skip": 10,
                    "total_videos": len(all_results),
                    "lote": lote_name,  
                    "execution_time_seconds": elapsed_seconds,
                    "execution_time_formatted": time_formatted,
                },
                "videos": all_results,
            },
            f,
            indent=4,
            ensure_ascii=False,
        )

    print(f"\n¡Proceso completado con éxito!")
    print(f" Lote: {lote_name}")
    print(f" Tiempo total: {time_formatted} ({elapsed_seconds} seg)")
    print(f" JSON guardado en: {json_output_path}")


if __name__ == "__main__":
    main()