"""
Generador de Fichas HTML
Lee los candidate_processed.json y genera index.html usando plantilla local
NO usa API - solo procesamiento local
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from loguru import logger


class FichaGenerator:
    """Genera fichas HTML desde los JSON procesados."""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.output_path = self.base_path / "output" / "publicaciones"

        # Callbacks para GUI
        self.on_progress: Optional[Callable] = None
        self.on_log: Optional[Callable] = None
        self.on_complete: Optional[Callable] = None

        # Estado
        self.generated_count = 0
        self.error_count = 0

    def log(self, mensaje: str, nivel: str = "info"):
        """Registra un mensaje."""
        if nivel == "info":
            logger.info(mensaje)
        elif nivel == "error":
            logger.error(mensaje)
        elif nivel == "warning":
            logger.warning(mensaje)

        if self.on_log:
            self.on_log(mensaje, nivel)

    def get_pending_folders(self) -> List[Path]:
        """Obtiene carpetas con JSON procesado pero sin HTML."""
        pendientes = []

        if not self.output_path.exists():
            return pendientes

        for carpeta in self.output_path.iterdir():
            if carpeta.is_dir():
                processed_path = carpeta / "candidate_processed.json"
                html_path = carpeta / "index.html"

                if processed_path.exists() and not html_path.exists():
                    pendientes.append(carpeta)

        return sorted(pendientes)

    def get_all_processed_folders(self) -> List[Path]:
        """Obtiene todas las carpetas con JSON procesado."""
        carpetas = []

        if not self.output_path.exists():
            return carpetas

        for carpeta in self.output_path.iterdir():
            if carpeta.is_dir():
                processed_path = carpeta / "candidate_processed.json"
                if processed_path.exists():
                    carpetas.append(carpeta)

        return sorted(carpetas)

    def generate_html(self, record: Dict, metadata: Dict) -> str:
        """Genera el HTML de la ficha usando la plantilla."""

        identity = record.get("identity", {})
        post = record.get("post", {})
        profile = record.get("profile", {})
        risk = record.get("political_risk", {})

        # Determinar clase de riesgo
        score = risk.get("overall_risk_score", 0) or 0
        risk_class = "high" if score >= 4 else "medium" if score >= 2 else "low"
        risk_color = "#c62828" if score >= 4 else "#f57c00" if score >= 2 else "#2e7d32"
        risk_bg = "#ffebee" if score >= 4 else "#fff3e0" if score >= 2 else "#e8f5e9"

        # Generar secciones
        education_html = self._generate_list(profile.get("education", []),
            lambda e: f"{e.get('degree', '')} - {e.get('institution', '')} ({e.get('year', '')})")

        work_html = self._generate_list(profile.get("work_experience", []),
            lambda e: f"{e.get('company', '')} | {e.get('roles', '')} ({e.get('period', '')})")

        redflags_html = self._generate_redflags(risk.get("redflags", []))

        sensitive_html = ""
        if risk.get("sensitive_info"):
            items = "".join([f"<li>{s}</li>" for s in risk.get("sensitive_info", [])])
            sensitive_html = f"""
            <div class="section sensitive">
                <h3>⚠️ Información Sensible Detectada</h3>
                <ul>{items}</ul>
            </div>
            """

        # Income declaration
        income = profile.get("income_declaration", {})
        income_html = ""
        if income and income.get("total"):
            income_html = f"""
            <div class="info-card">
                <h4>💰 Declaración de Ingresos ({income.get('year', '-')})</h4>
                <p class="amount">S/ {income.get('total', '-')}</p>
                <p class="detail">{income.get('breakdown', '')}</p>
            </div>
            """

        # Assets
        assets = profile.get("assets", {})
        assets_html = ""
        if assets and assets.get("total_value"):
            assets_html = f"""
            <div class="info-card">
                <h4>🏠 Patrimonio Declarado</h4>
                <p class="amount">S/ {assets.get('total_value', '-')}</p>
                <p class="detail">Inmuebles: {assets.get('real_estate', 'No declara')}</p>
                <p class="detail">Vehículos: {assets.get('vehicles', 'No declara')}</p>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{identity.get('full_name', 'Candidato')} - Ficha Electoral</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, sans-serif;
            background: #f0f2f5;
            color: #1c1e21;
            line-height: 1.6;
        }}
        .container {{
            max-width: 900px;
            margin: 20px auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        /* Header */
        .header {{
            background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
            color: white;
            padding: 30px;
            display: flex;
            gap: 25px;
            align-items: flex-start;
        }}
        .header img {{
            width: 140px;
            height: 140px;
            object-fit: cover;
            border-radius: 10px;
            border: 3px solid rgba(255,255,255,0.3);
        }}
        .header-info {{ flex: 1; }}
        .header-info h1 {{
            font-size: 26px;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        .chips {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin: 12px 0;
        }}
        .chip {{
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
        }}
        .chip-party {{ background: #ff5722; }}
        .chip-region {{ background: #4caf50; }}
        .chip-role {{ background: #2196f3; }}
        .source-link {{
            color: rgba(255,255,255,0.8);
            font-size: 13px;
            text-decoration: none;
            margin-top: 10px;
            display: inline-block;
        }}
        .source-link:hover {{ color: white; }}

        /* Risk Badge */
        .risk-badge {{
            position: absolute;
            top: 20px;
            right: 20px;
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 14px;
            background: {risk_bg};
            color: {risk_color};
        }}
        .header {{ position: relative; }}

        /* Sections */
        .section {{
            padding: 25px 30px;
            border-bottom: 1px solid #e4e6eb;
        }}
        .section:last-child {{ border-bottom: none; }}
        .section h2 {{
            color: #1a237e;
            font-size: 18px;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e8eaf6;
        }}
        .section h3 {{
            color: #424242;
            font-size: 15px;
            margin: 15px 0 10px 0;
        }}

        /* Table */
        .info-table {{ width: 100%; border-collapse: collapse; }}
        .info-table th, .info-table td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e4e6eb;
        }}
        .info-table th {{
            background: #f8f9fa;
            color: #65676b;
            font-weight: 600;
            width: 30%;
        }}

        /* Lists */
        .profile-list {{ list-style: none; }}
        .profile-list li {{
            padding: 10px 0;
            border-bottom: 1px solid #f0f2f5;
            padding-left: 20px;
            position: relative;
        }}
        .profile-list li:before {{
            content: "▸";
            position: absolute;
            left: 0;
            color: #1a237e;
        }}
        .profile-list li:last-child {{ border-bottom: none; }}

        /* Info Cards */
        .cards-row {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .info-card {{
            flex: 1;
            min-width: 200px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #1a237e;
        }}
        .info-card h4 {{
            color: #1a237e;
            margin-bottom: 10px;
            font-size: 14px;
        }}
        .info-card .amount {{
            font-size: 24px;
            font-weight: bold;
            color: #1c1e21;
        }}
        .info-card .detail {{
            color: #65676b;
            font-size: 13px;
            margin-top: 5px;
        }}

        /* Red Flags */
        .redflags {{ background: #fff8e1; }}
        .redflag-item {{
            background: white;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
            border-radius: 0 8px 8px 0;
        }}
        .redflag-item.high {{ border-left-color: #f44336; background: #ffebee; }}
        .redflag-item.medium {{ border-left-color: #ff9800; }}
        .redflag-type {{
            font-weight: bold;
            color: #f57c00;
            font-size: 13px;
            text-transform: uppercase;
        }}
        .redflag-item.high .redflag-type {{ color: #c62828; }}
        .redflag-evidence {{
            font-style: italic;
            color: #65676b;
            margin: 8px 0;
            font-size: 13px;
            padding: 10px;
            background: rgba(0,0,0,0.03);
            border-radius: 5px;
        }}
        .redflag-notes {{ font-size: 14px; }}

        /* Sensitive */
        .sensitive {{ background: #fce4ec; }}
        .sensitive h3 {{ color: #c62828; }}
        .sensitive ul {{
            list-style: none;
            padding-left: 0;
        }}
        .sensitive li {{
            padding: 8px 12px;
            background: white;
            margin: 5px 0;
            border-radius: 5px;
            font-size: 13px;
        }}

        /* Social Section */
        .social-section input, .social-section textarea {{
            width: 100%;
            padding: 10px 12px;
            margin: 5px 0 15px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }}
        .social-section input:focus, .social-section textarea:focus {{
            outline: none;
            border-color: #1a237e;
        }}
        .social-section label {{
            font-weight: 600;
            color: #424242;
            font-size: 14px;
        }}

        /* Footer */
        .footer {{
            background: #f8f9fa;
            padding: 20px 30px;
            text-align: center;
            color: #65676b;
            font-size: 12px;
        }}
        .footer a {{ color: #1a237e; }}

        /* Bio Summary */
        .bio-summary {{
            background: #e8eaf6;
            padding: 15px 20px;
            border-radius: 8px;
            font-size: 15px;
            line-height: 1.7;
        }}

        @media (max-width: 600px) {{
            .header {{ flex-direction: column; text-align: center; }}
            .header img {{ margin: 0 auto; }}
            .chips {{ justify-content: center; }}
            .cards-row {{ flex-direction: column; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="{metadata.get('imagen_local', 'imagen.jpg')}"
                 alt="Foto del candidato"
                 onerror="this.src='{post.get('image', {}).get('url', '')}'" />
            <div class="header-info">
                <h1>{identity.get('full_name', 'Nombre no disponible')}</h1>
                <div class="chips">
                    <span class="chip chip-party">{identity.get('party', 'Partido no especificado')}</span>
                    <span class="chip chip-region">{identity.get('region', 'Región')}</span>
                    <span class="chip chip-role">{identity.get('role_sought', 'Cargo')}</span>
                </div>
                <a href="{metadata.get('url_publicacion', '#')}" target="_blank" class="source-link">
                    📎 Ver publicación original en Facebook →
                </a>
            </div>
            <div class="risk-badge">
                Riesgo: {score}/5
            </div>
        </div>

        <div class="section">
            <h2>📋 Información General</h2>
            <table class="info-table">
                <tr><th>Nombre completo</th><td>{identity.get('full_name', '-')}</td></tr>
                <tr><th>Partido político</th><td>{identity.get('party', '-')}</td></tr>
                <tr><th>Cargo al que postula</th><td>{identity.get('role_sought', '-')}</td></tr>
                <tr><th>Región / Ciudad</th><td>{identity.get('region', '-')} / {identity.get('city', '-')}</td></tr>
                <tr><th>Fuente</th><td><a href="{metadata.get('url_publicacion', '#')}">{metadata.get('pagina', '-')}</a> - {metadata.get('fecha_publicacion', '-')}</td></tr>
            </table>
        </div>

        <div class="section">
            <h2>👤 Resumen del Perfil</h2>
            <div class="bio-summary">
                {profile.get('bio_summary', 'Sin información disponible')}
            </div>
        </div>

        <div class="section">
            <h2>📚 Formación y Experiencia</h2>

            <h3>🎓 Educación</h3>
            {education_html if education_html else '<p style="color: #65676b;">No especificado</p>'}

            <h3>💼 Experiencia Laboral</h3>
            {work_html if work_html else '<p style="color: #65676b;">No especificado</p>'}
        </div>

        <div class="section">
            <h2>💵 Declaraciones Económicas</h2>
            <div class="cards-row">
                {income_html if income_html else '<div class="info-card"><h4>💰 Ingresos</h4><p>No declarado</p></div>'}
                {assets_html if assets_html else '<div class="info-card"><h4>🏠 Patrimonio</h4><p>No declarado</p></div>'}
            </div>
        </div>

        <div class="section redflags">
            <h2>⚠️ Análisis de Riesgo</h2>
            <p style="margin-bottom: 15px;">
                <strong>Score general:</strong>
                <span style="background: {risk_bg}; color: {risk_color}; padding: 5px 12px; border-radius: 5px; font-weight: bold;">
                    {score} / 5
                </span>
            </p>
            {redflags_html if redflags_html else '<p style="color: #65676b;">No se identificaron alertas significativas.</p>'}
        </div>

        {sensitive_html}

        <div class="section social-section">
            <h2>📱 Redes Sociales (Llenado Manual)</h2>

            <label>Facebook:</label>
            <input type="text" placeholder="URL del perfil de Facebook" />

            <label>Instagram:</label>
            <input type="text" placeholder="@usuario" />

            <label>TikTok:</label>
            <input type="text" placeholder="@usuario" />

            <label>WhatsApp:</label>
            <input type="text" placeholder="Número de contacto" />

            <label>Observaciones de actividad en redes:</label>
            <textarea rows="3" placeholder="Notas sobre actividad, seguidores, tipo de contenido..."></textarea>

            <label>Mapa de actividad (enlaces y hallazgos):</label>
            <textarea rows="3" placeholder="Pegar enlaces relevantes encontrados..."></textarea>
        </div>

        <div class="footer">
            <p>Ficha generada automáticamente | Scraping: {metadata.get('fecha_scraping', '-')} | Post ID: {metadata.get('id_publicacion', '-')}</p>
            <p>Candidate ID: {identity.get('candidate_id', '-')}</p>
        </div>
    </div>
</body>
</html>"""

        return html

    def _generate_list(self, items: List[Dict], formatter) -> str:
        """Genera una lista HTML."""
        if not items:
            return ""

        items_html = ""
        for item in items:
            if item:
                items_html += f"<li>{formatter(item)}</li>"

        if items_html:
            return f'<ul class="profile-list">{items_html}</ul>'
        return ""

    def _generate_redflags(self, redflags: List[Dict]) -> str:
        """Genera el HTML de los redflags."""
        if not redflags:
            return ""

        html = ""
        for rf in redflags:
            severity = rf.get("severity", 0) or 0
            severity_class = "high" if severity >= 4 else "medium" if severity >= 2 else ""

            html += f"""
            <div class="redflag-item {severity_class}">
                <span class="redflag-type">[{rf.get('type', 'N/A')}] Severidad: {severity}/5</span>
                <div class="redflag-evidence">"{rf.get('evidence_text', '')}"</div>
                <div class="redflag-notes">{rf.get('notes', '')}</div>
            </div>
            """

        return html

    def process_folder(self, carpeta: Path) -> bool:
        """Procesa una carpeta y genera el HTML."""
        processed_path = carpeta / "candidate_processed.json"
        metadata_path = carpeta / "metadata.json"
        html_path = carpeta / "index.html"

        try:
            # Leer JSON procesado
            with open(processed_path, 'r', encoding='utf-8') as f:
                record = json.load(f)

            # Leer metadata original
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

            self.log(f"Generando HTML: {carpeta.name}")

            # Generar HTML
            html = self.generate_html(record, metadata)

            # Guardar
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)

            self.log(f"  -> Guardado: index.html")
            return True

        except Exception as e:
            self.log(f"Error en {carpeta.name}: {e}", "error")
            return False

    def generate_all(self, solo_pendientes: bool = True):
        """Genera HTML para todas las carpetas."""
        self.generated_count = 0
        self.error_count = 0

        carpetas = self.get_pending_folders() if solo_pendientes else self.get_all_processed_folders()
        total = len(carpetas)

        if total == 0:
            self.log("No hay carpetas para generar HTML")
            if self.on_complete:
                self.on_complete(0, 0)
            return

        self.log(f"Generando HTML para {total} carpetas...")

        for i, carpeta in enumerate(carpetas, 1):
            if self.on_progress:
                self.on_progress(i, total, carpeta.name)

            if self.process_folder(carpeta):
                self.generated_count += 1
            else:
                self.error_count += 1

        self.log(f"Completado: {self.generated_count} generados, {self.error_count} errores")

        if self.on_complete:
            self.on_complete(self.generated_count, self.error_count)


def main():
    """Genera fichas HTML desde línea de comandos."""
    import argparse

    parser = argparse.ArgumentParser(description="Generar fichas HTML desde JSON procesados")
    parser.add_argument("--all", action="store_true", help="Regenerar todas las fichas")
    args = parser.parse_args()

    generator = FichaGenerator()
    generator.generate_all(solo_pendientes=not args.all)


if __name__ == "__main__":
    main()
