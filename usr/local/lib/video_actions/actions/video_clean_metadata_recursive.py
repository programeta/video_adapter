#!/usr/bin/env python3
import subprocess
import os
import sys
import json

def tiene_titulo_metadata(ruta_archivo):
    """Verifica si el stream de video tiene un metadato de título."""
    comando = [
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream_tags=title',
        '-of', 'json', ruta_archivo
    ]
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True)
        datos = json.loads(resultado.stdout)
        if 'streams' in datos and len(datos['streams']) > 0:
            return 'tags' in datos['streams'][0] and 'title' in datos['streams'][0]['tags']
        return False
    except Exception:
        return False

def obtener_duracion(ruta_archivo):
    comando = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', ruta_archivo
    ]
    resultado = subprocess.run(comando, capture_output=True, text=True)
    try:
        return float(resultado.stdout)
    except:
        return None

def limpiar_con_progreso(ruta_archivo, ruta_relativa, indice_actual, total_archivos):
    duracion_total = obtener_duracion(ruta_archivo)
    if not duracion_total:
        print(f"[{indice_actual}/{total_archivos}] ❌ No se pudo analizar: {ruta_relativa}")
        return

    nombre_base, ext = os.path.splitext(ruta_archivo)
    archivo_temp = f"{nombre_base}_temp_remux{ext}"

    comando = [
        'ffmpeg', '-i', ruta_archivo,
        '-map', '0', '-map_metadata', '0', '-metadata:s:v:0', 'title=',
        '-c', 'copy', '-f', 'matroska' if ext.lower() == '.mkv' else 'mp4',
        '-progress', 'pipe:1', '-nostats', '-y', archivo_temp
    ]
    print(f"[{indice_actual}/{total_archivos}] Procesando: {ruta_relativa}")

    proceso = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    try:
        while True:
            linea = proceso.stdout.readline()
            if not linea and proceso.poll() is not None:
                break

            if "out_time_us=" in linea:
                try:
                    us = int(linea.split('=')[1])
                    segundos_actuales = us / 1_000_000
                    porcentaje = min(int((segundos_actuales / duracion_total) * 100), 100)

                    barra = "█" * (porcentaje // 2) + "-" * (50 - (porcentaje // 2))
                    sys.stdout.write(f"\r|{barra}| {porcentaje}%")
                    sys.stdout.flush()
                except:
                    continue

        proceso.wait()
        print("")

        if proceso.returncode == 0:
            # Reemplazo del archivo original por el limpio
            os.replace(archivo_temp, ruta_archivo)
            print(f"✅ Limpiado con éxito.")
        else:
            print(f"❌ Error en FFmpeg al procesar {ruta_relativa}")
            if os.path.exists(archivo_temp): os.remove(archivo_temp)

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        if proceso: proceso.kill()
        if os.path.exists(archivo_temp): os.remove(archivo_temp)

def main():
    extensiones_validas = ('.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv')
    directorio_actual = os.getcwd()

    print(f"🔍 Escaneando archivos de video en: {directorio_actual} y subcarpetas...")

    archivos_a_procesar = []

    # RECURSIVIDAD: os.walk recorre todo el árbol de directorios
    for root, dirs, files in os.walk(directorio_actual):
        for f in files:
            if f.lower().endswith(extensiones_validas):
                # Evitar procesar archivos temporales de sesiones previas
                if "_temp_remux" in f:
                    continue

                ruta_completa = os.path.join(root, f)
                if tiene_titulo_metadata(ruta_completa):
                    # Guardamos la ruta completa para trabajar y la relativa para mostrar
                    rel_path = os.path.relpath(ruta_completa, directorio_actual)
                    archivos_a_procesar.append((ruta_completa, rel_path))

    total = len(archivos_a_procesar)

    if total == 0:
        print("🎉 Todos los archivos están limpios o no se encontraron metadatos 'Title' en el video.")
        return

    print(f"🚀 Se han encontrado {total} archivos con metadatos de título para modificar.\n")

    # Ordenar por ruta relativa para que el proceso sea visualmente organizado
    for i, (ruta_abs, ruta_rel) in enumerate(sorted(archivos_a_procesar, key=lambda x: x[1]), 1):
        limpiar_con_progreso(ruta_abs, ruta_rel, i, total)
        print("-" * 60)

    print(f"\n✨ Tarea finalizada con éxito.")

if __name__ == "__main__":
    main()