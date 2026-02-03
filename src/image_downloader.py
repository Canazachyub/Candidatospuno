"""
image_downloader.py - Descarga y procesamiento de imagenes
"""

import os
import requests
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
from io import BytesIO
from loguru import logger


class ImageDownloader:
    """Gestiona la descarga y validacion de imagenes."""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Inicializa el descargador de imagenes.

        Args:
            timeout: Tiempo maximo de espera en segundos
            max_retries: Numero maximo de reintentos
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()

        # Headers para simular navegador
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Referer': 'https://www.facebook.com/'
        }
        self.session.headers.update(self.headers)

    def descargar_imagen(self, url: str, carpeta_destino: Path,
                         nombre_archivo: str = "imagen") -> Tuple[bool, str, int]:
        """
        Descarga una imagen desde una URL.

        Args:
            url: URL de la imagen
            carpeta_destino: Carpeta donde guardar
            nombre_archivo: Nombre base del archivo

        Returns:
            Tuple (exito, ruta_archivo, tamano_bytes)
        """
        if not url:
            return False, "", 0

        for intento in range(self.max_retries):
            try:
                # Hacer request
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    stream=True
                )
                response.raise_for_status()

                # Determinar extension
                content_type = response.headers.get('Content-Type', '')
                extension = self._obtener_extension(content_type, url)

                # Nombre completo del archivo
                nombre_completo = f"{nombre_archivo}.{extension}"
                ruta_archivo = carpeta_destino / nombre_completo

                # Guardar imagen
                with open(ruta_archivo, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                # Validar imagen
                if self._validar_imagen(ruta_archivo):
                    tamano = ruta_archivo.stat().st_size
                    logger.info(f"Imagen descargada: {nombre_completo} ({tamano / 1024:.1f} KB)")
                    return True, str(ruta_archivo), tamano
                else:
                    ruta_archivo.unlink(missing_ok=True)
                    logger.warning(f"Imagen corrupta, reintentando... ({intento + 1}/{self.max_retries})")

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout descargando imagen ({intento + 1}/{self.max_retries})")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error de conexion: {e} ({intento + 1}/{self.max_retries})")
            except Exception as e:
                logger.error(f"Error inesperado: {e}")
                break

        return False, "", 0

    def _obtener_extension(self, content_type: str, url: str) -> str:
        """
        Determina la extension del archivo basandose en el content-type.

        Args:
            content_type: Tipo MIME
            url: URL de la imagen

        Returns:
            Extension del archivo
        """
        # Mapeo de content-type a extension
        mapa_extensiones = {
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/png': 'png',
            'image/gif': 'gif',
            'image/webp': 'webp',
            'image/avif': 'avif'
        }

        # Intentar por content-type
        for tipo, ext in mapa_extensiones.items():
            if tipo in content_type.lower():
                return ext

        # Intentar por URL
        url_lower = url.lower()
        for ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            if f'.{ext}' in url_lower:
                return ext if ext != 'jpeg' else 'jpg'

        # Por defecto
        return 'jpg'

    def _validar_imagen(self, ruta: Path) -> bool:
        """
        Valida que el archivo sea una imagen valida.

        Args:
            ruta: Ruta al archivo de imagen

        Returns:
            True si es valida
        """
        try:
            # Verificar que existe y tiene tamano
            if not ruta.exists():
                return False

            if ruta.stat().st_size < 1024:  # Menos de 1KB
                return False

            # Intentar abrir con PIL
            with Image.open(ruta) as img:
                img.verify()

            return True
        except Exception:
            return False

    def descargar_y_convertir(self, url: str, carpeta_destino: Path,
                               nombre_archivo: str = "imagen",
                               formato_destino: str = "jpg") -> Tuple[bool, str, int]:
        """
        Descarga y convierte una imagen al formato especificado.

        Args:
            url: URL de la imagen
            carpeta_destino: Carpeta destino
            nombre_archivo: Nombre base
            formato_destino: Formato de salida (jpg, png)

        Returns:
            Tuple (exito, ruta_archivo, tamano_bytes)
        """
        # Primero descargar
        exito, ruta_temp, _ = self.descargar_imagen(url, carpeta_destino, nombre_archivo)

        if not exito:
            return False, "", 0

        ruta_temp = Path(ruta_temp)

        # Si ya esta en el formato correcto
        if ruta_temp.suffix.lower() == f'.{formato_destino}':
            return True, str(ruta_temp), ruta_temp.stat().st_size

        # Convertir
        try:
            with Image.open(ruta_temp) as img:
                # Convertir a RGB si es necesario (para JPG)
                if formato_destino.lower() == 'jpg' and img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                ruta_final = carpeta_destino / f"{nombre_archivo}.{formato_destino}"
                img.save(ruta_final, quality=95, optimize=True)

                # Eliminar original si es diferente
                if ruta_temp != ruta_final:
                    ruta_temp.unlink(missing_ok=True)

                tamano = ruta_final.stat().st_size
                return True, str(ruta_final), tamano

        except Exception as e:
            logger.error(f"Error convirtiendo imagen: {e}")
            return True, str(ruta_temp), ruta_temp.stat().st_size

    def obtener_info_imagen(self, ruta: Path) -> Optional[dict]:
        """
        Obtiene informacion de una imagen.

        Args:
            ruta: Ruta a la imagen

        Returns:
            Diccionario con info o None
        """
        try:
            with Image.open(ruta) as img:
                return {
                    'ancho': img.width,
                    'alto': img.height,
                    'formato': img.format,
                    'modo': img.mode,
                    'tamano_bytes': ruta.stat().st_size
                }
        except Exception:
            return None

    def cerrar(self):
        """Cierra la sesion de requests."""
        self.session.close()
