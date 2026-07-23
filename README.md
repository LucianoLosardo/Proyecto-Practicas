*Wildcam - Detección de Fauna con MegaDetector v5*
Herramienta en Python diseñada para procesar masivamente videos de cámaras trampa utilizando el modelo MegaDetector v5 con el fin de detectar jabalies en esos videos. Extrae automáticamente las detecciones de fauna, personas y vehículos, exportando los resultados en un reporte estructurado en formato JSON, optimizado para trabajar con grandes volúmenes de datos sin agotar la memoria RAM o VRAM del sistema.

*Características principales*
    - Detección Automática de Fauna: Detecta animales, personas y vehículos usando los pesos de MegaDetector v5 (md_v5a.0.0.pt).

    - Exportación Estructurada a JSON: Guarda cuadros delimitadores (bbox), marcas de tiempo en segundos (time_sec), fotograma exacto (frame), clases detectadas y niveles de certeza (confidence).

