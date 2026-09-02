"""
    La función de este script es:
        1 - Aplanar los videos y json para que puedan existir en una misma carpeta sin colisiones, mejorando el rendimiento en
        la siguiente etapa y evitando solapamientos.
        2 - Arreglar las inconsistencias en las estructuras de directorios de los videos y json's. 
        3 - Cambia el formato de los json para que incluya el nombre del video y el numero de frame
    La estrategia que se lleva a cabo es la siguiente:
        1 - Renombrar archivos: Se cambiará el nombre a json's y videos para que representen la estructura original pero puedan
        coexistir en una misma carpeta. Por ejemplo:
                sl001/20250823/IMG_0001.mp4 --> sl00_20250823_IMG_001.mp4
                                        y
                sl001/20250823/IMG_0001/detection_results.json --> sl00_20250823_IMG_001.json
        En ambos casos el resultado se guardará en una carpeta secundaria para no perturbar la estura del material original.
        Cabe aclarar que, dado el gran volumen de videos, se decidió reordenar los videos usando symlinks en lugar de copiarlos per se, 
        por no ocupar más espacio en disco del debido.
        

"""

import os
import shutil
from pathlib import Path
from cambiar_formato_json import cambiar_formato_json

# --- CONFIGURACIÓN DE RUTAS ---
# Carpeta raíz donde están los videos y los directorios sl---
# BASE_DIR = Path("/mnt/disco/ProyectoJabali/FotosCamarasTrampas")
# BASE_DIR_JSON = Path("/mnt/disco/ProyectoJabali/jsons_filtrados") ##PONER EL PATH DE LOS JSON ORIGINALES

# # Carpetas de salida (pueden estar en cualquier lado)
# DEST_VIDEOS_DIR = Path("/mnt/disco/ProyectoJabali/Dataset_Aplanado/videos")
# DEST_JSONS_DIR = Path("/mnt/disco/ProyectoJabali/Dataset_Aplanado/jsons")

# Extensión de videos a buscar
VIDEO_EXT = ".mp4"

#Ubicacion donde se guarda el json temporal de la funcion cambiar_formato_json
TEMP = "temp.json"

def aplanar_y_vincular(BASE_DIR, BASE_DIR_JSON, DEST_VIDEOS_DIR, DEST_JSONS_DIR):
    DEST_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    DEST_JSONS_DIR.mkdir(parents=True, exist_ok=True)

    pares_encontrados = 0
    videos_huérfanos = 0

    print("Iniciando escaneo de la estructura de directorios...\n")

    # Recorremos carpetas del tipo sl---
    for sl_dir in BASE_DIR.glob("sl*"):
        if not sl_dir.is_dir():
            continue
        
        sl_name = sl_dir.name  # Ejemplo: sl001

        # Recorremos subcarpetas de fechas dentro de sl---
        for fecha_dir in sl_dir.iterdir():
            if not fecha_dir.is_dir():
                continue
            
            fecha_name = fecha_dir.name  # Ejemplo: 20240812

            carpeta_fecha_json = Path(BASE_DIR_JSON) / sl_name / fecha_name #mismo nivel, pero en la carpeta de jsons

            # Buscamos todos los videos dentro del par sl-fecha (sin importar profundidad)
            for video_path in fecha_dir.rglob(f"*{VIDEO_EXT}"):
                video_name = video_path.stem  # Ejemplo: IMG_0001
                
                # Buscamos el JSON correspondiente en el mismo nivel o subcarpeta
                # Se asume que el json está en una carpeta homónima o junto al video
                posibles_jsons = []

                if carpeta_fecha_json.exists():
                # Buscar recursivamente la CARPETA que coincida con el nombre del video
                    carpetas_encontradas = [
                        d for d in carpeta_fecha_json.rglob(video_name) if d.is_dir()
                    ]
                    
                    #Por cada carpeta hallada, verificar si contiene el detection_results.json
                    for carpeta_video in carpetas_encontradas:
                        json_file = carpeta_video / "detection_results.json"
                        if json_file.exists():
                            posibles_jsons.append(json_file)   #PROBLEMA. los json de salida no tienen el nombre de video en files
                
                # Si no está en subcarpeta, probamos buscar por el nombre del video + json
                # if not posibles_jsons:
                #     json_candidato = video_path.parent / f"{video_name}.json"
                #     if json_candidato.exists():
                #         posibles_jsons = [json_candidato]




                if posibles_jsons:
                    json_path = posibles_jsons[0]
                    



                    #MODIFICACION: aca hago lo del cambio de formato
                    cambiar_formato_json(posibles_jsons[0], f"{nuevo_nombre_base}{VIDEO_EXT}", TEMP) #aca agarra el json, lo cambia de formato, le pone el nombre del video en file, y lo guarda en el archivo en TEMP



                    # Nuevo nombre unificado
                    nuevo_nombre_base = f"{sl_name}_{fecha_name}_{video_name}"
                    
                    target_video = DEST_VIDEOS_DIR / f"{nuevo_nombre_base}{VIDEO_EXT}"
                    target_json = DEST_JSONS_DIR / f"{nuevo_nombre_base}_detection_results.json"

                    # 1. Crear Symlink para el video (no ocupa espacio ni duplica)
                    if target_video.exists() or target_video.is_symlink():
                        target_video.unlink()
                    target_video.symlink_to(video_path.resolve())

                    # 2. Copiar el JSON (son livianos)
                    #shutil.copy2(json_path, target_json)
                    #MODIFICACION: aca copia el temp que tira cambiar formato
                    shutil.copy2(TEMP, target_json)

                    pares_encontrados += 1
                else:
                    videos_huérfanos += 1

    print("=" * 50)
    print("RESUMEN DE PROCESAMIENTO:")
    print(f" -> Pares válidos vinculados (Video + JSON): {pares_encontrados}")
    print(f" -> Videos sin JSON asociado ignorados: {videos_huérfanos}")
    print(f" -> Videos aplanados disponibles en: {DEST_VIDEOS_DIR}")
    print(f" -> JSONs aplanados disponibles en: {DEST_JSONS_DIR}")
    print("=" * 50)

if __name__ == "__main__":
    aplanar_y_vincular()