import json
import argparse
from pathlib import Path

def merge_json_files(input_dir: str, output_file: str):
    input_path = Path(input_dir)
    output_path = Path(output_file)

    if not input_path.exists() or not input_path.is_dir():
        raise ValueError(f"La carpeta de entrada no existe: {input_dir}")

    merged_data = {
        "images": [],
        "detection_categories": {},
        "info": {}
    }

    json_files = list(input_path.rglob("*.json"))
    print(f"Encontrados {len(json_files)} archivos JSON. Unificando...")

    for i, json_file in enumerate(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Acumular registros
                if "images" in data and data["images"]:
                    merged_data["images"].extend(data["images"])
                
                # Extraer la metadata e info únicamente del primer JSON
                if i == 0:
                    if "detection_categories" in data:
                        merged_data["detection_categories"] = data["detection_categories"]
                    if "info" in data:
                        merged_data["info"] = data["info"]

        except Exception as e:
            print(f"Error al leer {json_file.name}: {e}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("Escribiendo archivo consolidado con formato legible...")
    # Forzamos los saltos de línea explícitos con newline='\n'
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)

    print(f"¡Listo! Se guardaron {len(merged_data['images'])} registros en: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combina múltiples JSONs de MegaDetector en uno solo.")
    parser.add_argument("input_dir", help="Carpeta donde se encuentran los archivos JSON")
    parser.add_argument("output_file", help="Ruta del archivo JSON resultante")
    
    args = parser.parse_args()
    merge_json_files(args.input_dir, args.output_file)