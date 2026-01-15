#!/usr/bin/env python3

import os
import subprocess
import json
import time
import sys
from pathlib import Path

# --- Configuración ---
INPUT_DIR = Path(".").resolve()
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv'}

# Parámetros de ffmpeg
FFMPEG_PARAMS = [
    "-c:v", "libx265",
    "-crf", "23",
    "-preset", "medium",
    "-c:a", "copy"
]

MAX_LOAD_THRESHOLD = 4

def get_video_details(filepath):
    cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name:format=duration,size',
        '-of', 'json', str(filepath)
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(result.stdout)
        if not data.get('streams'): return None, 0, 0
        codec = data['streams'][0].get('codec_name', '')
        duration = float(data['format'].get('duration', 0))
        size = int(data['format'].get('size', 0))
        return (codec in ['hevc', 'h265']), duration, size
    except:
        return None, 0, 0

def is_ffmpeg_running():
    """Comprueba si hay algún proceso ffmpeg ejecutándose en el sistema."""
    try:
        # Buscamos procesos ffmpeg.
        # Si pgrep encuentra algo, el returncode será 0.
        # Usamos -x para que coincida exactamente con el nombre del proceso.
        result = subprocess.run(['pgrep', '-x', 'ffmpeg'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode == 0
    except FileNotFoundError:
        # Si pgrep no está instalado, intentamos una alternativa básica con ps
        return False

def wait_for_idle():
    """Espera hasta que la carga sea baja y no haya otro ffmpeg corriendo."""
    while True:
        try:
            load_1, _, _ = os.getloadavg()
            ffmpeg_active = is_ffmpeg_running()

            if load_1 < MAX_LOAD_THRESHOLD and not ffmpeg_active:
                break

            motivo = ""
            if load_1 >= MAX_LOAD_THRESHOLD:
                motivo = f"Carga Alta ({load_1:.2f})"
            if ffmpeg_active:
                motivo += (" & " if motivo else "") + "FFMPEG activo"

            sys.stdout.write(f"\r     Esperando: {motivo}...          ")
            sys.stdout.flush()
            time.sleep(30)
        except OSError:
            break

def format_seconds(seconds):
    if seconds < 0: seconds = 0
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d}"

def timestamp_to_seconds(ts):
    """Convierte HH:MM:SS a segundos totales."""
    try:
        parts = ts.split(':')
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except:
        return 0

def format_size(size_bytes):
    return f"{size_bytes / (1024**3):.2f} GB"

def main():
    print("=" * 75)
    print(f"🚀 ESCANEANDO Y REEMPLAZANDO EN: {INPUT_DIR}")
    print("   (Destino: .mkv | Original: .ext.ORI)")
    print("=" * 75)

    file_queue = []
    for f_path in INPUT_DIR.rglob('*'):
        if f_path.suffix.upper() == '.ORI': continue
        if not f_path.is_file() or f_path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue

        is_h265, duration, size = get_video_details(f_path)

        if is_h265 is False and is_h265 is not None:
            file_queue.append({
                'path': f_path,
                'duration_str': format_seconds(duration),
                'duration_sec': duration,
                'old_size': size
            })

    if not file_queue:
        print("\n✅ Nada que procesar.")
        return

    print(f"Vídeos a convertir: {len(file_queue)}")
    print("-" * 75)

    stats = []
    total_start_time = time.time()

    for i, item in enumerate(file_queue, 1):
        file_path = item['path']
        total_duration_str = item['duration_str']
        total_duration_sec = item['duration_sec']
        old_size = item['old_size']

        # Aquí es donde el script se detendrá si la máquina está cargada o hay otro ffmpeg
        wait_for_idle()

        original_backup = file_path.with_suffix(file_path.suffix + '.ORI')
        final_mkv = file_path.with_suffix('.mkv')
        temp_output = file_path.with_suffix('.converting_tmp.mkv')

        print(f"[{i}/{len(file_queue)}] 🎥 {file_path.name}")

        item_start_time = time.time()

        cmd_ffmpeg = ['ffmpeg', '-i', str(file_path)] + FFMPEG_PARAMS + [str(temp_output), '-y']
        full_cmd = ['nice', '-n', '19', 'ionice', '-c', '3'] + cmd_ffmpeg

        try:
            process = subprocess.Popen(full_cmd, stderr=subprocess.PIPE, text=True, universal_newlines=True)
        except FileNotFoundError:
            process = subprocess.Popen(cmd_ffmpeg, stderr=subprocess.PIPE, text=True, universal_newlines=True)
        for line in process.stderr:
            if "time=" in line:
                try:
                    current_time_str = line.split("time=")[1].split()[0].split(".")[0]
                    current_sec = timestamp_to_seconds(current_time_str)
                    elapsed_real = time.time() - item_start_time

                    if current_sec > 0:
                        remaining_sec_video = total_duration_sec - current_sec
                        conversion_speed = current_sec / elapsed_real
                        eta_sec = remaining_sec_video / conversion_speed
                        eta_str = format_seconds(eta_sec)
                    else:
                        eta_str = "--:--:--"

                    sys.stdout.write(
                        f"\r   -> {current_time_str} / {total_duration_str} | "
                        f"T: {format_seconds(elapsed_real)} | "
                        f"ETA: {eta_str} "
                    )
                    sys.stdout.flush()
                except: pass

        process.wait()

        if process.returncode == 0:
            try:
                new_size = temp_output.stat().st_size
                file_path.rename(original_backup)
                temp_output.rename(final_mkv)

                stats.append({
                    'name': file_path.name,
                    'old': old_size,
                    'new': new_size
                })
                print(f"\n   ✓ OK: Ahorro de {format_size(old_size - new_size)}")
            except Exception as e:
                print(f"\n   ❌ Error al renombrar: {e}")
        else:
            print(f"\n   ❌ Error en la conversión.")
            if temp_output.exists():
                temp_output.unlink()

        print("-" * 75)

    if stats:
        total_old = sum(s['old'] for s in stats)
        total_new = sum(s['new'] for s in stats)
        total_saved = total_old - total_new

        print("\n" + "═" * 85)
        print(f"{'PELÍCULA':<50} | {'ORIGINAL':<10} | {'H265':<10} | {'AHORRO':<10}")
        print("-" * 85)
        for s in stats:
            name_trunc = (s['name'][:47] + '..') if len(s['name']) > 47 else s['name']
            print(f"{name_trunc:<50} | {format_size(s['old']):<10} | {format_size(s['new']):<10} | {format_size(s['old']-s['new']):<10}")

        print("-" * 85)
        print(f"{'TOTAL GLOBAL':<50} | {format_size(total_old):<10} | {format_size(total_new):<10} | {format_size(total_saved):<10}")
        print("═" * 85)
        print(f"Tiempo total de ejecución: {format_seconds(time.time() - total_start_time)}")

if __name__ == "__main__":
    main()
