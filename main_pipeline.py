# esto es un pipeline que automatiza el análisis completo
from merge_jsons import merge_json_files
from run_md_and_speciesnet import run_md_and_speciesnet, RunMDSpeciesNetOptions
from aplanar_y_vincular import aplanar_y_vincular
from merge_json_files import merge_json_files

def pipeline_principal():
    # Paso 1: Aplanar archivos
    input_videos = "CARPETA DONDE ESTAN LOS VIDEOS ORIGINALES"
    input_jsons = "CARPETA DONDE ESTAN LOS JSON ORIGINALES"
    output_videos = "CARPETA DONDE VAN LOS SYMLINKS A LOS VIDEOS FORMATEADOS"
    output_jsons = "CARPETA DONDE VAN LOS JSON MODIFICADOS"
    aplanar_y_vincular(input_videos, input_jsons, output_videos, output_jsons)


    # Paso 1: Unificar JSONs
    print("Iniciando unificación de JSONs...")
    #input_folder = output_jsons
    merged_json = "json_mergeado.json"
    
    merge_json_files(output_jsons, merged_json)

    # Paso 2: Ejecutar SpeciesNet / MegaDetector
    print("Iniciando clasificación...")
    options = RunMDSpeciesNetOptions()
    options.source = ["LINK A LOS VIDEOS"]
    options.output_file = "output_sn.json"
    options.detections_file = merged_json
    options.classifier_batch_size = 16
    options.loader_workers = 4
    options.country = "ARG"

    run_md_and_speciesnet(options)

if __name__ == "__main__":
    pipeline_principal()