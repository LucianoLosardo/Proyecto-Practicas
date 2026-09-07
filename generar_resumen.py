import json
import os
import re
from collections import defaultdict

def procesar_predicciones(json_path, output_txt_path=None, top_1_solo=False, min_conf=0.0):
    """
    Procesa el JSON de predicciones y genera el formato de texto agrupado por video.
    
    :param json_path: Ruta al archivo JSON de entrada.
    :param output_txt_path: Ruta opcional para guardar el resultado en archivo .txt.
    :param top_1_solo: Si es True, solo considera la predicción con mayor score de cada frame.
    :param min_conf: Umbral mínimo de confianza para incluir una detección.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Estructura: videos[video_id][(class_id, class_name)] = lista_de_scores
    videos = defaultdict(lambda: defaultdict(list))

    for item in data.get("predictions", []):
        filepath = item.get("filepath", "")
        filename = os.path.basename(filepath.replace("\\", "/"))
        
        # Extrae el identificador del video omitiendo '_frame_XXXXXX.jpg'
        video_id = re.sub(r'_frame_\d+\.[a-zA-Z0-9]+$', '', filename, flags=re.IGNORECASE)
        
        classifications = item.get("classifications", {})
        classes = classifications.get("classes", [])
        scores = classifications.get("scores", [])
        
        # Si se solicita solo el top-1 por frame
        pairs = list(zip(classes, scores))
        if top_1_solo and pairs:
            pairs = [pairs[0]]
            
        for cls_str, score in pairs:
            if score < min_conf:
                continue
                
            parts = cls_str.split(";")
            cls_id = parts[0]
            
            # Nombre común (último elemento no vacío del string taxonómico)
            name_parts = [p for p in parts[1:] if p.strip()]
            cls_name = name_parts[-1] if name_parts else "desconocido"
            
            videos[video_id][(cls_id, cls_name)].append(score)

    # Construcción del texto de salida
    lineas_resultado = []
    for video_id, cls_data in videos.items():
        lineas_resultado.append(f"Video: {video_id}")
        lineas_resultado.append("Output:")
        
        for (cls_id, cls_name), scores_list in cls_data.items():
            avg_conf = sum(scores_list) / len(scores_list)
            count = len(scores_list)
            lineas_resultado.append(f"  - {cls_name} (ID {cls_id}): {avg_conf:.3f} conf promedio ({count} detecciones)")
            
        lineas_resultado.append("Realidad:\n")
        lineas_resultado.append("")

    resultado_final = "\n".join(lineas_resultado)
    
    # Imprimir en consola
    print(resultado_final)
    
    # Guardar en archivo si se especifica la ruta
    if output_txt_path:
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(resultado_final)

# Ejemplo de uso:
if __name__ == "__main__":
    # Reemplaza 'tus_predicciones.json' por la ruta real de tu archivo
    procesar_predicciones("especies_resultados_finales.json", output_txt_path="reporte_videos.txt")