"""
utils.py - Funciones auxiliares para el scraper de Facebook
"""

import re
import os
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from typing import Optional, List, Dict, Any
from pathlib import Path


def extraer_id_publicacion(url: str) -> Optional[str]:
    """
    Extrae el ID de publicacion de una URL de Facebook.

    Args:
        url: URL completa de Facebook

    Returns:
        ID de la publicacion o None si no se encuentra
    """
    try:
        # Patron para fbid en la URL
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        if 'fbid' in params:
            return params['fbid'][0]

        # Patron alternativo en el path
        match = re.search(r'/(\d{15,20})', url)
        if match:
            return match.group(1)

        # Patron para posts
        match = re.search(r'posts/(\d+)', url)
        if match:
            return match.group(1)

        return None
    except Exception:
        return None


def extraer_hashtags(texto: str) -> List[str]:
    """
    Extrae todos los hashtags de un texto.

    Args:
        texto: Texto donde buscar hashtags

    Returns:
        Lista de hashtags encontrados (sin duplicados)
    """
    if not texto:
        return []

    # Patron para hashtags
    patron = r'#[\wáéíóúñÁÉÍÓÚÑ]+'
    hashtags = re.findall(patron, texto, re.UNICODE)

    # Eliminar duplicados manteniendo orden
    vistos = set()
    resultado = []
    for tag in hashtags:
        if tag.lower() not in vistos:
            vistos.add(tag.lower())
            resultado.append(tag)

    return resultado


def limpiar_texto(texto: str) -> str:
    """
    Limpia un texto eliminando caracteres problematicos.

    Args:
        texto: Texto a limpiar

    Returns:
        Texto limpio
    """
    if not texto:
        return ""

    # Eliminar caracteres de control
    texto = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', texto)

    # Normalizar espacios
    texto = re.sub(r'\s+', ' ', texto)

    # Eliminar espacios al inicio y final
    texto = texto.strip()

    return texto


def limpiar_nombre_archivo(nombre: str, max_length: int = 50) -> str:
    """
    Limpia un nombre para usarlo como nombre de archivo.

    Args:
        nombre: Nombre original
        max_length: Longitud maxima

    Returns:
        Nombre limpio para archivo
    """
    if not nombre:
        return "sin_nombre"

    # Caracteres no permitidos en nombres de archivo
    caracteres_invalidos = r'[<>:"/\\|?*\x00-\x1f]'
    nombre = re.sub(caracteres_invalidos, '', nombre)

    # Reemplazar espacios por guiones bajos
    nombre = nombre.replace(' ', '_')

    # Limitar longitud
    if len(nombre) > max_length:
        nombre = nombre[:max_length]

    return nombre or "sin_nombre"


def parsear_numero(texto: str) -> int:
    """
    Extrae un numero de un texto.

    Args:
        texto: Texto que contiene un numero

    Returns:
        Numero extraido o 0
    """
    if not texto:
        return 0

    # Buscar numeros en el texto
    numeros = re.findall(r'\d+', texto.replace(',', '').replace('.', ''))

    if numeros:
        return int(numeros[0])

    return 0


def formatear_fecha(fecha_str: str) -> str:
    """
    Normaliza una fecha al formato YYYY-MM-DD.

    Args:
        fecha_str: Fecha en cualquier formato

    Returns:
        Fecha formateada o fecha actual si falla
    """
    fecha_actual = datetime.now().strftime('%Y-%m-%d')

    if not fecha_str:
        return fecha_actual

    # Intentar extraer fecha
    meses = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
        'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 'ago': '08',
        'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'
    }

    fecha_lower = fecha_str.lower()

    for mes_nombre, mes_num in meses.items():
        if mes_nombre in fecha_lower:
            # Buscar dia
            dia_match = re.search(r'(\d{1,2})', fecha_str)
            if dia_match:
                dia = dia_match.group(1).zfill(2)
                # Buscar ano
                ano_match = re.search(r'20\d{2}', fecha_str)
                ano = ano_match.group(0) if ano_match else datetime.now().strftime('%Y')
                return f"{ano}-{mes_num}-{dia}"

    return fecha_actual


def validar_url_facebook(url: str) -> bool:
    """
    Valida que una URL sea de Facebook.

    Args:
        url: URL a validar

    Returns:
        True si es valida, False si no
    """
    if not url:
        return False

    url = url.strip().lower()

    # Verificar que sea de Facebook
    patrones_validos = [
        'facebook.com',
        'fb.com',
        'fb.watch'
    ]

    return any(patron in url for patron in patrones_validos)


def generar_timestamp() -> str:
    """
    Genera un timestamp actual formateado.

    Returns:
        Timestamp en formato YYYY-MM-DD HH:MM:SS
    """
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def generar_nombre_carpeta(fecha: str, id_publicacion: str) -> str:
    """
    Genera el nombre de carpeta para una publicacion.

    Args:
        fecha: Fecha de la publicacion (YYYY-MM-DD)
        id_publicacion: ID de la publicacion

    Returns:
        Nombre de carpeta formateado
    """
    fecha_limpia = fecha.replace('/', '-').replace('\\', '-')
    return f"{fecha_limpia}_{id_publicacion}"


def cargar_configuracion(ruta_config: str) -> Dict[str, Any]:
    """
    Carga la configuracion desde un archivo JSON.

    Args:
        ruta_config: Ruta al archivo de configuracion

    Returns:
        Diccionario con la configuracion
    """
    config_default = {
        "scraper": {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "window_size": [1920, 1080],
            "page_load_timeout": 30,
            "implicit_wait": 10
        },
        "delays": {
            "min_delay": 3,
            "max_delay": 7
        },
        "download": {
            "timeout": 30,
            "max_retries": 3
        }
    }

    try:
        with open(ruta_config, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Mezclar con valores por defecto
            return {**config_default, **config}
    except FileNotFoundError:
        return config_default
    except json.JSONDecodeError:
        return config_default


def formatear_duracion(segundos: float) -> str:
    """
    Formatea una duracion en segundos a un formato legible.

    Args:
        segundos: Duracion en segundos

    Returns:
        Duracion formateada (ej: "5 min 30 seg")
    """
    if segundos < 60:
        return f"{int(segundos)} seg"
    elif segundos < 3600:
        minutos = int(segundos // 60)
        segs = int(segundos % 60)
        return f"{minutos} min {segs} seg"
    else:
        horas = int(segundos // 3600)
        minutos = int((segundos % 3600) // 60)
        return f"{horas} h {minutos} min"


def leer_urls_desde_archivo(ruta_archivo: str) -> List[str]:
    """
    Lee URLs desde un archivo de texto.

    Args:
        ruta_archivo: Ruta al archivo con URLs

    Returns:
        Lista de URLs validas
    """
    urls = []

    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            for linea in f:
                linea = linea.strip()
                # Ignorar lineas vacias y comentarios
                if linea and not linea.startswith('#'):
                    if validar_url_facebook(linea):
                        urls.append(linea)
    except FileNotFoundError:
        pass

    # Eliminar duplicados manteniendo orden
    vistos = set()
    urls_unicas = []
    for url in urls:
        id_pub = extraer_id_publicacion(url)
        if id_pub and id_pub not in vistos:
            vistos.add(id_pub)
            urls_unicas.append(url)
        elif not id_pub and url not in vistos:
            vistos.add(url)
            urls_unicas.append(url)

    return urls_unicas
