#!/usr/bin/env python3
import os
import subprocess
import sys

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def ejecutar_script(nombre_archivo):
    """
    Localiza la subcarpeta 'actions' relativa a la ubicación REAL
    del script de menú, resolviendo enlaces simbólicos.
    """
    # 1. Resolvemos la ruta real del archivo (sigue el symlink hasta /usr/local/lib/...)
    ruta_real_menu = os.path.realpath(__file__)

    # 2. Obtenemos el directorio base donde están el menú y la carpeta 'actions'
    directorio_base = os.path.dirname(ruta_real_menu)

    # 3. Construimos la ruta final al subscript
    ruta_completa = os.path.join(directorio_base, nombre_archivo)

    if os.path.exists(ruta_completa):
        try:
            print(f"\n" + "-"*40)
            print(f"[ Iniciando: {os.path.basename(nombre_archivo)} ]")
            print(f"[ Origen del script: {ruta_completa} ]")
            print("-" * 40 + "\n")

            # Ejecuta el script con el intérprete actual
            subprocess.run([sys.executable, ruta_completa], check=True)

        except subprocess.CalledProcessError as e:
            print(f"\n[!] Error durante la ejecución: {e}")
    else:
        print(f"\n[!] Error: No se encuentra el archivo en:")
        print(f"    {ruta_completa}")

def mostrar_menu():
    limpiar_pantalla()
    # Obtenemos la ruta desde donde el usuario ha llamado al script
    ruta_trabajo = os.getcwd()

    print("="*60)
    print("                GESTOR DE VIDEOS - MENU")
    print("="*60)
    print(f" DIRECTORIO DE TRABAJO: {ruta_trabajo}")
    print("="*60)
    print(" 1- Obtener información de ficheros")
    print(" 2- Renombrar ficheros con formato de video")
    print(" 3- Eliminar el Metadata-Title del video")
    print(" 4- Eliminar idiomas no castellano")
    print(" 5- Convertir videos a H265/HVEC (en segundo plano)")
    print("- "*30)
    print(" 6- Obtener información de ficheros (recursivo)")
    print(" 7- Renombrar ficheros con formato de video (recursivo)")
    print(" 8- Eliminar el Metadata-Title del video (recursivo)")
    print(" 9- Eliminar idiomas no castellano (recursivo)")
    print(" 0- Salir")
    print("-" * 60)

def main():
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción: ").strip()

        # Mapeo de opciones a archivos en la subcarpeta actions/
        acciones = {
            "1": "actions/video_check.py",
            "2": "actions/video_rename.py",
            "3": "actions/video_clean_metadata.py",
            "4": "actions/video_clean_languages.py",
            "5": "actions/video_convert_to_h265_idle.py",
            "6": "actions/video_check_recursive.py",
            "7": "actions/video_rename_recursive.py",
            "8": "actions/video_clean_metadata_recursive.py",
            "9": "actions/video_clean_languages_recursive.py",
        }

        if opcion == "0":
            print("\nSaliendo del programa. ¡Hasta luego calamar!")
            break

        elif opcion in acciones:
            ejecutar_script(acciones[opcion])

        else:
            print(f"\n[!] Opción '{opcion}' no válida. Introduce un número del 0 al 5.")

        input("\nPresiona Enter para volver al menú...")

if __name__ == "__main__":
    main()
