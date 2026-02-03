"""
file_manager.py - Gestion de archivos y carpetas locales
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger


class FileManager:
    """Gestiona la creacion y escritura de archivos locales."""

    def __init__(self, base_path: str):
        """
        Inicializa el gestor de archivos.

        Args:
            base_path: Ruta base del proyecto
        """
        self.base_path = Path(base_path)
        self.output_path = self.base_path / "output"
        self.publicaciones_path = self.output_path / "publicaciones"
        self.reportes_path = self.output_path / "reportes"
        self.logs_path = self.base_path / "logs"

        # Crear estructura de carpetas
        self._crear_estructura()

    def _crear_estructura(self):
        """Crea la estructura de carpetas necesaria."""
        carpetas = [
            self.output_path,
            self.publicaciones_path,
            self.reportes_path,
            self.logs_path
        ]

        for carpeta in carpetas:
            carpeta.mkdir(parents=True, exist_ok=True)

    def crear_carpeta_publicacion(self, nombre_carpeta: str) -> Path:
        """
        Crea una carpeta para una publicacion.

        Args:
            nombre_carpeta: Nombre de la carpeta (fecha_id)

        Returns:
            Ruta a la carpeta creada
        """
        carpeta = self.publicaciones_path / nombre_carpeta

        # Si ya existe, agregar sufijo
        contador = 1
        carpeta_original = carpeta
        while carpeta.exists():
            carpeta = Path(f"{carpeta_original}_{contador}")
            contador += 1

        carpeta.mkdir(parents=True, exist_ok=True)
        return carpeta

    def guardar_descripcion(self, carpeta: Path, descripcion: str) -> bool:
        """
        Guarda la descripcion en un archivo TXT.

        Args:
            carpeta: Ruta a la carpeta de la publicacion
            descripcion: Texto de la descripcion

        Returns:
            True si se guardo correctamente
        """
        try:
            archivo = carpeta / "descripcion.txt"
            with open(archivo, 'w', encoding='utf-8-sig') as f:
                f.write(descripcion)
            return True
        except Exception as e:
            logger.error(f"Error guardando descripcion: {e}")
            return False

    def guardar_metadata(self, carpeta: Path, metadata: Dict[str, Any]) -> bool:
        """
        Guarda la metadata en un archivo JSON.

        Args:
            carpeta: Ruta a la carpeta de la publicacion
            metadata: Diccionario con la metadata

        Returns:
            True si se guardo correctamente
        """
        try:
            archivo = carpeta / "metadata.json"
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error guardando metadata: {e}")
            return False

    def agregar_url_exitosa(self, url: str):
        """Agrega una URL al archivo de URLs exitosas."""
        archivo = self.reportes_path / "urls_exitosas.txt"
        with open(archivo, 'a', encoding='utf-8') as f:
            f.write(f"{url}\n")

    def agregar_url_fallida(self, url: str, razon: str):
        """Agrega una URL al archivo de URLs fallidas."""
        archivo = self.reportes_path / "urls_fallidas.txt"
        with open(archivo, 'a', encoding='utf-8') as f:
            f.write(f"{url} | {razon}\n")

    def generar_reporte(self, estadisticas: Dict[str, Any]) -> str:
        """
        Genera un reporte de ejecucion.

        Args:
            estadisticas: Diccionario con estadisticas de la ejecucion

        Returns:
            Ruta al archivo de reporte
        """
        fecha = datetime.now().strftime('%Y-%m-%d')
        archivo = self.reportes_path / f"scraping_{fecha}.log"

        contenido = f"""
============================================
 REPORTE DE SCRAPING - Facebook
 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
============================================

RESULTADOS:
- URLs procesadas: {estadisticas.get('total', 0)}
- Exitosas: {estadisticas.get('exitosas', 0)}
- Fallidas: {estadisticas.get('fallidas', 0)}
- Tasa de exito: {estadisticas.get('tasa_exito', 0):.1f}%

DESCARGAS:
- Imagenes descargadas: {estadisticas.get('imagenes', 0)}
- Espacio usado: {estadisticas.get('espacio_mb', 0):.2f} MB

TIEMPO DE EJECUCION:
- Inicio: {estadisticas.get('inicio', 'N/A')}
- Fin: {estadisticas.get('fin', 'N/A')}
- Duracion: {estadisticas.get('duracion', 'N/A')}

ARCHIVOS GENERADOS:
- Excel maestro: output/metadata_master.xlsx
- Carpetas de publicaciones: {estadisticas.get('exitosas', 0)}

============================================
"""

        with open(archivo, 'w', encoding='utf-8') as f:
            f.write(contenido)

        return str(archivo)

    def obtener_ruta_excel(self) -> Path:
        """Retorna la ruta al archivo Excel maestro."""
        return self.output_path / "metadata_master.xlsx"

    def limpiar_reportes_antiguos(self, dias: int = 30):
        """
        Elimina reportes mas antiguos que X dias.

        Args:
            dias: Dias de antiguedad maxima
        """
        from datetime import timedelta

        fecha_limite = datetime.now() - timedelta(days=dias)

        for archivo in self.reportes_path.glob("*.log"):
            if archivo.stat().st_mtime < fecha_limite.timestamp():
                archivo.unlink()

    def contar_publicaciones(self) -> int:
        """Cuenta el numero de publicaciones descargadas."""
        return len(list(self.publicaciones_path.iterdir()))

    def calcular_espacio_usado(self) -> float:
        """
        Calcula el espacio usado en MB.

        Returns:
            Espacio en megabytes
        """
        total = 0
        for archivo in self.publicaciones_path.rglob("*"):
            if archivo.is_file():
                total += archivo.stat().st_size

        return total / (1024 * 1024)  # Convertir a MB
