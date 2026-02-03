#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Facebook Scraper Local
======================

Herramienta para extraer publicaciones de Facebook con descarga local de imagenes,
descripciones y generacion de Excel con metadata.

Uso:
    python main.py          # Inicia la interfaz grafica
    python main.py --cli    # Modo linea de comandos
    python main.py --help   # Muestra ayuda

Autor: Facebook Scraper
Version: 1.0.0
"""

import sys
import os
import argparse
from pathlib import Path

# Agregar src al path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))


def verificar_dependencias():
    """Verifica que las dependencias esten instaladas."""
    dependencias = [
        ('selenium', 'selenium'),
        ('customtkinter', 'customtkinter'),
        ('pandas', 'pandas'),
        ('PIL', 'Pillow'),
        ('openpyxl', 'openpyxl'),
        ('requests', 'requests'),
        ('loguru', 'loguru'),
        ('webdriver_manager', 'webdriver-manager')
    ]

    faltantes = []
    for modulo, nombre_pip in dependencias:
        try:
            __import__(modulo)
        except ImportError:
            faltantes.append(nombre_pip)

    if faltantes:
        print("=" * 50)
        print("DEPENDENCIAS FALTANTES")
        print("=" * 50)
        print("\nPor favor instala las siguientes dependencias:\n")
        print(f"  pip install {' '.join(faltantes)}")
        print("\nO instala todas con:")
        print(f"  pip install -r requirements.txt")
        print("=" * 50)
        return False

    return True


def crear_estructura_carpetas():
    """Crea la estructura de carpetas necesaria."""
    carpetas = [
        BASE_DIR / "config",
        BASE_DIR / "input",
        BASE_DIR / "output" / "publicaciones",
        BASE_DIR / "output" / "reportes",
        BASE_DIR / "logs"
    ]

    for carpeta in carpetas:
        carpeta.mkdir(parents=True, exist_ok=True)


def iniciar_gui():
    """Inicia la interfaz grafica."""
    try:
        from src.gui import FacebookScraperGUI

        print("Iniciando interfaz grafica...")
        app = FacebookScraperGUI()
        app.mainloop()

    except ImportError as e:
        print(f"Error importando modulos: {e}")
        print("Asegurate de haber instalado las dependencias.")
        sys.exit(1)
    except Exception as e:
        print(f"Error iniciando la aplicacion: {e}")
        sys.exit(1)


def ejecutar_cli(args):
    """Ejecuta el scraper en modo CLI."""
    from src.scraper import FacebookScraper
    from src.excel_generator import ExcelGenerator
    from src.utils import leer_urls_desde_archivo, cargar_configuracion
    from loguru import logger

    # Configurar logger
    logger.add(
        BASE_DIR / "logs" / "ejecuciones.log",
        rotation="10 MB",
        retention="30 days",
        level="INFO"
    )

    print("=" * 50)
    print(" FACEBOOK SCRAPER - Modo CLI")
    print("=" * 50)

    # Cargar URLs
    if args.urls:
        urls = leer_urls_desde_archivo(args.urls)
    else:
        archivo_default = BASE_DIR / "input" / "urls_facebook.txt"
        if archivo_default.exists():
            urls = leer_urls_desde_archivo(str(archivo_default))
        else:
            print("\nError: No se especifico archivo de URLs.")
            print(f"Usa: python main.py --cli --urls <archivo>")
            print(f"O crea: {archivo_default}")
            sys.exit(1)

    if not urls:
        print("\nNo hay URLs validas para procesar.")
        sys.exit(1)

    print(f"\nURLs a procesar: {len(urls)}")
    print(f"Modo headless: {args.headless}")
    print("")

    # Cargar configuracion
    config = cargar_configuracion(str(BASE_DIR / "config" / "settings.json"))

    # Crear scraper
    scraper = FacebookScraper(str(BASE_DIR), config)

    # Ejecutar
    try:
        estadisticas = scraper.ejecutar_scraping(urls, args.headless)

        # Generar Excel
        resultados = scraper.obtener_resultados()
        if resultados:
            excel_gen = ExcelGenerator()
            ruta_excel = BASE_DIR / "output" / "metadata_master.xlsx"
            excel_gen.generar_excel(resultados, ruta_excel)
            excel_gen.agregar_hoja_resumen(ruta_excel, estadisticas)

        # Mostrar resumen
        print("\n" + "=" * 50)
        print(" RESUMEN")
        print("=" * 50)
        print(f"  URLs procesadas: {estadisticas['total']}")
        print(f"  Exitosas: {estadisticas['exitosas']}")
        print(f"  Fallidas: {estadisticas['fallidas']}")
        print(f"  Tasa de exito: {estadisticas['tasa_exito']:.1f}%")
        print(f"  Duracion: {estadisticas['duracion']}")
        print("=" * 50)

    except KeyboardInterrupt:
        print("\n\nScraping cancelado por el usuario.")
        scraper.detener()
    except Exception as e:
        print(f"\nError durante el scraping: {e}")
        sys.exit(1)


def main():
    """Funcion principal."""
    parser = argparse.ArgumentParser(
        description="Facebook Scraper - Extractor de publicaciones con descarga local",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main.py                    # Inicia la GUI
  python main.py --cli              # Modo CLI con archivo por defecto
  python main.py --cli --urls mi_archivo.txt
  python main.py --cli --headless   # Sin interfaz del navegador
        """
    )

    parser.add_argument(
        '--cli',
        action='store_true',
        help='Ejecutar en modo linea de comandos (sin GUI)'
    )

    parser.add_argument(
        '--urls',
        type=str,
        help='Archivo con URLs a procesar (una por linea)'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        help='Ejecutar navegador sin interfaz grafica'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Facebook Scraper v1.0.0'
    )

    args = parser.parse_args()

    # Verificar dependencias
    if not verificar_dependencias():
        sys.exit(1)

    # Crear estructura de carpetas
    crear_estructura_carpetas()

    # Ejecutar segun modo
    if args.cli:
        ejecutar_cli(args)
    else:
        iniciar_gui()


if __name__ == "__main__":
    main()
