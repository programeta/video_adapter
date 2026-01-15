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
    """Extrae metadatos detallados usando ffprobe con manejo de errores mejorado."""
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
                # Normalización de nombres de códec
                if codec_name == 'HEVC': codec_name = 'H265'
                metadata['v_codec'] = codec_name

            elif codec_type == 'audio' and metadata['a_codec'] == 'NoAudio':
                metadata['a_codec'] = codec_name

        return metadata
    except Exception as e:
        return None

def apply_renaming():
    if not check_dependencies():
        return

    target_dir = os.getcwd()
    files = [f for f in os.listdir(target_dir) if f.lower().endswith(VIDEO_EXTENSIONS)]

    if not files:
        print(f"No se encontraron videos en: {target_dir}")
        return

    print(f"\n{'ARCHIVO ORIGEN':<40} | {'INFO EXTRAÍDA':<20} | {'ESTADO'}")
    print("-" * 100)

    for filename in sorted(files):
        metadata = get_video_metadata(filename)

        if not metadata or metadata['width'] is None:
            print(f"{filename[:40]:<40} | {'N/A':<20} | [ERROR] No se pudo analizar")
            continue

        quality = get_resolution_label(metadata['width'])
        v_codec = metadata['v_codec']
        a_codec = metadata['a_codec']

        tag = f"{quality} {v_codec} {a_codec}"
        name, ext = os.path.splitext(filename)

        # Evitar renombrar si la etiqueta ya existe (case insensitive)
        if tag.lower() in name.lower():
            print(f"{filename[:40]:<40} | {tag:<20} | [OK] Ya tiene etiqueta")
        else:
            new_name = f"{name} - {tag}{ext}"
            try:
                os.rename(filename, new_name)
                print(f"{filename[:40]:<40} | {tag:<20} | [RENOMBRADO]")
            except Exception as e:
                print(f"{filename[:40]:<40} | {tag:<20} | [ERROR] {e}")

    print("-" * 100)
    print("Proceso completado.\n")

if __name__ == "__main__":
    apply_renaming()
