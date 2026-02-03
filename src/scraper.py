"""
scraper.py - Logica principal de scraping con Selenium
"""

import time
import random
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger

from .utils import (
    extraer_id_publicacion,
    extraer_hashtags,
    limpiar_texto,
    formatear_fecha,
    generar_timestamp,
    generar_nombre_carpeta,
    parsear_numero
)
from .file_manager import FileManager
from .image_downloader import ImageDownloader


class FacebookScraper:
    """Scraper de publicaciones de Facebook usando Selenium."""

    def __init__(self, base_path: str, config: Dict[str, Any] = None):
        """
        Inicializa el scraper.

        Args:
            base_path: Ruta base del proyecto
            config: Configuracion opcional
        """
        self.base_path = Path(base_path)
        self.config = config or {}
        self.driver = None
        self.file_manager = FileManager(base_path)
        self.image_downloader = ImageDownloader(
            timeout=self.config.get('download', {}).get('timeout', 30),
            max_retries=self.config.get('download', {}).get('max_retries', 3)
        )

        # Ruta al archivo de cookies
        self.cookies_path = self.base_path / "config" / "facebook_cookies.txt"

        # Callbacks para la GUI
        self.on_progress: Optional[Callable] = None
        self.on_log: Optional[Callable] = None
        self.on_complete: Optional[Callable] = None

        # Estado
        self.running = False
        self.resultados: List[Dict[str, Any]] = []

    def _cargar_cookies_netscape(self) -> List[Dict[str, Any]]:
        """
        Carga cookies desde un archivo en formato Netscape.

        Returns:
            Lista de diccionarios con las cookies
        """
        cookies = []

        if not self.cookies_path.exists():
            self.log("Archivo de cookies no encontrado", "warning")
            return cookies

        try:
            with open(self.cookies_path, 'r', encoding='utf-8') as f:
                for linea in f:
                    linea = linea.strip()
                    # Ignorar comentarios y lineas vacias
                    if not linea or linea.startswith('#'):
                        continue

                    partes = linea.split('\t')
                    if len(partes) >= 7:
                        cookie = {
                            'domain': partes[0],
                            'path': partes[2],
                            'secure': partes[3].upper() == 'TRUE',
                            'expiry': int(partes[4]) if partes[4] != '0' else None,
                            'name': partes[5],
                            'value': partes[6]
                        }
                        # Eliminar expiry si es None (cookie de sesion)
                        if cookie['expiry'] is None:
                            del cookie['expiry']
                        cookies.append(cookie)

            self.log(f"Cargadas {len(cookies)} cookies desde archivo")
        except Exception as e:
            self.log(f"Error cargando cookies: {e}", "error")

        return cookies

    def _inyectar_cookies(self) -> bool:
        """
        Inyecta las cookies en el navegador.

        Returns:
            True si se inyectaron correctamente
        """
        try:
            # Primero navegar a Facebook para poder agregar cookies del dominio
            self.log("Navegando a Facebook para inyectar cookies...")
            self.driver.get("https://www.facebook.com")
            time.sleep(3)

            # Cargar cookies
            cookies = self._cargar_cookies_netscape()
            if not cookies:
                self.log("No hay cookies para inyectar", "warning")
                return False

            # Inyectar cada cookie
            cookies_inyectadas = 0
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                    cookies_inyectadas += 1
                except Exception as e:
                    # Algunas cookies pueden fallar, es normal
                    pass

            self.log(f"Cookies inyectadas: {cookies_inyectadas}/{len(cookies)}")

            # Refrescar para aplicar cookies
            self.driver.refresh()
            time.sleep(3)

            # Verificar si estamos logueados
            if self._verificar_sesion():
                self.log("Sesion de Facebook activa - Autenticado correctamente")
                return True
            else:
                self.log("No se pudo verificar la sesion", "warning")
                return False

        except Exception as e:
            self.log(f"Error inyectando cookies: {e}", "error")
            return False

    def _verificar_sesion(self) -> bool:
        """
        Verifica si hay una sesion activa en Facebook.

        Returns:
            True si hay sesion activa
        """
        try:
            # Buscar elementos que solo aparecen cuando estas logueado
            indicadores_login = [
                "div[aria-label='Tu perfil']",
                "div[aria-label='Cuenta']",
                "div[aria-label='Menu']",
                "svg[aria-label='Tu perfil']",
                "a[href*='/me/']"
            ]

            for selector in indicadores_login:
                try:
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elementos:
                        return True
                except:
                    continue

            # Verificar que NO estemos en la pagina de login
            url_actual = self.driver.current_url.lower()
            if 'login' in url_actual or 'checkpoint' in url_actual:
                return False

            # Si la URL contiene facebook.com y no es login, probablemente estamos bien
            if 'facebook.com' in url_actual and 'login' not in url_actual:
                return True

            return False

        except Exception:
            return False

    def log(self, mensaje: str, nivel: str = "info"):
        """Registra un mensaje y lo envia al callback si existe."""
        if nivel == "info":
            logger.info(mensaje)
        elif nivel == "error":
            logger.error(mensaje)
        elif nivel == "warning":
            logger.warning(mensaje)

        if self.on_log:
            self.on_log(mensaje, nivel)

    def iniciar_navegador(self, headless: bool = False) -> bool:
        """
        Inicializa el navegador Chrome con Selenium.

        Args:
            headless: Si es True, ejecuta sin interfaz grafica

        Returns:
            True si se inicio correctamente
        """
        try:
            options = Options()

            # Configuracion basica
            user_agent = self.config.get('scraper', {}).get(
                'user_agent',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            options.add_argument(f'--user-agent={user_agent}')

            # Tamano de ventana
            window_size = self.config.get('scraper', {}).get('window_size', [1920, 1080])
            options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')

            # Opciones anti-deteccion
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)

            # Otras opciones
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-infobars')
            options.add_argument('--lang=es-ES')

            # Modo headless
            if headless:
                options.add_argument('--headless=new')
                options.add_argument('--disable-gpu')

            # Iniciar driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

            # Configurar timeouts
            timeout = self.config.get('scraper', {}).get('page_load_timeout', 30)
            self.driver.set_page_load_timeout(timeout)

            implicit_wait = self.config.get('scraper', {}).get('implicit_wait', 10)
            self.driver.implicitly_wait(implicit_wait)

            # Eliminar bandera webdriver
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            self.log("Navegador iniciado correctamente")

            # Inyectar cookies de Facebook
            if self.cookies_path.exists():
                self._inyectar_cookies()
            else:
                self.log("No se encontro archivo de cookies - Se requiere login manual", "warning")

            return True

        except Exception as e:
            self.log(f"Error iniciando navegador: {e}", "error")
            return False

    def cerrar_navegador(self):
        """Cierra el navegador."""
        if self.driver:
            try:
                self.driver.quit()
                self.log("Navegador cerrado")
            except Exception:
                pass
            self.driver = None

    def delay_aleatorio(self, min_delay: float = None, max_delay: float = None):
        """Pausa con delay aleatorio para simular comportamiento humano."""
        min_d = min_delay or self.config.get('delays', {}).get('min_delay', 3)
        max_d = max_delay or self.config.get('delays', {}).get('max_delay', 7)
        delay = random.uniform(min_d, max_d)
        time.sleep(delay)

    def scroll_suave(self, pixels: int = 500):
        """Hace scroll suave en la pagina."""
        try:
            self.driver.execute_script(f"window.scrollBy(0, {pixels});")
            time.sleep(0.5)
        except Exception:
            pass

    def _cerrar_popups(self):
        """Cierra popups y modales molestos de Facebook."""
        try:
            # Cerrar popup de cookies
            selectores_cerrar = [
                "button[data-cookiebanner='accept_button']",
                "button[title='Aceptar todas']",
                "button[title='Allow all cookies']",
                "div[aria-label='Cerrar']",
                "div[aria-label='Close']",
                "button[aria-label='Cerrar']",
                "button[aria-label='Close']"
            ]

            for selector in selectores_cerrar:
                try:
                    botones = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for boton in botones:
                        if boton.is_displayed():
                            boton.click()
                            time.sleep(0.5)
                            break
                except:
                    continue

            # Cerrar modal de login si aparece
            try:
                close_buttons = self.driver.find_elements(
                    By.XPATH,
                    "//div[@role='dialog']//div[@aria-label='Cerrar' or @aria-label='Close']"
                )
                for btn in close_buttons:
                    if btn.is_displayed():
                        btn.click()
                        time.sleep(0.5)
            except:
                pass

        except Exception:
            pass

    def extraer_datos_publicacion(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extrae todos los datos de una publicacion.

        Args:
            url: URL de la publicacion

        Returns:
            Diccionario con los datos o None si falla
        """
        try:
            # Navegar a la URL
            self.driver.get(url)
            time.sleep(self.config.get('delays', {}).get('page_load_wait', 5))

            # Cerrar popups molestos
            self._cerrar_popups()

            # Scroll para cargar contenido lazy
            self.scroll_suave(300)
            time.sleep(1)
            self.scroll_suave(-200)
            time.sleep(1)

            # Extraer ID
            id_publicacion = extraer_id_publicacion(url)
            if not id_publicacion:
                id_publicacion = datetime.now().strftime('%Y%m%d%H%M%S')

            # Extraer datos
            datos = {
                'url_publicacion': url,
                'id_publicacion': id_publicacion,
                'pagina': self._extraer_nombre_pagina(),
                'fecha_publicacion': self._extraer_fecha(),
                'fecha_scraping': generar_timestamp(),
                'descripcion_completa': self._extraer_descripcion(),
                'titulo': '',
                'hashtags': [],
                'imagen_url': self._extraer_url_imagen(),
                'reacciones': self._extraer_reacciones(),
                'comentarios': self._extraer_comentarios(),
                'compartidos': self._extraer_compartidos(),
                'visibilidad': 'Publico'
            }

            # Procesar descripcion
            if datos['descripcion_completa']:
                # Titulo: primera linea o primeros 200 caracteres
                lineas = datos['descripcion_completa'].split('\n')
                datos['titulo'] = limpiar_texto(lineas[0][:200] if lineas else '')
                datos['hashtags'] = extraer_hashtags(datos['descripcion_completa'])

            return datos

        except TimeoutException:
            self.log(f"Timeout cargando: {url}", "warning")
            return None
        except Exception as e:
            self.log(f"Error extrayendo datos: {e}", "error")
            return None

    def _extraer_nombre_pagina(self) -> str:
        """Extrae el nombre de la pagina de Facebook."""
        selectores = [
            # Selectores para el nombre de la pagina en posts
            "h2 a strong span",
            "h2 a span",
            "h2 span a strong",
            # Selectores para paginas
            "[data-ad-rendering-role='profile_name'] span a",
            "a[aria-label] strong span",
            # Selectores alternativos
            "span.xt0psk2 a strong",
            "a[role='link'] strong span",
            "h2 strong span",
            # Link del perfil/pagina
            "a[href*='/profile.php'] span",
            "a[href*='facebook.com/'][role='link'] strong"
        ]

        for selector in selectores:
            try:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elemento in elementos:
                    nombre = elemento.text.strip()
                    # Validar que sea un nombre real (no botones, no muy corto)
                    if (nombre and
                        len(nombre) > 2 and
                        len(nombre) < 100 and
                        nombre.lower() not in ['me gusta', 'compartir', 'comentar', 'seguir']):
                        return nombre
            except:
                continue

        # Metodo alternativo: buscar el primer h2 con un link
        try:
            h2_elements = self.driver.find_elements(By.CSS_SELECTOR, "h2 a")
            for h2 in h2_elements:
                texto = h2.text.strip()
                if texto and len(texto) > 2:
                    return texto
        except:
            pass

        return "Pagina Desconocida"

    def _extraer_fecha(self) -> str:
        """Extrae la fecha de publicacion."""
        selectores = [
            "a[aria-label*='·'] span",
            "span[id*='jsc'] a",
            "abbr[data-utime]",
            "span.x4k7w5x a"
        ]

        for selector in selectores:
            try:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elementos:
                    texto = elem.text.strip()
                    # Buscar patrones de fecha
                    if any(p in texto.lower() for p in ['enero', 'febrero', 'marzo', 'abril',
                                                         'mayo', 'junio', 'julio', 'agosto',
                                                         'septiembre', 'octubre', 'noviembre', 'diciembre',
                                                         'ayer', 'hoy', 'hora', 'min']):
                        return texto
            except NoSuchElementException:
                continue

        return datetime.now().strftime('%d de %B de %Y')

    def _expandir_ver_mas(self):
        """Hace clic en 'Ver más' para expandir el texto completo."""
        try:
            # Selectores para el boton "Ver más"
            selectores_ver_mas = [
                "div[role='button']:contains('Ver más')",
                "span:contains('Ver más')",
                "div.x1i10hfl[role='button']"
            ]

            # Buscar con XPath que es mas preciso para texto
            ver_mas_xpath = [
                "//div[@role='button' and contains(text(), 'Ver más')]",
                "//div[@role='button' and contains(text(), 'See more')]",
                "//span[contains(text(), 'Ver más')]/parent::div[@role='button']",
                "//div[contains(@class, 'x1i10hfl') and contains(text(), 'Ver más')]"
            ]

            for xpath in ver_mas_xpath:
                try:
                    elementos = self.driver.find_elements(By.XPATH, xpath)
                    for elem in elementos:
                        if elem.is_displayed():
                            elem.click()
                            time.sleep(1)
                            self.log("  -> Expandido 'Ver más'")
                            return True
                except:
                    continue

            # Intento alternativo con JavaScript
            try:
                script = """
                var buttons = document.querySelectorAll('div[role="button"]');
                for (var btn of buttons) {
                    if (btn.textContent.trim() === 'Ver más' || btn.textContent.trim() === 'See more') {
                        btn.click();
                        return true;
                    }
                }
                return false;
                """
                resultado = self.driver.execute_script(script)
                if resultado:
                    time.sleep(1)
                    self.log("  -> Expandido 'Ver más' (JS)")
                    return True
            except:
                pass

        except Exception as e:
            pass

        return False

    def _extraer_descripcion(self) -> str:
        """Extrae la descripcion completa de la publicacion."""

        # Primero expandir "Ver más" si existe
        self._expandir_ver_mas()

        textos = []

        # Metodo 1: Usar JavaScript para extraer el texto del post (mas confiable)
        try:
            script = """
            // Buscar el span principal que contiene el texto del post
            var spans = document.querySelectorAll('span[dir="auto"]');
            var textos = [];

            for (var span of spans) {
                var texto = span.innerText || span.textContent;
                if (texto && texto.length > 100) {
                    // Verificar que contenga hashtags (indicador de post)
                    if (texto.includes('#EG2026') || texto.includes('#Puno') || texto.includes('#')) {
                        // Limpiar texto
                        texto = texto.replace(/Ver más$/g, '').replace(/Ver menos$/g, '').trim();
                        if (texto.length > 100) {
                            textos.push({text: texto, len: texto.length});
                        }
                    }
                }
            }

            // Ordenar por longitud y devolver el mas largo
            textos.sort((a, b) => b.len - a.len);
            return textos.length > 0 ? textos[0].text : '';
            """
            texto_js = self.driver.execute_script(script)
            if texto_js and len(texto_js) > 100:
                return limpiar_texto(texto_js)
        except Exception as e:
            pass

        # Metodo 2: Buscar con XPath spans que contengan hashtags
        try:
            elementos = self.driver.find_elements(
                By.XPATH,
                "//span[@dir='auto' and (contains(., '#EG2026') or contains(., '#Puno'))]"
            )
            for elem in elementos:
                texto = elem.text.strip()
                if texto and len(texto) > 100:
                    # Limpiar "Ver menos" o "Ver más"
                    texto = re.sub(r'Ver (más|menos)$', '', texto).strip()
                    if texto not in textos:
                        textos.append(texto)
        except:
            pass

        # Metodo 3: Selectores CSS tradicionales
        selectores = [
            "span.x193iq5w.xeuugli.x13faqbe[dir='auto']",
            "div[data-ad-comet-preview='message'] span[dir='auto']",
            "div.x1iorvi4 span[dir='auto']"
        ]

        for selector in selectores:
            try:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elementos:
                    texto = elem.text.strip()
                    if texto and len(texto) > 100 and texto not in textos:
                        texto = re.sub(r'Ver (más|menos)$', '', texto).strip()
                        textos.append(texto)
            except:
                continue

        if textos:
            # Tomar el texto mas largo
            descripcion = max(textos, key=len)
            return limpiar_texto(descripcion)

        return ""

    def _extraer_url_imagen(self) -> str:
        """Extrae la URL de la imagen principal."""
        selectores = [
            "img[data-visualcompletion='media-vc-image']",
            "img.x1ey2m1c",
            "img[src*='scontent']",
            "div[data-pagelet] img"
        ]

        for selector in selectores:
            try:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elementos:
                    src = elem.get_attribute('src')
                    if src and 'scontent' in src and 'emoji' not in src.lower():
                        # Preferir imagenes grandes
                        if 'p' in src or 's' in src:  # URLs de fotos
                            return src
            except NoSuchElementException:
                continue

        return ""

    def _extraer_reacciones(self) -> Dict[str, int]:
        """Extrae el conteo de reacciones."""
        reacciones = {
            'me_gusta': 0,
            'me_encanta': 0,
            'me_enoja': 0,
            'me_divierte': 0,
            'me_asombra': 0,
            'me_entristece': 0,
            'total': 0
        }

        try:
            # Buscar el total de reacciones
            selectores_total = [
                "span[aria-label*='reaccion']",
                "span.x1e558r4",
                "div[aria-label*='Me gusta'] span"
            ]

            for selector in selectores_total:
                try:
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elementos:
                        aria_label = elem.get_attribute('aria-label') or ''
                        texto = elem.text or aria_label

                        # Buscar numero
                        numeros = re.findall(r'\d+', texto.replace(',', ''))
                        if numeros:
                            total = int(numeros[0])
                            if total > reacciones['total']:
                                reacciones['total'] = total
                except Exception:
                    continue

            # Si encontramos total, asumimos son "me gusta" por defecto
            if reacciones['total'] > 0:
                reacciones['me_gusta'] = reacciones['total']

        except Exception as e:
            self.log(f"Error extrayendo reacciones: {e}", "warning")

        return reacciones

    def _extraer_comentarios(self) -> int:
        """Extrae el numero de comentarios."""
        try:
            selectores = [
                "span:contains('comentario')",
                "div[aria-label*='comentario']"
            ]

            # Buscar texto que contenga "comentario"
            elementos = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'comentario')]")
            for elem in elementos:
                texto = elem.text
                numeros = re.findall(r'(\d+)\s*comentario', texto.lower())
                if numeros:
                    return int(numeros[0])

        except Exception:
            pass

        return 0

    def _extraer_compartidos(self) -> int:
        """Extrae el numero de compartidos."""
        try:
            elementos = self.driver.find_elements(
                By.XPATH,
                "//*[contains(text(), 'compartido') or contains(text(), 'veces compartido')]"
            )
            for elem in elementos:
                texto = elem.text
                numeros = re.findall(r'(\d+)', texto)
                if numeros:
                    return int(numeros[0])

        except Exception:
            pass

        return 0

    def procesar_url(self, url: str, indice: int, total: int) -> Optional[Dict[str, Any]]:
        """
        Procesa una URL completa: extrae datos, descarga imagen, guarda archivos.

        Args:
            url: URL a procesar
            indice: Indice actual
            total: Total de URLs

        Returns:
            Diccionario con datos o None si falla
        """
        self.log(f"[{indice}/{total}] Procesando: {extraer_id_publicacion(url) or 'URL'}")

        # Actualizar progreso
        if self.on_progress:
            self.on_progress(indice, total, f"Procesando publicacion {indice}/{total}")

        try:
            # Extraer datos
            datos = self.extraer_datos_publicacion(url)
            if not datos:
                self.file_manager.agregar_url_fallida(url, "No se pudieron extraer datos")
                return None

            # Crear carpeta
            fecha_carpeta = formatear_fecha(datos['fecha_publicacion'])
            nombre_carpeta = generar_nombre_carpeta(fecha_carpeta, datos['id_publicacion'])
            carpeta = self.file_manager.crear_carpeta_publicacion(nombre_carpeta)

            # Descargar imagen
            imagen_local = ""
            if datos['imagen_url'] and self.config.get('download', {}).get('download_images', True):
                self.log(f"  -> Descargando imagen...")
                exito, ruta_imagen, tamano = self.image_downloader.descargar_imagen(
                    datos['imagen_url'],
                    carpeta,
                    "imagen"
                )
                if exito:
                    imagen_local = Path(ruta_imagen).name
                    self.log(f"  -> Imagen descargada ({tamano / 1024:.1f} KB)")
                else:
                    self.log(f"  -> No se pudo descargar la imagen", "warning")

            # Actualizar datos
            datos['imagen_local'] = imagen_local
            datos['carpeta'] = str(carpeta.relative_to(self.file_manager.output_path))

            # Guardar descripcion
            if datos['descripcion_completa']:
                self.file_manager.guardar_descripcion(carpeta, datos['descripcion_completa'])

            # Guardar metadata
            self.file_manager.guardar_metadata(carpeta, datos)

            # Registrar exito
            self.file_manager.agregar_url_exitosa(url)
            self.log(f"  -> Completado exitosamente")

            return datos

        except Exception as e:
            self.log(f"Error procesando {url}: {e}", "error")
            self.file_manager.agregar_url_fallida(url, str(e))
            return None

    def ejecutar_scraping(self, urls: List[str], headless: bool = False) -> Dict[str, Any]:
        """
        Ejecuta el scraping completo para una lista de URLs.

        Args:
            urls: Lista de URLs a procesar
            headless: Si ejecutar sin interfaz grafica

        Returns:
            Diccionario con estadisticas
        """
        self.running = True
        self.resultados = []
        inicio = datetime.now()

        estadisticas = {
            'total': len(urls),
            'exitosas': 0,
            'fallidas': 0,
            'imagenes': 0,
            'inicio': inicio.strftime('%Y-%m-%d %H:%M:%S'),
            'fin': '',
            'duracion': '',
            'tasa_exito': 0,
            'espacio_mb': 0
        }

        self.log(f"Iniciando scraping de {len(urls)} URLs...")

        # Iniciar navegador
        if not self.iniciar_navegador(headless):
            self.log("No se pudo iniciar el navegador", "error")
            self.running = False
            return estadisticas

        try:
            for i, url in enumerate(urls, 1):
                if not self.running:
                    self.log("Scraping cancelado por el usuario")
                    break

                resultado = self.procesar_url(url, i, len(urls))

                if resultado:
                    self.resultados.append(resultado)
                    estadisticas['exitosas'] += 1
                    if resultado.get('imagen_local'):
                        estadisticas['imagenes'] += 1
                else:
                    estadisticas['fallidas'] += 1

                # Delay entre URLs
                if i < len(urls):
                    self.delay_aleatorio()

        except Exception as e:
            self.log(f"Error durante el scraping: {e}", "error")

        finally:
            self.cerrar_navegador()

        # Calcular estadisticas finales
        fin = datetime.now()
        duracion = (fin - inicio).total_seconds()

        estadisticas['fin'] = fin.strftime('%Y-%m-%d %H:%M:%S')
        estadisticas['duracion'] = self._formatear_duracion(duracion)
        estadisticas['tasa_exito'] = (estadisticas['exitosas'] / estadisticas['total'] * 100) if estadisticas['total'] > 0 else 0
        estadisticas['espacio_mb'] = self.file_manager.calcular_espacio_usado()
        estadisticas['fecha'] = fin.strftime('%Y-%m-%d %H:%M:%S')

        # Generar reporte
        self.file_manager.generar_reporte(estadisticas)

        self.log(f"\nScraping completado: {estadisticas['exitosas']}/{estadisticas['total']} exitosas")
        self.running = False

        if self.on_complete:
            self.on_complete(estadisticas, self.resultados)

        return estadisticas

    def _formatear_duracion(self, segundos: float) -> str:
        """Formatea duracion en segundos a texto legible."""
        if segundos < 60:
            return f"{int(segundos)} seg"
        elif segundos < 3600:
            mins = int(segundos // 60)
            segs = int(segundos % 60)
            return f"{mins} min {segs} seg"
        else:
            horas = int(segundos // 3600)
            mins = int((segundos % 3600) // 60)
            return f"{horas} h {mins} min"

    def detener(self):
        """Detiene el scraping."""
        self.running = False
        self.log("Deteniendo scraping...")

    def obtener_resultados(self) -> List[Dict[str, Any]]:
        """Retorna los resultados del scraping."""
        return self.resultados
