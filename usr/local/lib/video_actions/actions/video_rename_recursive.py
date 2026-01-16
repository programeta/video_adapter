#!/usr/bin/env python3
import os
import subprocess
import json
import re
import shutil

# Extensiones de video compatibles
VIDEO_EXTENSIONS = ('.mkv', '.mp4', '.avi', '.mov', '.m4v')

def check_dependencies():
    """Verifica si ffprobe está instalado."""
    if shutil.which("ffprobe") is None:
        print("ERROR: 'ffprobe' no está instalado o no se encuentra en el PATH.")
        return False
    return True

def get_resolution_label(width):
    if not width: return "SD"
    try:
        width = int(width)
        if width >= 3840: return "4K"
        elif width >= 1920: return "1080p"
        elif width >= 1280: return "720p"
        elif width >= 720: return "480p"
        else: return "SD"
    except:
        return "SD"

def get_video_metadata(filepath):
    """Extrae metadatos detallados usando ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_streams',
        '-of', 'json', filepath
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        streams = data.get('streams', [])

        metadata = {
            'width': None,
            'v_codec': 'UnknownVideo',
            'a_codec': 'NoAudio'
        }
        for stream in streams:
            codec_type = stream.get('codec_type')
            codec_name = stream.get('codec_name', '').upper()

            if codec_type == 'video' and metadata['width'] is None:
                metadata['width'] = stream.get('width')
                if codec_name == 'HEVC': codec_name = 'H265'
                metadata['v_codec'] = codec_name

            elif codec_type == 'audio' and metadata['a_codec'] == 'NoAudio':
                metadata['a_codec'] = codec_name

        return metadata
    except Exception:
        return None

def apply_renaming_recursive():
    if not check_dependencies():
        return

    target_dir = os.getcwd()
    video_files = []

    # RECURSIVIDAD: Buscamos en todas las subcarpetas
    print(f"🔍 Escaneando archivos en: {target_dir}...")
    for root, dirs, files in os.walk(target_dir):
        for f in files:
            if f.lower().endswith(VIDEO_EXTENSIONS):
                # Guardamos ruta completa y ruta relativa para el log
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, target_dir)
                video_files.append((full_path, rel_path, f))

    if not video_files:
        print(f"No se encontraron videos en el directorio actual ni en sus subcarpetas.")
        return

    print(f"\n{'ARCHIVO (RUTA RELATIVA)':<45} | {'TAG GENERADO':<20} | {'ESTADO'}")
    print("-" * 105)

    # Procesar ordenados por nombre para facilitar la lectura
    for full_path, rel_path, filename in sorted(video_files, key=lambda x: x[1]):
        metadata = get_video_metadata(full_path)

        if not metadata or metadata['width'] is None:
            display_name = (rel_path[:42] + '..') if len(rel_path) > 45 else rel_path
            print(f"{display_name:<45} | {'N/A':<20} | [ERROR] Falló ffprobe")
            continue

        quality = get_resolution_label(metadata['width'])
        v_codec = metadata['v_codec']
        a_codec = metadata['a_codec']

        tag = f"{quality} {v_codec} {a_codec}"
        name, ext = os.path.splitext(filename)

        # Evitar renombrar si la etiqueta ya existe en el nombre del archivo
        if tag.lower() in name.lower():
            display_name = (rel_path[:42] + '..') if len(rel_path) > 45 else rel_path
            print(f"{display_name:<45} | {tag:<20} | [OK] Ya etiquetado")
        else:
            new_filename = f"{name} - {tag}{ext}"
            new_full_path = os.path.join(os.path.dirname(full_path), new_filename)

            try:
                os.rename(full_path, new_full_path)
                display_name = (rel_path[:42] + '..') if len(rel_path) > 45 else rel_path
                print(f"{display_name:<45} | {tag:<20} | [RENOMBRADO]")
            except Exception as e:
                display_name = (rel_path[:42] + '..') if len(rel_path) > 45 else rel_path
                print(f"{display_name:<45} | {tag:<20} | [ERROR] {e}")

    print("-" * 105)
    print("Proceso recursivo completado.\n")

if __name__ == "__main__":
    apply_renaming_recursive()