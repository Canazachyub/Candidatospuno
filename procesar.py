#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
procesar.py - Procesador de Candidatos con DeepSeek AI
Analiza los metadata.json del scraping y genera fichas estructuradas + dashboard

Uso:
    python procesar.py          # Abre la GUI
    python procesar.py --cli    # Modo línea de comandos
    python procesar.py --all    # Reprocesar todos (CLI)
"""

import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.processor_gui import main as gui_main
from src.candidate_processor import CandidateProcessor
from src.dashboard_generator import DashboardGenerator


def main_cli(reprocesar_todos: bool = False):
    """Ejecuta el procesador en modo CLI."""
    print("=" * 50)
    print("  PROCESADOR DE CANDIDATOS - DeepSeek AI")
    print("=" * 50)
    print()

    processor = CandidateProcessor()

    # Mostrar estadísticas
    pendientes = len(processor.get_pending_folders())
    total = len(processor.get_all_folders())

    print(f"Total de publicaciones: {total}")
    print(f"Ya procesadas: {total - pendientes}")
    print(f"Pendientes: {pendientes}")
    print()

    if pendientes == 0 and not reprocesar_todos:
        print("No hay publicaciones pendientes de procesar.")
        print("Usa --all para reprocesar todas.")
        return

    # Confirmar
    modo = "TODAS" if reprocesar_todos else f"{pendientes} pendientes"
    confirmacion = input(f"¿Procesar {modo} publicaciones? (s/n): ")

    if confirmacion.lower() != 's':
        print("Cancelado.")
        return

    print()
    print("Iniciando procesamiento...")
    print("-" * 50)

    # Procesar
    processor.process_all(solo_pendientes=not reprocesar_todos)

    print()
    print("-" * 50)
    print(f"Procesamiento completado.")
    print(f"Exitosos: {processor.processed_count}")
    print(f"Errores: {processor.error_count}")
    print()

    # Preguntar si generar dashboard
    generar = input("¿Generar dashboard HTML? (s/n): ")
    if generar.lower() == 's':
        print("Generando dashboard...")
        generator = DashboardGenerator()
        path = generator.generate_dashboard()
        print(f"Dashboard generado: {path}")

        # Abrir en navegador
        import webbrowser
        webbrowser.open(path)


def main():
    """Punto de entrada principal."""
    if len(sys.argv) > 1:
        if '--cli' in sys.argv:
            main_cli(reprocesar_todos='--all' in sys.argv)
        elif '--all' in sys.argv:
            main_cli(reprocesar_todos=True)
        elif '--dashboard' in sys.argv:
            print("Generando dashboard...")
            generator = DashboardGenerator()
            path = generator.generate_dashboard()
            print(f"Dashboard generado: {path}")
            import webbrowser
            webbrowser.open(path)
        elif '--help' in sys.argv or '-h' in sys.argv:
            print(__doc__)
        else:
            gui_main()
    else:
        gui_main()


if __name__ == "__main__":
    main()
