"""
GUI para el Procesador de Candidatos
3 Fases separadas:
1. Procesar JSON con DeepSeek (API)
2. Generar Fichas HTML (local)
3. Generar Dashboard (local)
"""

import customtkinter as ctk
from tkinter import messagebox
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
from candidate_processor import CandidateProcessor
from ficha_generator import FichaGenerator
from dashboard_generator import DashboardGenerator


class ProcessorGUI(ctk.CTk):
    """Interfaz gráfica para procesar candidatos."""

    def __init__(self):
        super().__init__()

        self.title("Procesador de Candidatos - EG2026")
        self.geometry("950x750")
        self.resizable(True, True)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.base_path = Path(__file__).parent.parent
        self.processor = None

        self._setup_ui()

    def _setup_ui(self):
        """Configura la interfaz."""

        # Frame principal
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Título
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            header,
            text="📊 Procesador de Candidatos",
            font=("Segoe UI", 26, "bold")
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="Análisis con IA + Generación de Fichas",
            font=("Segoe UI", 13),
            text_color="gray"
        ).pack(side="left", padx=(15, 0))

        # Stats Frame
        stats_frame = ctk.CTkFrame(self.main_frame)
        stats_frame.pack(fill="x", pady=10)

        stats = [
            ("total", "📁 Total:", "#FFFFFF"),
            ("json_pending", "🔄 JSON Pendientes:", "#FFC107"),
            ("json_done", "✅ JSON Procesados:", "#4CAF50"),
            ("html_pending", "📄 HTML Pendientes:", "#2196F3"),
        ]

        self.stat_labels = {}
        for key, label, color in stats:
            frame = ctk.CTkFrame(stats_frame, fg_color="transparent")
            frame.pack(side="left", padx=20, pady=10)
            ctk.CTkLabel(frame, text=label, font=("Segoe UI", 12)).pack()
            self.stat_labels[key] = ctk.CTkLabel(
                frame, text="-", font=("Segoe UI", 20, "bold"), text_color=color
            )
            self.stat_labels[key].pack()

        # Tabs
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(fill="both", expand=True, pady=10)

        self.tab_proceso = self.tabview.add("1. Procesar JSON")
        self.tab_fichas = self.tabview.add("2. Generar Fichas")
        self.tab_dashboard = self.tabview.add("3. Dashboard")

        self._crear_tab_proceso()
        self._crear_tab_fichas()
        self._crear_tab_dashboard()

        # Actualizar stats
        self.after(300, self._actualizar_stats)

    def _crear_tab_proceso(self):
        """Tab de procesamiento con DeepSeek."""
        self.tab_proceso.grid_columnconfigure(0, weight=1)
        self.tab_proceso.grid_rowconfigure(1, weight=1)

        # Info
        info = ctk.CTkFrame(self.tab_proceso)
        info.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(
            info,
            text="🤖 Fase 1: Análisis con DeepSeek",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15, pady=10)

        ctk.CTkLabel(
            info,
            text="Genera candidate_processed.json para cada publicación",
            font=("Segoe UI", 12),
            text_color="gray"
        ).pack(side="left", padx=10)

        # Log
        self.proc_log = ctk.CTkTextbox(self.tab_proceso, font=("Consolas", 11))
        self.proc_log.grid(row=1, column=0, sticky="nsew", pady=5)

        # Progress
        prog_frame = ctk.CTkFrame(self.tab_proceso, fg_color="transparent")
        prog_frame.grid(row=2, column=0, sticky="ew", pady=5)

        self.proc_label = ctk.CTkLabel(prog_frame, text="Listo", font=("Segoe UI", 12))
        self.proc_label.pack(side="left")

        self.proc_progress = ctk.CTkProgressBar(prog_frame, width=350)
        self.proc_progress.pack(side="left", padx=15)
        self.proc_progress.set(0)

        # Botones
        btn_frame = ctk.CTkFrame(self.tab_proceso, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", pady=10)

        self.btn_proc = ctk.CTkButton(
            btn_frame, text="▶️ Procesar Pendientes",
            command=self._procesar_json, width=180, height=40,
            fg_color="#4CAF50", hover_color="#388E3C"
        )
        self.btn_proc.pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="🔁 Reprocesar Todos",
            command=lambda: self._procesar_json(todos=True),
            width=160, height=40, fg_color="#FF9800", hover_color="#F57C00"
        ).pack(side="left", padx=5)

        self.btn_proc_stop = ctk.CTkButton(
            btn_frame, text="⏹️ Detener", command=self._detener_proceso,
            width=100, height=40, fg_color="#F44336", hover_color="#D32F2F",
            state="disabled"
        )
        self.btn_proc_stop.pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="🔄 Actualizar", command=self._actualizar_stats,
            width=100, height=40
        ).pack(side="right", padx=5)

    def _crear_tab_fichas(self):
        """Tab de generación de fichas HTML."""
        self.tab_fichas.grid_columnconfigure(0, weight=1)
        self.tab_fichas.grid_rowconfigure(1, weight=1)

        # Info
        info = ctk.CTkFrame(self.tab_fichas)
        info.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(
            info,
            text="📄 Fase 2: Generar Fichas HTML",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15, pady=10)

        ctk.CTkLabel(
            info,
            text="Crea index.html desde los JSON procesados (sin API)",
            font=("Segoe UI", 12),
            text_color="gray"
        ).pack(side="left", padx=10)

        # Descripción
        desc = ctk.CTkTextbox(self.tab_fichas, font=("Segoe UI", 12), height=200)
        desc.grid(row=1, column=0, sticky="nsew", pady=5, padx=5)
        desc.insert("1.0", """Este paso genera las fichas HTML individuales:

✓ Lee cada candidate_processed.json
✓ Aplica una plantilla HTML uniforme
✓ Genera index.html en cada carpeta de publicación

Cada ficha incluye:
  • Información del candidato (nombre, partido, cargo, región)
  • Resumen del perfil
  • Educación y experiencia laboral
  • Declaraciones económicas
  • Análisis de riesgo y red flags
  • Campos editables para redes sociales

⚡ Este proceso es local y rápido (no usa API)
""")
        desc.configure(state="disabled")

        # Progress
        prog_frame = ctk.CTkFrame(self.tab_fichas, fg_color="transparent")
        prog_frame.grid(row=2, column=0, sticky="ew", pady=5)

        self.ficha_label = ctk.CTkLabel(prog_frame, text="Listo", font=("Segoe UI", 12))
        self.ficha_label.pack(side="left")

        self.ficha_progress = ctk.CTkProgressBar(prog_frame, width=350)
        self.ficha_progress.pack(side="left", padx=15)
        self.ficha_progress.set(0)

        # Botones
        btn_frame = ctk.CTkFrame(self.tab_fichas, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", pady=10)

        self.btn_fichas = ctk.CTkButton(
            btn_frame, text="📄 Generar Fichas Pendientes",
            command=self._generar_fichas, width=200, height=45,
            fg_color="#2196F3", hover_color="#1976D2",
            font=("Segoe UI", 14)
        )
        self.btn_fichas.pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="🔁 Regenerar Todas",
            command=lambda: self._generar_fichas(todos=True),
            width=160, height=45, fg_color="#FF9800", hover_color="#F57C00"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="📂 Abrir Carpeta",
            command=self._abrir_fichas, width=130, height=45, fg_color="gray"
        ).pack(side="right", padx=5)

    def _crear_tab_dashboard(self):
        """Tab del dashboard."""
        self.tab_dashboard.grid_columnconfigure(0, weight=1)
        self.tab_dashboard.grid_rowconfigure(1, weight=1)

        # Info
        info = ctk.CTkFrame(self.tab_dashboard)
        info.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(
            info,
            text="📊 Fase 3: Dashboard Agregado",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15, pady=10)

        ctk.CTkLabel(
            info,
            text="HTML interactivo con todos los candidatos",
            font=("Segoe UI", 12),
            text_color="gray"
        ).pack(side="left", padx=10)

        # Descripción
        desc = ctk.CTkTextbox(self.tab_dashboard, font=("Segoe UI", 12), height=200)
        desc.grid(row=1, column=0, sticky="nsew", pady=5, padx=5)
        desc.insert("1.0", """El Dashboard incluye:

✓ Tabla de todos los candidatos procesados
✓ Filtros por partido, región y nivel de riesgo
✓ Búsqueda por nombre
✓ Ordenamiento de columnas
✓ Link a cada ficha individual
✓ Estadísticas agregadas (totales, por partido, por riesgo)

Agrupaciones:
  • Por partido político
  • Por región/departamento
  • Por score de riesgo (alto/medio/bajo)

El dashboard se guarda en: output/dashboard.html
⚡ Este proceso es local y rápido (no usa API)
""")
        desc.configure(state="disabled")

        # Botones
        btn_frame = ctk.CTkFrame(self.tab_dashboard, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", pady=15)

        self.btn_dash = ctk.CTkButton(
            btn_frame, text="🚀 Generar Dashboard",
            command=self._generar_dashboard, width=200, height=50,
            fg_color="#3b82f6", hover_color="#2563eb",
            font=("Segoe UI", 15, "bold")
        )
        self.btn_dash.pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame, text="🌐 Abrir Dashboard",
            command=self._abrir_dashboard, width=160, height=50,
            font=("Segoe UI", 14)
        ).pack(side="left", padx=10)

    # === MÉTODOS ===

    def _actualizar_stats(self):
        """Actualiza estadísticas."""
        try:
            processor = CandidateProcessor(str(self.base_path))
            generator = FichaGenerator(str(self.base_path))

            total = len(processor.get_all_folders())
            json_pending = len(processor.get_pending_folders())
            json_done = total - json_pending
            html_pending = len(generator.get_pending_folders())

            self.stat_labels["total"].configure(text=str(total))
            self.stat_labels["json_pending"].configure(text=str(json_pending))
            self.stat_labels["json_done"].configure(text=str(json_done))
            self.stat_labels["html_pending"].configure(text=str(html_pending))

        except Exception as e:
            self._log(f"Error: {e}", "error")

    def _log(self, msg: str, nivel: str = "info"):
        """Log al textbox."""
        ts = datetime.now().strftime("%H:%M:%S")
        icon = {"info": "ℹ️", "error": "❌", "warning": "⚠️", "success": "✅"}.get(nivel, "")
        self.proc_log.insert("end", f"[{ts}] {icon} {msg}\n")
        self.proc_log.see("end")

    def _procesar_json(self, todos: bool = False):
        """Procesa con DeepSeek."""
        self.btn_proc.configure(state="disabled")
        self.btn_proc_stop.configure(state="normal")
        self.proc_log.delete("1.0", "end")
        self.proc_progress.set(0)

        def run():
            self.processor = CandidateProcessor(str(self.base_path))
            self.processor.on_log = lambda m, n: self.after(0, self._log, m, n)
            self.processor.on_progress = lambda a, t, n: self.after(
                0, self._on_proc_progress, a, t, n)
            self.processor.on_complete = lambda e, err: self.after(
                0, self._on_proc_complete, e, err)
            self.processor.process_all(solo_pendientes=not todos)

        threading.Thread(target=run, daemon=True).start()

    def _on_proc_progress(self, actual, total, nombre):
        self.proc_progress.set(actual / total)
        self.proc_label.configure(text=f"[{actual}/{total}] {nombre}")

    def _on_proc_complete(self, exitosos, errores):
        self.btn_proc.configure(state="normal")
        self.btn_proc_stop.configure(state="disabled")
        self.proc_label.configure(text="✅ Completado")
        self._actualizar_stats()
        messagebox.showinfo("Completado", f"JSON procesados: {exitosos}\nErrores: {errores}")

    def _detener_proceso(self):
        if self.processor:
            self.processor.detener()
        self.btn_proc_stop.configure(state="disabled")

    def _generar_fichas(self, todos: bool = False):
        """Genera fichas HTML."""
        self.btn_fichas.configure(state="disabled", text="Generando...")
        self.ficha_progress.set(0)

        def run():
            generator = FichaGenerator(str(self.base_path))
            generator.on_progress = lambda a, t, n: self.after(
                0, self._on_ficha_progress, a, t, n)
            generator.on_complete = lambda e, err: self.after(
                0, self._on_ficha_complete, e, err)
            generator.generate_all(solo_pendientes=not todos)

        threading.Thread(target=run, daemon=True).start()

    def _on_ficha_progress(self, actual, total, nombre):
        self.ficha_progress.set(actual / total)
        self.ficha_label.configure(text=f"[{actual}/{total}] {nombre}")

    def _on_ficha_complete(self, exitosos, errores):
        self.btn_fichas.configure(state="normal", text="📄 Generar Fichas Pendientes")
        self.ficha_label.configure(text="✅ Completado")
        self._actualizar_stats()
        messagebox.showinfo("Completado", f"Fichas generadas: {exitosos}\nErrores: {errores}")

    def _generar_dashboard(self):
        """Genera el dashboard."""
        self.btn_dash.configure(state="disabled", text="Generando...")

        def run():
            try:
                generator = DashboardGenerator(str(self.base_path))
                path = generator.generate_dashboard()
                self.after(0, lambda: self._on_dash_complete(path))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.after(0, lambda: self.btn_dash.configure(
                    state="normal", text="🚀 Generar Dashboard"))

        threading.Thread(target=run, daemon=True).start()

    def _on_dash_complete(self, path):
        self.btn_dash.configure(state="normal", text="🚀 Generar Dashboard")
        messagebox.showinfo("Éxito", f"Dashboard generado:\n{path}")
        webbrowser.open(path)

    def _abrir_dashboard(self):
        path = self.base_path / "output" / "dashboard.html"
        if path.exists():
            webbrowser.open(str(path))
        else:
            messagebox.showwarning("Advertencia", "Dashboard no existe. Genéralo primero.")

    def _abrir_fichas(self):
        path = self.base_path / "output" / "publicaciones"
        if path.exists():
            webbrowser.open(str(path))


def main():
    app = ProcessorGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
