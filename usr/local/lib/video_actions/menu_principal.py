#!/usr/bin/env python3
import os
import subprocess
import sys

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def ejecutar_script(nombre_archivo):
    """
    Busca el script en el mismo directorio que este menú y lo ejecuta.
    """
    # Localiza la carpeta donde reside este menú
    directorio_base = os.path.dirname(os.path.abspath(__file__))
    ruta_completa = os.path.join(directorio_base, nombre_archivo)

    if os.path.exists(ruta_completa):
        try:
            print(f"\n" + "-"*40)
            print(f"[ Iniciando: {nombre_archivo} ]")
            print("-"*40 + "\n")

            # Ejecuta el script con el intérprete actual
            subprocess.run([sys.executable, ruta_completa], check=True)

        except subprocess.CalledProcessError as e:
            print(f"\n[!] Error durante la ejecución: {e}")
    else:
        print(f"\n[!] Error: No se encuentra el archivo '{nombre_archivo}'")
        print(f"Ruta buscada: {directorio_base}")

def mostrar_menu():
    limpiar_pantalla()
    print("="*40)
    print("      GESTOR DE VIDEOS")
    print("="*40)
    print("1- Obtener información de ficheros")
    print("2- Renombrar ficheros con formato de video")
    print("3- Eliminar el Metadata-Title del video")
    print("4- Eliminar idiomas no castellano")
    print("5- Convertir videos a H265/HVEC (en segundo plano)")
    print("0- Salir")
    print("-" * 40)

def main():
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción: ").strip()

        if opcion == "1":
            ejecutar_script("actions/video_check.py")

        elif opcion == "2":
            ejecutar_script("actions/video_rename.py")

        elif opcion == "3":
            ejecutar_script("actions/video_clean_metadata.py")

        elif opcion == "4":
            ejecutar_script("actions/video_clean_languages.py")

        elif opcion == "5":
            ejecutar_script("actions/video_convert_to_h265_idle.py")

        elif opcion == "0":
            print("\nSaliendo del programa. ¡Hasta luego calamar!")
            break

        else:
            print("\n[!] Opción no válida. Por favor, introduce un número del 0 al 4.")

        input("\nPresiona Enter para volver al menú...")

if __name__ == "__main__":
    main()
