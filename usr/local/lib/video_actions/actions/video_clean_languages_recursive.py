#!/usr/bin/env python3
import os
import subprocess
import json
import sys
import re

# Extensiones compatibles
EXTENSIONS = ('.mkv', '.mp4', '.m4v', '.avi')
# Códigos de idioma para identificar el español
S_CODES = {'spa', 'es', 'es-es', 'es-419', 'spanish', 'castellano'}

def obtener_info_pistas(filepath):
    """Retorna metadatos detallados de todas las pistas."""
    # Nota: Requiere mkvtoolnix instalado
    cmd = ['mkvmerge', '-J', filepath]
    audio_tracks = []
    sub_tracks = []

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        for track in data.get('tracks', []):
            props = track.get('properties', {})
            track_info = {
                'id': str(track['id']),
                'type': track['type'],
                'lang': props.get('language', 'und').lower(),
                'name': props.get('track_name', ''),
                'codec': track.get('codec', 'Unknown')
            }

            if track['type'] == 'audio':
                audio_tracks.append(track_info)
            elif track['type'] == 'subtitles':
                sub_tracks.append(track_info)

        return audio_tracks, sub_tracks
    except Exception as e:
        print(f"   [!] Error analizando metadatos: {e}")
        return [], []

def mostrar_plan_limpieza(audios, subs):
    """Muestra qué se queda y qué se va."""
    print("   Estado de las pistas:")

    a_ids_mantener = []
    for a in audios:
        mantener = a['lang'] in S_CODES
        status = "[MANTENER]" if mantener else "[ELIMINAR]"
        print(f"      Audio -> ID {a['id']}: {a['lang']} ({a['codec']}) {a['name']} {status}")
        if mantener: a_ids_mantener.append(a['id'])

    s_ids_mantener = []
    for s in subs:
        mantener = s['lang'] in S_CODES
        status = "[MANTENER]" if mantener else "[ELIMINAR]"
        print(f"      Subs  -> ID {s['id']}: {s['lang']} ({s['codec']}) {s['name']} {status}")
        if mantener: s_ids_mantener.append(s['id'])

    return a_ids_mantener, s_ids_mantener

def process_file(filepath, audio_ids, sub_ids):
    dirname = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    # Creamos el temporal en la misma carpeta que el original
    temp_file = os.path.join(dirname, f"temp_processing_{filename}.mkv")

    cmd = ['mkvmerge', '-o', temp_file]

    if audio_ids:
        cmd.extend(['--audio-tracks', ",".join(audio_ids)])
    else:
        cmd.append('--no-audio')

    if sub_ids:
        cmd.extend(['--subtitle-tracks', ",".join(sub_ids)])
    else:
        cmd.append('--no-subtitles')

    cmd.append(filepath)

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in process.stdout:
        progress = re.findall(r'(\d+%)', line)
        if progress:
            sys.stdout.write(f"\r   [Progreso: {progress[0]}] ")
            sys.stdout.flush()

    process.wait()

    if process.returncode in [0, 1]:
        sys.stdout.write("\r   [OK] Procesado correctamente.          \n")
        try:
            # Reemplazo seguro: eliminamos original y renombramos temporal
            os.remove(filepath)
            final_name = os.path.splitext(filepath)[0] + ".mkv"
            os.rename(temp_file, final_name)
        except Exception as e:
            print(f"   [!] Error de archivos (Permisos/Acceso): {e}")
    else:
        print(f"\n   [!] ERROR en mkvmerge (Code {process.returncode})")
        if os.path.exists(temp_file): os.remove(temp_file)

def main():
    target_dir = os.getcwd()
    files_to_process = []

    # RECURSIVIDAD: Buscamos en todas las subcarpetas
    print(f"Escaneando archivos en: {target_dir}...")
    for root, dirs, files in os.walk(target_dir):
        for f in files:
            if f.lower().endswith(EXTENSIONS):
                # Evitamos procesar archivos temporales de una ejecución fallida anterior
                if not f.startswith("temp_processing_"):
                    files_to_process.append(os.path.join(root, f))

    total_files = len(files_to_process)
    if total_files == 0:
        print("No se encontraron archivos de video compatibles.")
        return

    print(f"\n=== INICIANDO LIMPIEZA RECURSIVA ({total_files} archivos) ===\n")

    for index, f_path in enumerate(sorted(files_to_process), 1):
        # Mostramos la ruta relativa para mayor claridad
        rel_path = os.path.relpath(f_path, target_dir)
        print(f"({index}/{total_files}) ARCHIVO: {rel_path}")

        audios, subs = obtener_info_pistas(f_path)

        if not audios and not subs:
            print("   [SALTADO] No se pudieron leer pistas o formato no compatible.")
            print("-" * 50)
            continue

        a_ids, s_ids = mostrar_plan_limpieza(audios, subs)

        # Lógica de decisión
        if not a_ids:
            print("   [SALTADO] No se detectó audio en español (S_CODES).")
        elif len(a_ids) == len(audios) and len(s_ids) == len(subs):
            print("   [SALTADO] El archivo ya contiene solo pistas en español.")
        else:
            process_file(f_path, a_ids, s_ids)

        print("-" * 50)

    print("\n--- Tarea finalizada con éxito ---\n")

if __name__ == "__main__":
    main()