"""
Generador de Dashboard - Agrega todos los candidatos en una vista unificada
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger


class DashboardGenerator:
    """Genera un dashboard HTML agregando todos los candidatos procesados."""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.output_path = self.base_path / "output"
        self.publicaciones_path = self.output_path / "publicaciones"

    def load_all_candidates(self) -> List[Dict[str, Any]]:
        """Carga todos los candidate_processed.json."""
        candidatos = []

        if not self.publicaciones_path.exists():
            return candidatos

        for carpeta in self.publicaciones_path.iterdir():
            if carpeta.is_dir():
                processed_path = carpeta / "candidate_processed.json"
                if processed_path.exists():
                    try:
                        with open(processed_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            data['_folder'] = carpeta.name
                            candidatos.append(data)
                    except Exception as e:
                        logger.warning(f"Error cargando {processed_path}: {e}")

        return candidatos

    def generate_dashboard(self) -> str:
        """Genera el dashboard HTML."""
        candidatos = self.load_all_candidates()
        logger.info(f"Cargados {len(candidatos)} candidatos procesados")

        # Agrupar por partido
        por_partido = {}
        por_region = {}
        por_riesgo = {"alto": [], "medio": [], "bajo": []}

        for c in candidatos:
            identity = c.get("identity", {})
            risk = c.get("political_risk", {})

            partido = identity.get("party", "Sin partido")
            region = identity.get("region", "Sin región")
            score = risk.get("overall_risk_score", 0) or 0

            # Por partido
            if partido not in por_partido:
                por_partido[partido] = []
            por_partido[partido].append(c)

            # Por región
            if region not in por_region:
                por_region[region] = []
            por_region[region].append(c)

            # Por riesgo
            if score >= 4:
                por_riesgo["alto"].append(c)
            elif score >= 2:
                por_riesgo["medio"].append(c)
            else:
                por_riesgo["bajo"].append(c)

        # Generar HTML
        html = self._build_html(candidatos, por_partido, por_region, por_riesgo)

        # Guardar
        dashboard_path = self.output_path / "dashboard.html"
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"Dashboard generado: {dashboard_path}")
        return str(dashboard_path)

    def _build_html(self, candidatos, por_partido, por_region, por_riesgo) -> str:
        """Construye el HTML del dashboard."""

        # Generar filas de la tabla
        rows_html = ""
        for c in sorted(candidatos, key=lambda x: x.get("political_risk", {}).get("overall_risk_score", 0) or 0, reverse=True):
            identity = c.get("identity", {})
            profile = c.get("profile", {})
            risk = c.get("political_risk", {})
            post = c.get("post", {})

            score = risk.get("overall_risk_score", 0) or 0
            score_class = "high" if score >= 4 else "medium" if score >= 2 else "low"

            rows_html += f"""
            <tr class="candidate-row" data-partido="{identity.get('party', '')}" data-region="{identity.get('region', '')}" data-riesgo="{score_class}">
                <td>
                    <a href="publicaciones/{c.get('_folder', '')}/index.html" class="candidate-link">
                        {identity.get('full_name', 'N/A')}
                    </a>
                </td>
                <td><span class="badge badge-partido">{identity.get('party', 'N/A')}</span></td>
                <td>{identity.get('role_sought', 'N/A')}</td>
                <td>{identity.get('region', 'N/A')}</td>
                <td>{identity.get('city', 'N/A')}</td>
                <td><span class="risk-badge risk-{score_class}">{score}/5</span></td>
                <td class="bio-cell">{(profile.get('bio_summary', '') or '')[:100]}...</td>
                <td>{len(risk.get('redflags', []))}</td>
            </tr>
            """

        # Generar opciones de filtros
        partidos_options = "".join([f'<option value="{p}">{p} ({len(cs)})</option>' for p, cs in sorted(por_partido.items())])
        regiones_options = "".join([f'<option value="{r}">{r} ({len(cs)})</option>' for r, cs in sorted(por_region.items())])

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Candidatos - Elecciones 2026</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
        }}

        .header {{
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            padding: 30px;
            text-align: center;
            border-bottom: 2px solid #3b82f6;
        }}
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
            color: #f8fafc;
        }}
        .header p {{
            color: #94a3b8;
            font-size: 16px;
        }}

        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 40px;
            padding: 20px;
            background: #1e293b;
            flex-wrap: wrap;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: bold;
            color: #3b82f6;
        }}
        .stat-label {{
            color: #94a3b8;
            font-size: 14px;
        }}
        .stat.riesgo-alto .stat-number {{ color: #ef4444; }}
        .stat.riesgo-medio .stat-number {{ color: #f59e0b; }}
        .stat.riesgo-bajo .stat-number {{ color: #22c55e; }}

        .filters {{
            display: flex;
            gap: 20px;
            padding: 20px 30px;
            background: #1e293b;
            border-bottom: 1px solid #334155;
            flex-wrap: wrap;
            align-items: center;
        }}
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .filter-group label {{
            color: #94a3b8;
            font-size: 14px;
        }}
        .filter-group select, .filter-group input {{
            background: #334155;
            border: 1px solid #475569;
            color: #e2e8f0;
            padding: 8px 15px;
            border-radius: 5px;
            font-size: 14px;
        }}
        .filter-group select:focus, .filter-group input:focus {{
            outline: none;
            border-color: #3b82f6;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }}

        .table-container {{
            background: #1e293b;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background: #334155;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #f8fafc;
            position: sticky;
            top: 0;
            cursor: pointer;
        }}
        th:hover {{
            background: #475569;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #334155;
        }}
        tr:hover {{
            background: #334155;
        }}

        .candidate-link {{
            color: #60a5fa;
            text-decoration: none;
            font-weight: 500;
        }}
        .candidate-link:hover {{
            text-decoration: underline;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 500;
        }}
        .badge-partido {{
            background: #3b82f6;
            color: white;
        }}

        .risk-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 13px;
        }}
        .risk-high {{
            background: #7f1d1d;
            color: #fca5a5;
        }}
        .risk-medium {{
            background: #78350f;
            color: #fcd34d;
        }}
        .risk-low {{
            background: #14532d;
            color: #86efac;
        }}

        .bio-cell {{
            max-width: 300px;
            font-size: 13px;
            color: #94a3b8;
        }}

        .hidden {{
            display: none;
        }}

        .footer {{
            text-align: center;
            padding: 30px;
            color: #64748b;
            font-size: 14px;
        }}

        @media (max-width: 1200px) {{
            .table-container {{
                overflow-x: auto;
            }}
            table {{
                min-width: 1000px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Dashboard de Candidatos - EG2026</h1>
        <p>Análisis automatizado de perfiles políticos • Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    </div>

    <div class="stats-bar">
        <div class="stat">
            <div class="stat-number">{len(candidatos)}</div>
            <div class="stat-label">Total Candidatos</div>
        </div>
        <div class="stat">
            <div class="stat-number">{len(por_partido)}</div>
            <div class="stat-label">Partidos</div>
        </div>
        <div class="stat">
            <div class="stat-number">{len(por_region)}</div>
            <div class="stat-label">Regiones</div>
        </div>
        <div class="stat riesgo-alto">
            <div class="stat-number">{len(por_riesgo['alto'])}</div>
            <div class="stat-label">Riesgo Alto</div>
        </div>
        <div class="stat riesgo-medio">
            <div class="stat-number">{len(por_riesgo['medio'])}</div>
            <div class="stat-label">Riesgo Medio</div>
        </div>
        <div class="stat riesgo-bajo">
            <div class="stat-number">{len(por_riesgo['bajo'])}</div>
            <div class="stat-label">Riesgo Bajo</div>
        </div>
    </div>

    <div class="filters">
        <div class="filter-group">
            <label>🔍 Buscar:</label>
            <input type="text" id="searchInput" placeholder="Nombre del candidato..." />
        </div>
        <div class="filter-group">
            <label>🏛️ Partido:</label>
            <select id="filterPartido">
                <option value="">Todos los partidos</option>
                {partidos_options}
            </select>
        </div>
        <div class="filter-group">
            <label>📍 Región:</label>
            <select id="filterRegion">
                <option value="">Todas las regiones</option>
                {regiones_options}
            </select>
        </div>
        <div class="filter-group">
            <label>⚠️ Riesgo:</label>
            <select id="filterRiesgo">
                <option value="">Todos los niveles</option>
                <option value="high">Alto (4-5)</option>
                <option value="medium">Medio (2-3)</option>
                <option value="low">Bajo (0-1)</option>
            </select>
        </div>
    </div>

    <div class="container">
        <div class="table-container">
            <table id="candidatesTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">Nombre ▼</th>
                        <th onclick="sortTable(1)">Partido</th>
                        <th onclick="sortTable(2)">Cargo</th>
                        <th onclick="sortTable(3)">Región</th>
                        <th onclick="sortTable(4)">Ciudad</th>
                        <th onclick="sortTable(5)">Riesgo</th>
                        <th>Resumen</th>
                        <th onclick="sortTable(7)">Flags</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>

    <div class="footer">
        <p>Dashboard generado automáticamente con DeepSeek AI</p>
        <p>Total de candidatos analizados: {len(candidatos)} | Partidos: {len(por_partido)} | Regiones: {len(por_region)}</p>
    </div>

    <script>
        // Filtros
        const searchInput = document.getElementById('searchInput');
        const filterPartido = document.getElementById('filterPartido');
        const filterRegion = document.getElementById('filterRegion');
        const filterRiesgo = document.getElementById('filterRiesgo');
        const rows = document.querySelectorAll('.candidate-row');

        function applyFilters() {{
            const searchTerm = searchInput.value.toLowerCase();
            const partido = filterPartido.value;
            const region = filterRegion.value;
            const riesgo = filterRiesgo.value;

            rows.forEach(row => {{
                const name = row.cells[0].textContent.toLowerCase();
                const rowPartido = row.dataset.partido;
                const rowRegion = row.dataset.region;
                const rowRiesgo = row.dataset.riesgo;

                const matchSearch = name.includes(searchTerm);
                const matchPartido = !partido || rowPartido === partido;
                const matchRegion = !region || rowRegion === region;
                const matchRiesgo = !riesgo || rowRiesgo === riesgo;

                if (matchSearch && matchPartido && matchRegion && matchRiesgo) {{
                    row.classList.remove('hidden');
                }} else {{
                    row.classList.add('hidden');
                }}
            }});
        }}

        searchInput.addEventListener('input', applyFilters);
        filterPartido.addEventListener('change', applyFilters);
        filterRegion.addEventListener('change', applyFilters);
        filterRiesgo.addEventListener('change', applyFilters);

        // Ordenamiento de tabla
        let sortDirection = {{}};
        function sortTable(columnIndex) {{
            const table = document.getElementById('candidatesTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            sortDirection[columnIndex] = !sortDirection[columnIndex];
            const dir = sortDirection[columnIndex] ? 1 : -1;

            rows.sort((a, b) => {{
                let aVal = a.cells[columnIndex].textContent.trim();
                let bVal = b.cells[columnIndex].textContent.trim();

                // Para columna de riesgo, ordenar numéricamente
                if (columnIndex === 5) {{
                    aVal = parseInt(aVal) || 0;
                    bVal = parseInt(bVal) || 0;
                    return (aVal - bVal) * dir;
                }}

                // Para flags, ordenar numéricamente
                if (columnIndex === 7) {{
                    aVal = parseInt(aVal) || 0;
                    bVal = parseInt(bVal) || 0;
                    return (aVal - bVal) * dir;
                }}

                return aVal.localeCompare(bVal) * dir;
            }});

            rows.forEach(row => tbody.appendChild(row));
        }}
    </script>
</body>
</html>"""

        return html


def main():
    """Genera el dashboard."""
    generator = DashboardGenerator()
    path = generator.generate_dashboard()
    print(f"Dashboard generado: {path}")


if __name__ == "__main__":
    main()
