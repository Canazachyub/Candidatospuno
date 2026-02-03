"""
gui.py - Interfaz grafica moderna con CustomTkinter
"""

import os
import sys
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import webbrowser

import customtkinter as ctk
from tkinter import filedialog, messagebox

# Configurar apariencia
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class FacebookScraperGUI(ctk.CTk):
    """Interfaz grafica principal del scraper."""

    def __init__(self):
        super().__init__()

        # Configuracion de la ventana
        self.title("Facebook Scraper - Extractor de Publicaciones")
        self.geometry("1000x700")
        self.minsize(800, 600)

        # Ruta base del proyecto
        self.base_path = Path(__file__).parent.parent
        self.config = self._cargar_config()

        # Variables
        self.urls: List[str] = []
        self.scraper = None
        self.scraping_thread = None
        self.is_running = False

        # Construir interfaz
        self._crear_widgets()

    def _cargar_config(self) -> Dict[str, Any]:
        """Carga la configuracion desde settings.json."""
        config_path = self.base_path / "config" / "settings.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _crear_widgets(self):
        """Crea todos los widgets de la interfaz."""
        # Configurar grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # === HEADER ===
        self._crear_header()

        # === TABS ===
        self._crear_tabs()

        # === FOOTER ===
        self._crear_footer()

    def _crear_header(self):
        """Crea el encabezado con titulo."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Titulo
        titulo = ctk.CTkLabel(
            header_frame,
            text="Facebook Scraper",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        titulo.pack(side="left")

        # Subtitulo
        subtitulo = ctk.CTkLabel(
            header_frame,
            text="Extractor de publicaciones con descarga local",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitulo.pack(side="left", padx=(15, 0))

    def _crear_tabs(self):
        """Crea el sistema de pestanas."""
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.grid_rowconfigure(1, weight=1)

        # Agregar tabs
        self.tab_urls = self.tabview.add("URLs")
        self.tab_config = self.tabview.add("Configuracion")
        self.tab_log = self.tabview.add("Log")
        self.tab_resultados = self.tabview.add("Resultados")

        # Construir contenido de cada tab
        self._crear_tab_urls()
        self._crear_tab_config()
        self._crear_tab_log()
        self._crear_tab_resultados()

    def _crear_tab_urls(self):
        """Crea la pestana de entrada de URLs."""
        self.tab_urls.grid_columnconfigure(0, weight=1)
        self.tab_urls.grid_rowconfigure(1, weight=1)

        # Frame de botones
        btn_frame = ctk.CTkFrame(self.tab_urls, fg_color="transparent")
        btn_frame.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        ctk.CTkButton(
            btn_frame,
            text="Cargar desde archivo",
            command=self._cargar_urls_archivo,
            width=150
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Pegar URLs",
            command=self._pegar_urls,
            width=100
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Limpiar",
            command=self._limpiar_urls,
            width=80,
            fg_color="gray"
        ).pack(side="left")

        # Contador de URLs
        self.lbl_contador = ctk.CTkLabel(
            btn_frame,
            text="0 URLs cargadas",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_contador.pack(side="right")

        # Textarea para URLs
        self.txt_urls = ctk.CTkTextbox(
            self.tab_urls,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="none"
        )
        self.txt_urls.grid(row=1, column=0, sticky="nsew")

        # Placeholder
        self.txt_urls.insert("1.0", "# Pega aqui las URLs de Facebook (una por linea)\n# Las lineas que empiezan con # son ignoradas\n\nhttps://www.facebook.com/photo.php?fbid=...\nhttps://www.facebook.com/photo.php?fbid=...")

    def _crear_tab_config(self):
        """Crea la pestana de configuracion."""
        self.tab_config.grid_columnconfigure(1, weight=1)

        # Frame scrollable
        scroll_frame = ctk.CTkScrollableFrame(self.tab_config)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        scroll_frame.grid_columnconfigure(1, weight=1)

        row = 0

        # === Seccion Navegador ===
        ctk.CTkLabel(
            scroll_frame,
            text="Navegador",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=row, column=0, columnspan=2, pady=(0, 10), sticky="w")
        row += 1

        # Modo headless
        self.var_headless = ctk.BooleanVar(value=False)
        ctk.CTkLabel(scroll_frame, text="Modo sin interfaz (headless):").grid(row=row, column=0, sticky="w", pady=5)
        ctk.CTkSwitch(scroll_frame, text="", variable=self.var_headless, width=50).grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        # === Seccion Delays ===
        ctk.CTkLabel(
            scroll_frame,
            text="\nDelays Anti-bloqueo",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=row, column=0, columnspan=2, pady=(10, 10), sticky="w")
        row += 1

        # Delay minimo
        ctk.CTkLabel(scroll_frame, text="Delay minimo (seg):").grid(row=row, column=0, sticky="w", pady=5)
        self.slider_delay_min = ctk.CTkSlider(scroll_frame, from_=1, to=10, number_of_steps=9)
        self.slider_delay_min.set(3)
        self.slider_delay_min.grid(row=row, column=1, sticky="ew", pady=5, padx=(0, 50))
        self.lbl_delay_min = ctk.CTkLabel(scroll_frame, text="3")
        self.lbl_delay_min.grid(row=row, column=1, sticky="e", pady=5)
        self.slider_delay_min.configure(command=lambda v: self.lbl_delay_min.configure(text=f"{int(v)}"))
        row += 1

        # Delay maximo
        ctk.CTkLabel(scroll_frame, text="Delay maximo (seg):").grid(row=row, column=0, sticky="w", pady=5)
        self.slider_delay_max = ctk.CTkSlider(scroll_frame, from_=3, to=15, number_of_steps=12)
        self.slider_delay_max.set(7)
        self.slider_delay_max.grid(row=row, column=1, sticky="ew", pady=5, padx=(0, 50))
        self.lbl_delay_max = ctk.CTkLabel(scroll_frame, text="7")
        self.lbl_delay_max.grid(row=row, column=1, sticky="e", pady=5)
        self.slider_delay_max.configure(command=lambda v: self.lbl_delay_max.configure(text=f"{int(v)}"))
        row += 1

        # === Seccion Descargas ===
        ctk.CTkLabel(
            scroll_frame,
            text="\nDescargas",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=row, column=0, columnspan=2, pady=(10, 10), sticky="w")
        row += 1

        # Descargar imagenes
        self.var_descargar_img = ctk.BooleanVar(value=True)
        ctk.CTkLabel(scroll_frame, text="Descargar imagenes:").grid(row=row, column=0, sticky="w", pady=5)
        ctk.CTkSwitch(scroll_frame, text="", variable=self.var_descargar_img, width=50).grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        # Max reintentos
        ctk.CTkLabel(scroll_frame, text="Reintentos maximos:").grid(row=row, column=0, sticky="w", pady=5)
        self.slider_reintentos = ctk.CTkSlider(scroll_frame, from_=1, to=5, number_of_steps=4)
        self.slider_reintentos.set(3)
        self.slider_reintentos.grid(row=row, column=1, sticky="ew", pady=5, padx=(0, 50))
        self.lbl_reintentos = ctk.CTkLabel(scroll_frame, text="3")
        self.lbl_reintentos.grid(row=row, column=1, sticky="e", pady=5)
        self.slider_reintentos.configure(command=lambda v: self.lbl_reintentos.configure(text=f"{int(v)}"))
        row += 1

        # === Seccion Salida ===
        ctk.CTkLabel(
            scroll_frame,
            text="\nCarpeta de Salida",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=row, column=0, columnspan=2, pady=(10, 10), sticky="w")
        row += 1

        # Ruta de salida
        output_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        output_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        output_frame.grid_columnconfigure(0, weight=1)

        self.entry_output = ctk.CTkEntry(output_frame, placeholder_text="Ruta de salida...")
        self.entry_output.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry_output.insert(0, str(self.base_path / "output"))

        ctk.CTkButton(
            output_frame,
            text="Examinar",
            command=self._seleccionar_carpeta_salida,
            width=80
        ).grid(row=0, column=1)

    def _crear_tab_log(self):
        """Crea la pestana de log."""
        self.tab_log.grid_columnconfigure(0, weight=1)
        self.tab_log.grid_rowconfigure(0, weight=1)

        # Textbox para logs
        self.txt_log = ctk.CTkTextbox(
            self.tab_log,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.txt_log.grid(row=0, column=0, sticky="nsew")
        self.txt_log.configure(state="disabled")

        # Frame de botones
        btn_frame = ctk.CTkFrame(self.tab_log, fg_color="transparent")
        btn_frame.grid(row=1, column=0, pady=(10, 0), sticky="e")

        ctk.CTkButton(
            btn_frame,
            text="Limpiar log",
            command=self._limpiar_log,
            width=100,
            fg_color="gray"
        ).pack(side="right")

    def _crear_tab_resultados(self):
        """Crea la pestana de resultados."""
        self.tab_resultados.grid_columnconfigure(0, weight=1)
        self.tab_resultados.grid_rowconfigure(1, weight=1)

        # Frame de estadisticas
        stats_frame = ctk.CTkFrame(self.tab_resultados)
        stats_frame.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        # Labels de estadisticas
        self.stats_labels = {}
        stats = [
            ("total", "Total URLs:"),
            ("exitosas", "Exitosas:"),
            ("fallidas", "Fallidas:"),
            ("imagenes", "Imagenes:"),
            ("duracion", "Duracion:")
        ]

        for i, (key, texto) in enumerate(stats):
            ctk.CTkLabel(stats_frame, text=texto).grid(row=0, column=i*2, padx=(20, 5), pady=10)
            self.stats_labels[key] = ctk.CTkLabel(
                stats_frame,
                text="0",
                font=ctk.CTkFont(weight="bold")
            )
            self.stats_labels[key].grid(row=0, column=i*2+1, padx=(0, 20), pady=10)

        # Textbox para resultados
        self.txt_resultados = ctk.CTkTextbox(
            self.tab_resultados,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.txt_resultados.grid(row=1, column=0, sticky="nsew")

        # Botones
        btn_frame = ctk.CTkFrame(self.tab_resultados, fg_color="transparent")
        btn_frame.grid(row=2, column=0, pady=(10, 0), sticky="e")

        ctk.CTkButton(
            btn_frame,
            text="Abrir carpeta output",
            command=self._abrir_carpeta_output,
            width=150
        ).pack(side="right", padx=(10, 0))

        ctk.CTkButton(
            btn_frame,
            text="Abrir Excel",
            command=self._abrir_excel,
            width=100
        ).pack(side="right")

    def _crear_footer(self):
        """Crea el pie de pagina con controles principales."""
        footer_frame = ctk.CTkFrame(self)
        footer_frame.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        footer_frame.grid_columnconfigure(1, weight=1)

        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(footer_frame, width=400)
        self.progress_bar.grid(row=0, column=0, padx=(20, 10), pady=15)
        self.progress_bar.set(0)

        # Label de estado
        self.lbl_estado = ctk.CTkLabel(
            footer_frame,
            text="Listo para iniciar",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_estado.grid(row=0, column=1, sticky="w")

        # Botones de control
        btn_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=2, padx=20)

        self.btn_detener = ctk.CTkButton(
            btn_frame,
            text="Detener",
            command=self._detener_scraping,
            width=100,
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.btn_detener.pack(side="left", padx=(0, 10))

        self.btn_iniciar = ctk.CTkButton(
            btn_frame,
            text="Iniciar Scraping",
            command=self._iniciar_scraping,
            width=150,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.btn_iniciar.pack(side="left")

    # === METODOS DE EVENTOS ===

    def _cargar_urls_archivo(self):
        """Abre dialogo para cargar URLs desde archivo."""
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo de URLs",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
            initialdir=str(self.base_path / "input")
        )

        if archivo:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                self.txt_urls.delete("1.0", "end")
                self.txt_urls.insert("1.0", contenido)
                self._actualizar_contador()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

    def _pegar_urls(self):
        """Pega URLs desde el portapapeles."""
        try:
            contenido = self.clipboard_get()
            if contenido:
                self.txt_urls.insert("end", "\n" + contenido)
                self._actualizar_contador()
        except Exception:
            pass

    def _limpiar_urls(self):
        """Limpia el textarea de URLs."""
        self.txt_urls.delete("1.0", "end")
        self._actualizar_contador()

    def _actualizar_contador(self):
        """Actualiza el contador de URLs."""
        urls = self._obtener_urls_validas()
        self.lbl_contador.configure(text=f"{len(urls)} URLs validas")

    def _obtener_urls_validas(self) -> List[str]:
        """Obtiene las URLs validas del textarea."""
        from .utils import validar_url_facebook, extraer_id_publicacion

        contenido = self.txt_urls.get("1.0", "end")
        urls = []
        ids_vistos = set()

        for linea in contenido.split('\n'):
            linea = linea.strip()
            if linea and not linea.startswith('#'):
                if validar_url_facebook(linea):
                    id_pub = extraer_id_publicacion(linea)
                    if id_pub and id_pub not in ids_vistos:
                        ids_vistos.add(id_pub)
                        urls.append(linea)
                    elif not id_pub:
                        urls.append(linea)

        return urls

    def _seleccionar_carpeta_salida(self):
        """Abre dialogo para seleccionar carpeta de salida."""
        carpeta = filedialog.askdirectory(
            title="Seleccionar carpeta de salida",
            initialdir=str(self.base_path / "output")
        )
        if carpeta:
            self.entry_output.delete(0, "end")
            self.entry_output.insert(0, carpeta)

    def _limpiar_log(self):
        """Limpia el log."""
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")

    def _agregar_log(self, mensaje: str, nivel: str = "info"):
        """Agrega un mensaje al log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefijo = {"info": "[INFO]", "error": "[ERROR]", "warning": "[WARN]"}.get(nivel, "[INFO]")

        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", f"{timestamp} {prefijo} {mensaje}\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _actualizar_progreso(self, actual: int, total: int, mensaje: str):
        """Actualiza la barra de progreso."""
        progreso = actual / total if total > 0 else 0
        self.progress_bar.set(progreso)
        self.lbl_estado.configure(text=mensaje)

    def _iniciar_scraping(self):
        """Inicia el proceso de scraping."""
        urls = self._obtener_urls_validas()

        if not urls:
            messagebox.showwarning("Advertencia", "No hay URLs validas para procesar.")
            return

        # Confirmar inicio
        if not messagebox.askyesno("Confirmar", f"Se procesaran {len(urls)} URLs.\n\n¿Desea continuar?"):
            return

        self.is_running = True
        self.btn_iniciar.configure(state="disabled")
        self.btn_detener.configure(state="normal")
        self.progress_bar.set(0)

        # Cambiar a tab de log
        self.tabview.set("Log")
        self._limpiar_log()

        # Obtener configuracion
        config = self._obtener_config_actual()

        # Iniciar en thread separado
        self.scraping_thread = threading.Thread(
            target=self._ejecutar_scraping_thread,
            args=(urls, config)
        )
        self.scraping_thread.daemon = True
        self.scraping_thread.start()

    def _obtener_config_actual(self) -> Dict[str, Any]:
        """Obtiene la configuracion actual de la GUI."""
        return {
            'scraper': self.config.get('scraper', {}),
            'delays': {
                'min_delay': int(self.slider_delay_min.get()),
                'max_delay': int(self.slider_delay_max.get()),
                'page_load_wait': 5
            },
            'download': {
                'timeout': 30,
                'max_retries': int(self.slider_reintentos.get()),
                'download_images': self.var_descargar_img.get()
            },
            'browser': {
                'headless': self.var_headless.get()
            }
        }

    def _ejecutar_scraping_thread(self, urls: List[str], config: Dict[str, Any]):
        """Ejecuta el scraping en un thread separado."""
        from .scraper import FacebookScraper
        from .excel_generator import ExcelGenerator

        try:
            # Crear scraper
            self.scraper = FacebookScraper(str(self.base_path), config)

            # Configurar callbacks
            self.scraper.on_log = lambda msg, nivel: self.after(0, self._agregar_log, msg, nivel)
            self.scraper.on_progress = lambda a, t, m: self.after(0, self._actualizar_progreso, a, t, m)
            self.scraper.on_complete = lambda e, r: self.after(0, self._on_scraping_complete, e, r)

            # Ejecutar scraping
            headless = config.get('browser', {}).get('headless', False)
            estadisticas = self.scraper.ejecutar_scraping(urls, headless)

        except Exception as e:
            self.after(0, self._agregar_log, f"Error critico: {e}", "error")
            self.after(0, self._finalizar_scraping)

    def _on_scraping_complete(self, estadisticas: Dict[str, Any], resultados: List[Dict[str, Any]]):
        """Callback cuando termina el scraping."""
        from .excel_generator import ExcelGenerator

        # Generar Excel
        if resultados:
            self._agregar_log("Generando Excel maestro...")
            excel_gen = ExcelGenerator()
            ruta_excel = self.base_path / "output" / "metadata_master.xlsx"
            if excel_gen.generar_excel(resultados, ruta_excel):
                excel_gen.agregar_hoja_resumen(ruta_excel, estadisticas)
                self._agregar_log(f"Excel generado: {ruta_excel}")

        # Actualizar estadisticas en UI
        self.stats_labels['total'].configure(text=str(estadisticas.get('total', 0)))
        self.stats_labels['exitosas'].configure(text=str(estadisticas.get('exitosas', 0)))
        self.stats_labels['fallidas'].configure(text=str(estadisticas.get('fallidas', 0)))
        self.stats_labels['imagenes'].configure(text=str(estadisticas.get('imagenes', 0)))
        self.stats_labels['duracion'].configure(text=estadisticas.get('duracion', '0 seg'))

        # Mostrar resultados
        self.txt_resultados.delete("1.0", "end")
        self.txt_resultados.insert("1.0", f"=== RESUMEN DE SCRAPING ===\n\n")
        self.txt_resultados.insert("end", f"URLs procesadas: {estadisticas.get('total', 0)}\n")
        self.txt_resultados.insert("end", f"Exitosas: {estadisticas.get('exitosas', 0)}\n")
        self.txt_resultados.insert("end", f"Fallidas: {estadisticas.get('fallidas', 0)}\n")
        self.txt_resultados.insert("end", f"Tasa de exito: {estadisticas.get('tasa_exito', 0):.1f}%\n\n")
        self.txt_resultados.insert("end", f"Imagenes descargadas: {estadisticas.get('imagenes', 0)}\n")
        self.txt_resultados.insert("end", f"Espacio usado: {estadisticas.get('espacio_mb', 0):.2f} MB\n\n")
        self.txt_resultados.insert("end", f"Duracion: {estadisticas.get('duracion', 'N/A')}\n")
        self.txt_resultados.insert("end", f"\n=== PUBLICACIONES EXTRAIDAS ===\n\n")

        for i, pub in enumerate(resultados, 1):
            self.txt_resultados.insert("end", f"{i}. {pub.get('titulo', 'Sin titulo')[:80]}...\n")
            self.txt_resultados.insert("end", f"   ID: {pub.get('id_publicacion', 'N/A')}\n")
            self.txt_resultados.insert("end", f"   Reacciones: {pub.get('reacciones', {}).get('total', 0)}\n\n")

        self._finalizar_scraping()

        # Cambiar a tab de resultados
        self.tabview.set("Resultados")

        messagebox.showinfo(
            "Completado",
            f"Scraping completado.\n\n"
            f"Exitosas: {estadisticas.get('exitosas', 0)}/{estadisticas.get('total', 0)}\n"
            f"Duracion: {estadisticas.get('duracion', 'N/A')}"
        )

    def _detener_scraping(self):
        """Detiene el scraping."""
        if self.scraper:
            self.scraper.detener()
        self._agregar_log("Scraping detenido por el usuario", "warning")

    def _finalizar_scraping(self):
        """Finaliza el proceso de scraping."""
        self.is_running = False
        self.btn_iniciar.configure(state="normal")
        self.btn_detener.configure(state="disabled")
        self.lbl_estado.configure(text="Listo")
        self.progress_bar.set(1)

    def _abrir_carpeta_output(self):
        """Abre la carpeta de salida en el explorador."""
        ruta = self.base_path / "output"
        if ruta.exists():
            webbrowser.open(str(ruta))
        else:
            messagebox.showwarning("Advertencia", "La carpeta de salida no existe.")

    def _abrir_excel(self):
        """Abre el archivo Excel generado."""
        ruta = self.base_path / "output" / "metadata_master.xlsx"
        if ruta.exists():
            webbrowser.open(str(ruta))
        else:
            messagebox.showwarning("Advertencia", "El archivo Excel no existe.")


def main():
    """Funcion principal para ejecutar la GUI."""
    app = FacebookScraperGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
