"""
Preparador de Despliegue para GitHub Pages
Copia el dashboard y las fichas a la carpeta docs/ para ser servidos por GitHub Pages
"""

import shutil
import json
from pathlib import Path
from datetime import datetime
from loguru import logger


class DeployPreparer:
    """Prepara los archivos para despliegue en GitHub Pages."""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.output_path = self.base_path / "output"
        self.docs_path = self.base_path / "docs"
        self.publicaciones_path = self.output_path / "publicaciones"

    def prepare_docs(self):
        """Prepara la carpeta docs/ con todo el contenido para GitHub Pages."""
        logger.info("Preparando archivos para GitHub Pages...")

        # Crear carpeta docs si no existe
        self.docs_path.mkdir(exist_ok=True)

        # Crear carpeta para las fichas
        fichas_path = self.docs_path / "fichas"
        fichas_path.mkdir(exist_ok=True)

        # Copiar dashboard.html como index.html principal
        dashboard_src = self.output_path / "dashboard.html"
        if dashboard_src.exists():
            # Leer y modificar el dashboard para actualizar las rutas
            with open(dashboard_src, 'r', encoding='utf-8') as f:
                dashboard_html = f.read()

            # Actualizar rutas relativas
            dashboard_html = dashboard_html.replace(
                'publicaciones/',
                'fichas/'
            )

            # Guardar como index.html
            with open(self.docs_path / "index.html", 'w', encoding='utf-8') as f:
                f.write(dashboard_html)
            logger.info("Dashboard copiado como index.html")
        else:
            logger.warning("dashboard.html no encontrado")

        # Copiar todas las fichas de candidatos
        candidatos_copiados = 0
        if self.publicaciones_path.exists():
            for carpeta in self.publicaciones_path.iterdir():
                if carpeta.is_dir():
                    # Crear subcarpeta para el candidato
                    dest_carpeta = fichas_path / carpeta.name
                    dest_carpeta.mkdir(exist_ok=True)

                    # Copiar index.html
                    index_src = carpeta / "index.html"
                    if index_src.exists():
                        shutil.copy2(index_src, dest_carpeta / "index.html")

                    # Copiar imagen si existe
                    imagen_src = carpeta / "imagen.jpg"
                    if imagen_src.exists():
                        shutil.copy2(imagen_src, dest_carpeta / "imagen.jpg")

                    # También copiar imágenes con otros nombres/formatos
                    for img_ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp']:
                        for img_file in carpeta.glob(img_ext):
                            shutil.copy2(img_file, dest_carpeta / img_file.name)

                    candidatos_copiados += 1

        logger.info(f"Copiadas {candidatos_copiados} fichas de candidatos")

        # Crear archivo de metadatos para el sitio
        self._create_site_metadata(candidatos_copiados)

        # Crear archivo 404.html
        self._create_404_page()

        logger.info(f"Preparación completada. Archivos en: {self.docs_path}")
        return candidatos_copiados

    def _create_site_metadata(self, total_candidatos: int):
        """Crea un archivo JSON con metadatos del sitio."""
        metadata = {
            "sitio": "Dashboard de Candidatos Electorales - Puno 2026",
            "generado": datetime.now().isoformat(),
            "total_candidatos": total_candidatos,
            "fuente": "Scraping de Facebook - Elecciones Generales 2026",
            "version": "1.0.0"
        }

        with open(self.docs_path / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _create_404_page(self):
        """Crea una página 404 personalizada."""
        html_404 = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Página no encontrada - Dashboard Candidatos</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, sans-serif;
            background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }
        .container {
            text-align: center;
            padding: 40px;
        }
        h1 { font-size: 72px; margin: 0; }
        p { font-size: 20px; opacity: 0.9; }
        a {
            display: inline-block;
            margin-top: 20px;
            padding: 12px 30px;
            background: #ff5722;
            color: white;
            text-decoration: none;
            border-radius: 25px;
            font-weight: bold;
            transition: transform 0.2s;
        }
        a:hover { transform: scale(1.05); }
    </style>
</head>
<body>
    <div class="container">
        <h1>404</h1>
        <p>La ficha de candidato que buscas no existe o fue movida.</p>
        <a href="/">Volver al Dashboard</a>
    </div>
</body>
</html>"""
        with open(self.docs_path / "404.html", 'w', encoding='utf-8') as f:
            f.write(html_404)

    def clean_docs(self):
        """Limpia la carpeta docs/ para un nuevo despliegue."""
        if self.docs_path.exists():
            shutil.rmtree(self.docs_path)
            logger.info("Carpeta docs/ limpiada")
        self.docs_path.mkdir(exist_ok=True)


def main():
    """Función principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Preparar archivos para GitHub Pages")
    parser.add_argument("--clean", action="store_true", help="Limpiar docs/ antes de preparar")
    args = parser.parse_args()

    preparer = DeployPreparer()

    if args.clean:
        preparer.clean_docs()

    preparer.prepare_docs()
    print(f"\nArchivos listos en: {preparer.docs_path}")
    print("Ahora puedes hacer commit y push a GitHub.")


if __name__ == "__main__":
    main()
