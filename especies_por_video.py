import json

# --- CONFIGURACIÓN DE RUTAS ---
JSON_INPUT = r"C:\Users\Kiara\Desktop\practicas\Mega Detector\detection_result_sn.json"
TXT_OUTPUT = r"C:\Users\Kiara\Desktop\practicas\Mega Detector\especies_resumen.txt"

def generar_resumen(json_path, output_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Diccionario para mapear ID -> Nombre común de la especie
    categories_map = data.get('classification_categories', {})
    images = data.get('images', [])

    lineas_resumen = []

    for item in images:
        file_name = item.get('file', 'Desconocido')
        detections = item.get('detections', [])

        # Acumulador por video: { "cat_id": [confianza1, confianza2, ...] }
        scores_por_etiqueta = {}

        for det in detections:
            classifications = det.get('classifications', [])
            for cat_id, conf in classifications:
                if cat_id not in scores_por_etiqueta:
                    scores_por_etiqueta[cat_id] = []
                scores_por_etiqueta[cat_id].append(conf)

        # Si el video tiene clasificaciones, calculamos la media
        if scores_por_etiqueta:
            lineas_resumen.append(f"Video: {file_name}")
            for cat_id, conf_list in scores_por_etiqueta.items():
                especie_nombre = categories_map.get(cat_id, f"ID_{cat_id}")
                promedio = sum(conf_list) / len(conf_list)
                n_frames = len(conf_list)
                lineas_resumen.append(
                    f"  - {especie_nombre} (ID {cat_id}): {promedio:.3f} conf promedio ({n_frames} detecciones)"
                )
            lineas_resumen.append("")  # Línea en blanco entre videos
        else:
            lineas_resumen.append(f"Video: {file_name}")
            lineas_resumen.append("  - Sin detecciones/clasificaciones\n")

    # Escribir el resultado a archivo
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lineas_resumen))

    print(f"¡Resumen generado con éxito en: {output_path}!")

if __name__ == '__main__':
    generar_resumen(JSON_INPUT, TXT_OUTPUT)