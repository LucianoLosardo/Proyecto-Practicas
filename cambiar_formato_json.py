#anda, habria que automatizar el cambio de formato para todos los archivos. Lo puedo meter en el "test.py"
import json
import re
import os

# Update these values
def cambiar_formato_json(input_json, video_rel_path, output_json):
    #input_json = r"C:\Users\Kiara\Desktop\practicas\Test Multiples Json\detection_results.json"
    #output_json = "temp.json"
    #video_rel_path = "my_video.mp4"  # Path to video relative to your source folder
    if os.path.exists(output_json):
        os.remove(output_json)

    with open(input_json, "r") as f:
        data = json.load(f)

    video_detections = []

    for image_entry in data.get("images", []):
        frame_file = image_entry.get("file", "")

        # Extract frame number from "frame_000000.jpg"
        match = re.search(r"frame_(\d+)\.jpg", frame_file)
        if not match:
            continue
        frame_number = int(match.group(1))

        # Append frame_number to each detection in this frame
        for det in image_entry.get("detections", []):
            det["frame_number"] = frame_number
            video_detections.append(det)

    # Build standard MegaDetector video JSON format
    formatted_data = {
        "images": [{"file": video_rel_path, "detections": video_detections}]
    }

    # Preserve top-level metadata if present
    if "info" in data:
        formatted_data["info"] = data["info"]
    if "detection_categories" in data:
        formatted_data["detection_categories"] = data["detection_categories"]

    with open(output_json, "w") as f:
        json.dump(formatted_data, f, indent=2)