#!/usr/bin/env python3
import os
import subprocess
import json

# Extensiones de video compatibles
VIDEO_EXTENSIONS = ('.mkv', '.mp4', '.avi', '.mov', '.m4v')

def get_resolution_label(width):
    """Mapea el ancho del video a una etiqueta de calidad."""
    if not width: return "Desconocido"
    if width >= 3840: return "4K"
    elif width >= 1920: return "1080p"
    elif width >= 1280: return "720p"
    elif width >= 720: return "480p"
    else: return "SD"

def get_video_info(filepath):
    """Usa ffprobe para obtener el ancho y el códec del video."""
    cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,codec_name', '-of', 'json', filepath
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        stream = data['streams'][0]
        return stream.get('width'), stream.get('codec_name', 'N/A')
    except:
        return None, "Error"

def show_analysis_table():
    # Obtener archivos de la carpeta ACTUAL
    current_dir = os.getcwd()
    files = [f for f in os.listdir(current_dir) if f.lower().endswith(VIDEO_EXTENSIONS)]

    if not files:
        print(f"\nNo se encontraron videos en: {current_dir}")
        return

    # Cabecera de la tabla ajustada para incluir Códec y Tamaño
    # Nombre (45), Calidad (10), Códec (10), Tamaño (10)
    header = f"{'ARCHIVO ORIGEN':<45} | {'CALIDAD':<10} | {'CODEC':<10} | {'TAMAÑO':<10}"
    separator = "-" * len(header)

    print(f"\nAnalizando carpeta: {current_dir}\n")
    print(header)
    print(separator)

    for filename in sorted(files):
        # Obtener información técnica
        width, codec = get_video_info(filename)
        quality = get_resolution_label(width)

        # Obtener tamaño del archivo en GB
        try:
            bytes_size = os.path.getsize(filename)
            gb_size = bytes_size / (1024 ** 3)
            size_str = f"{gb_size:.2f} GB"
        except:
            size_str = "Error"

        # Truncar nombre si es muy largo para mantener la estructura
        display_name = (filename[:42] + '..') if len(filename) > 45 else filename

        print(f"{display_name:<45} | {quality:<10} | {codec:<10} | {size_str:<10}")

    print(separator)
    print(f"Total de archivos analizados: {len(files)}\n")

if __name__ == "__main__":
    show_analysis_table()
