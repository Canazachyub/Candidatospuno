"""
Integrador de Redes Sociales
Actualiza los candidate_processed.json con datos de redes sociales
y regenera los HTML correspondientes
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

# Datos de redes sociales obtenidos de la investigación con Perplexity
# Mapeo: nombre del candidato -> datos de redes sociales
# Búsqueda realizada: 2 de febrero de 2026
SOCIAL_MEDIA_DATA = {
    # 1. Lucia Edita Betshy Orihuela Pasaca - Renovación Popular
    "Lucia Edita Betshy Orihuela Pasaca": {
        "facebook": {
            "url": "https://www.facebook.com/profile.php?id=100093495664223",
            "username": "profile.php?id=100093495664223",
            "followers": "5 amigos",
            "verified": False,
            "location": "Juliaca"
        }
    },
    # 2. Sheila Estrella Angles Canlla - Renovación Popular
    "Sheila Estrella Angles Canlla": {
        "facebook": {
            "url": "https://www.facebook.com/sheila.anglescanlla",
            "username": "sheila.anglescanlla",
            "followers": None,
            "verified": False,
            "location": "Puno"
        }
    },
    # 4. Sara Ana Luque Pérez - FREPAP
    "Sara Ana Luque Pérez": {
        "facebook": {
            "url": "https://www.facebook.com/sara.perez.3762584",
            "username": "sara.perez.3762584",
            "followers": "2.6K amigos",
            "verified": False,
            "notes": "Candidata DIPUTADA N°1 FREPAP"
        },
        "instagram": {
            "url": "https://www.instagram.com/luquesara17",
            "username": "@luquesara17",
            "followers": None,
            "verified": False
        }
    },
    # 6. Adelma Quispe Condori - Alianza Electoral Venceremos
    "Adelma Quispe Condori": {
        "facebook": {
            "url": "https://www.facebook.com/adelma.quispecondori",
            "username": "adelma.quispecondori",
            "followers": "4.5K amigos",
            "verified": False
        }
    },
    # 7. Irene Carcausto Huanca - Alianza Para el Progreso
    "Irene Carcausto Huanca": {
        "facebook": {
            "url": "https://www.facebook.com/irene.carcaustohuanca",
            "username": "irene.carcaustohuanca",
            "followers": "5.7K seguidores",
            "verified": False,
            "location": "Azángaro, UNA-PUNO"
        }
    },
    # 13. Luz María Hancco Suca - Perú Primero
    "Luz María Hancco Suca": {
        "facebook": {
            "url": "https://www.facebook.com/luzmaria.hanccosuca.5",
            "username": "luzmaria.hanccosuca.5",
            "followers": "60 amigos",
            "verified": False,
            "location": "Ayaviri, IsepaMelgar"
        }
    },
    # 14. Saulo Nicolás Apaza Quispe - PODEMOS PERÚ
    "Saulo Nicolás Apaza Quispe": {
        "facebook": {
            "url": "https://www.facebook.com/saulonicolas.apazaquispe",
            "username": "saulonicolas.apazaquispe",
            "followers": "1.7K seguidores",
            "verified": False,
            "location": "Juliaca"
        }
    },
    # 20. Estanislao Edgar Mancha Pineda - Renovación Popular
    "Estanislao Edgar Mancha Pineda": {
        "facebook": {
            "url": "https://www.facebook.com/edgarmanp",
            "username": "edgarmanp",
            "followers": "18K seguidores",
            "verified": False,
            "location": "Puno",
            "notes": "Figura pública"
        },
        "tiktok": {
            "url": "https://www.tiktok.com/@edgarmanp",
            "username": "@edgarmanp",
            "followers": "300K+",
            "verified": False
        }
    },
    # 22. Flavio Cruz Mamani - Perú Libre
    "Flavio Cruz Mamani": {
        "facebook": {
            "url": "https://www.facebook.com/flavio.cruzmamani.1",
            "username": "flavio.cruzmamani.1",
            "followers": "6K seguidores",
            "verified": True,
            "location": "UNA-Puno"
        }
    },
    # 23. Mao Tsetung Machaca Avilés - Renovación Popular
    "Mao Tsetung Machaca Avilés": {
        "facebook": {
            "url": "https://www.facebook.com/mao.machaca.2025",
            "username": "mao.machaca.2025",
            "followers": "2.4K seguidores",
            "verified": False,
            "location": "Puno"
        }
    },
    # 24. Jhomira Noheli Jiménez Jalire - Somos Perú
    "Jhomira Noheli Jiménez Jalire": {
        "facebook": {
            "url": "https://www.facebook.com/jhomiranoheli.jimenezjalire",
            "username": "jhomiranoheli.jimenezjalire",
            "followers": None,
            "verified": False,
            "notes": "Perfil básico"
        }
    },
    # 26. Denilson Medina Sánchez - Partido Demócrata Verde
    "Denilson Medina Sánchez": {
        "facebook": {
            "url": "https://www.facebook.com/denilson.medina.sanchez.2025",
            "username": "denilson.medina.sanchez.2025",
            "followers": "282 seguidores",
            "verified": False,
            "location": "Lima"
        }
    },
    # 30. César Hugo Tito Rojas - Juntos por el Perú
    "César Hugo Tito Rojas": {
        "facebook": {
            "url": "https://www.facebook.com/profile.php?id=100082372457814",
            "username": "profile.php?id=100082372457814",
            "followers": "5.5K seguidores",
            "verified": False,
            "location": "Puno, UNA-PUNO",
            "notes": "DIPUTADO REGIONAL"
        }
    },
    # 36. Juan Luque Mamani - Perú Moderno
    "Juan Luque Mamani": {
        "facebook": {
            "url": "https://www.facebook.com/juan.luque.mamani.2025",
            "username": "juan.luque.mamani.2025",
            "followers": "1.8K amigos",
            "verified": False,
            "location": "Azángaro, Puno"
        }
    },
    # 39. Alberto Eugenio Quintanilla Chacón - Alianza Electoral Venceremos
    "Alberto Eugenio Quintanilla Chacón": {
        "facebook": {
            "url": "https://www.facebook.com/alberto.quintanillachacon.1",
            "username": "alberto.quintanillachacon.1",
            "followers": "744 amigos",
            "verified": False,
            "location": "Puno, UNMSM, UNI"
        }
    },
    # 41. Ángel Gumercindo Huanca Yampara - PRIN
    "Ángel Gumercindo Huanca Yampara": {
        "facebook": {
            "url": "https://www.facebook.com/angel.gumercindo.huancayampara",
            "username": "angel.gumercindo.huancayampara",
            "followers": "1.9K seguidores",
            "verified": False,
            "location": "Puno"
        }
    },
    # 45. Rubén Alemán Gonzales - Perú Libre
    "Rubén Alemán Gonzales": {
        "facebook": {
            "url": "https://www.facebook.com/ruben.alemangonzales",
            "username": "ruben.alemangonzales",
            "followers": "1.7K amigos",
            "verified": False,
            "location": "UNA-PUNO, UANCV",
            "notes": "Docente Universitario"
        }
    },
    # 46. Manuela Vela Rengifo - Fuerza Popular
    "Manuela Vela Rengifo": {
        "facebook": {
            "url": "https://www.facebook.com/manuela.vela.5",
            "username": "manuela.vela.5",
            "followers": "514 amigos",
            "verified": False,
            "location": "La Paz, Hospital Daniel A. Carrión"
        }
    },
    # 50. Yessica Callata Quispe - Partido Demócrata Unido Perú
    "Yessica Callata Quispe": {
        "facebook": {
            "url": "https://www.facebook.com/yessica.callata.quispe",
            "username": "yessica.callata.quispe",
            "followers": "8.5K seguidores",
            "verified": False,
            "location": "Juliaca, UNA-PUNO"
        }
    },
    # 57. Omar Condori Cuno - Perú Primero
    "Omar Condori Cuno": {
        "facebook": {
            "url": "https://www.facebook.com/omar.condori.3",
            "username": "omar.condori.3",
            "followers": "1.1K amigos",
            "verified": False,
            "location": "Lima/Puno, Preparatoria La Academia"
        }
    }
}


class SocialIntegrator:
    """Integra datos de redes sociales en las fichas de candidatos."""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.output_path = self.base_path / "output" / "publicaciones"
        self.updated_count = 0
        self.skipped_count = 0

    def log(self, mensaje: str, nivel: str = "info"):
        """Registra un mensaje."""
        if nivel == "info":
            logger.info(mensaje)
        elif nivel == "error":
            logger.error(mensaje)
        elif nivel == "warning":
            logger.warning(mensaje)

    def find_candidate_folder(self, candidate_name: str) -> Optional[Path]:
        """Busca la carpeta de un candidato por nombre."""
        if not self.output_path.exists():
            return None

        for carpeta in self.output_path.iterdir():
            if carpeta.is_dir():
                processed_path = carpeta / "candidate_processed.json"
                if processed_path.exists():
                    try:
                        with open(processed_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            full_name = data.get("identity", {}).get("full_name", "")
                            if full_name == candidate_name:
                                return carpeta
                    except:
                        pass
        return None

    def update_candidate_json(self, carpeta: Path, social_data: Dict) -> bool:
        """Actualiza el JSON del candidato con datos de redes sociales."""
        processed_path = carpeta / "candidate_processed.json"

        try:
            with open(processed_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Agregar o actualizar el bloque social_media
            data["social_media"] = social_data

            with open(processed_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            self.log(f"Error actualizando JSON: {e}", "error")
            return False

    def update_html_with_social(self, carpeta: Path, social_data: Dict) -> bool:
        """Actualiza el HTML del candidato con datos de redes sociales prellenados."""
        html_path = carpeta / "index.html"

        if not html_path.exists():
            self.log(f"HTML no existe en {carpeta.name}", "warning")
            return False

        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Extraer datos
            fb = social_data.get("facebook", {})
            ig = social_data.get("instagram", {})
            tk = social_data.get("tiktok", {})

            fb_url = fb.get("url", "")
            fb_followers = fb.get("followers", "")
            fb_verified = " (Verificado)" if fb.get("verified") else ""

            ig_user = ig.get("username", "")
            ig_url = ig.get("url", "")

            tk_user = tk.get("username", "")
            tk_url = tk.get("url", "")
            tk_followers = tk.get("followers", "")

            # Generar observaciones
            obs_parts = []
            if fb_followers:
                obs_parts.append(f"Facebook: {fb_followers} seguidores{fb_verified}")
            if tk_followers:
                obs_parts.append(f"TikTok: {tk_followers} seguidores")
            observaciones = ". ".join(obs_parts) if obs_parts else ""

            # Crear nueva sección social con valores prellenados
            new_social_section = f'''<div class="section social-section">
            <h2>📱 Redes Sociales Identificadas</h2>

            <label>Facebook:</label>
            <input type="text" value="{fb_url}" readonly style="background: #e8f5e9;" />

            <label>Instagram:</label>
            <input type="text" value="{ig_url if ig_url else ig_user}" {"readonly style='background: #e8f5e9;'" if ig_url or ig_user else 'placeholder="@usuario"'} />

            <label>TikTok:</label>
            <input type="text" value="{tk_url if tk_url else tk_user}" {"readonly style='background: #e8f5e9;'" if tk_url or tk_user else 'placeholder="@usuario"'} />

            <label>WhatsApp:</label>
            <input type="text" placeholder="Número de contacto" />

            <label>Observaciones de actividad en redes:</label>
            <textarea rows="3" style="background: #e8f5e9;">{observaciones}</textarea>

            <label>Mapa de actividad (enlaces y hallazgos):</label>
            <textarea rows="3" placeholder="Pegar enlaces relevantes encontrados..."></textarea>
        </div>'''

            # Reemplazar la sección social existente
            import re
            pattern = r'<div class="section social-section">.*?</div>\s*(?=<div class="footer">)'
            html_content = re.sub(pattern, new_social_section + '\n\n        ', html_content, flags=re.DOTALL)

            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            return True
        except Exception as e:
            self.log(f"Error actualizando HTML: {e}", "error")
            return False

    def integrate_all(self):
        """Integra todos los datos de redes sociales disponibles."""
        self.updated_count = 0
        self.skipped_count = 0

        self.log(f"Iniciando integración de {len(SOCIAL_MEDIA_DATA)} candidatos con redes sociales...")

        for nombre, social_data in SOCIAL_MEDIA_DATA.items():
            carpeta = self.find_candidate_folder(nombre)

            if carpeta:
                self.log(f"Procesando: {nombre} ({carpeta.name})")

                # Actualizar JSON
                if self.update_candidate_json(carpeta, social_data):
                    self.log(f"  -> JSON actualizado")

                # Actualizar HTML
                if self.update_html_with_social(carpeta, social_data):
                    self.log(f"  -> HTML actualizado")
                    self.updated_count += 1
                else:
                    self.skipped_count += 1
            else:
                self.log(f"No encontrado: {nombre}", "warning")
                self.skipped_count += 1

        self.log(f"Completado: {self.updated_count} actualizados, {self.skipped_count} omitidos")
        return self.updated_count, self.skipped_count

    def add_social_data(self, candidate_name: str, social_data: Dict) -> bool:
        """Agrega datos de redes sociales para un candidato específico."""
        carpeta = self.find_candidate_folder(candidate_name)

        if not carpeta:
            self.log(f"Candidato no encontrado: {candidate_name}", "error")
            return False

        # Actualizar JSON
        self.update_candidate_json(carpeta, social_data)

        # Actualizar HTML
        return self.update_html_with_social(carpeta, social_data)

    def list_candidates_without_social(self) -> List[str]:
        """Lista candidatos que no tienen datos de redes sociales."""
        sin_redes = []

        if not self.output_path.exists():
            return sin_redes

        for carpeta in self.output_path.iterdir():
            if carpeta.is_dir():
                processed_path = carpeta / "candidate_processed.json"
                if processed_path.exists():
                    try:
                        with open(processed_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            full_name = data.get("identity", {}).get("full_name", "")
                            if "social_media" not in data and full_name:
                                sin_redes.append(full_name)
                    except:
                        pass

        return sorted(sin_redes)


def main():
    """Función principal."""
    import argparse

    parser = argparse.ArgumentParser(description="Integrar datos de redes sociales")
    parser.add_argument("--list-pending", action="store_true", help="Listar candidatos sin redes sociales")
    args = parser.parse_args()

    integrator = SocialIntegrator()

    if args.list_pending:
        pendientes = integrator.list_candidates_without_social()
        print(f"\nCandidatos sin datos de redes sociales ({len(pendientes)}):")
        for nombre in pendientes:
            print(f"  - {nombre}")
    else:
        integrator.integrate_all()


if __name__ == "__main__":
    main()
