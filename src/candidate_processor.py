"""
Procesador de Candidatos con DeepSeek API
Analiza metadata.json y genera fichas estructuradas + HTML
"""

import json
import os
import re
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
import requests
from loguru import logger

# Configuración de la API DeepSeek
DEEPSEEK_API_KEY = "sk-3babf30cbecb4ce697328c8b89af9162"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


class CandidateProcessor:
    """Procesa metadata de publicaciones y genera fichas de candidatos."""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.output_path = self.base_path / "output" / "publicaciones"

        # Callbacks para GUI
        self.on_progress: Optional[Callable] = None
        self.on_log: Optional[Callable] = None
        self.on_complete: Optional[Callable] = None

        # Estado
        self.running = False
        self.processed_count = 0
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
        """Obtiene carpetas que aún no tienen candidate_processed.json."""
        pendientes = []

        if not self.output_path.exists():
            return pendientes

        for carpeta in self.output_path.iterdir():
            if carpeta.is_dir():
                metadata_path = carpeta / "metadata.json"
                processed_path = carpeta / "candidate_processed.json"

                # Solo procesar si existe metadata pero no el procesado
                if metadata_path.exists() and not processed_path.exists():
                    pendientes.append(carpeta)

        return sorted(pendientes)

    def get_all_folders(self) -> List[Path]:
        """Obtiene todas las carpetas con metadata.json."""
        carpetas = []

        if not self.output_path.exists():
            return carpetas

        for carpeta in self.output_path.iterdir():
            if carpeta.is_dir():
                metadata_path = carpeta / "metadata.json"
                if metadata_path.exists():
                    carpetas.append(carpeta)

        return sorted(carpetas)

    def build_prompt(self, metadata: Dict[str, Any]) -> str:
        """Construye el prompt para DeepSeek - SOLO genera JSON, no HTML."""

        prompt = f"""Eres un analista político experto. Analiza el siguiente JSON de una publicación de Facebook sobre un candidato político.

## DATOS DE ENTRADA (JSON crudo del scraping):
```json
{json.dumps(metadata, ensure_ascii=False, indent=2)}
```

## INSTRUCCIONES - Genera un objeto JSON con exactamente estos 4 bloques:

### A) identity (clave para dashboard)
- full_name: nombre completo del candidato
- party: partido político
- role_sought: cargo al que postula (diputado/diputada, senador/senadora, etc.)
- region: región/departamento
- city: ciudad
- candidate_id: genera un ID único basado en el post_id + nombre

### B) post (auditoría / evidencia)
- source: "facebook"
- url: URL de la publicación
- post_id: ID de la publicación
- page_name: nombre de la página
- published_at_text: fecha como aparece
- published_at_iso: fecha en formato ISO si es posible, sino null
- scraped_at: fecha de scraping
- title: título corto
- hashtags: array de hashtags
- image: objeto con "url" (URL de imagen) y "local" (nombre archivo local)
- engagement: objeto con "reactions", "comments", "shares"
- raw_text: COPIA EXACTA de descripcion_completa SIN MODIFICAR

### C) profile (resumen estructurado)
- bio_summary: 2-4 líneas neutrales resumiendo al candidato
- birth: objeto con "date" y "place" si aparecen, sino null
- residence: lugar de residencia
- education: array de objetos con "degree", "institution", "year"
- work_experience: array de objetos con "company", "period", "roles"
- income_declaration: objeto con "year", "total", "breakdown" (desglose)
- assets: objeto con "real_estate", "vehicles", "total_value"

### D) political_risk (redflags y sensibilidad)
- redflags: array de objetos, cada uno con:
  - type: uno de ["denuncia", "inconsistencia", "solapamiento_laboral", "patrimonio", "afiliacion", "informacion_sensible", "desinformacion_posible", "experiencia_limitada", "otro"]
  - severity: número del 1 al 5
  - evidence_text: extracto CORTO del texto original que evidencia esto
  - notes: explicación breve
- overall_risk_score: número del 0 al 5 basado en los redflags
- sensitive_info: array de datos sensibles encontrados (fechas nacimiento exactas, domicilios, placas, etc.)

## REGLAS ESTRICTAS:
1. NO INVENTES datos. Si algo no está en el texto, usa null o "No especifica"
2. El raw_text debe ser EXACTAMENTE igual a descripcion_completa
3. Los redflags deben basarse SOLO en frases explícitas del texto
4. Sé objetivo y neutral en el análisis

## FORMATO DE RESPUESTA:
Responde ÚNICAMENTE con el JSON del CandidateRecord, sin explicaciones adicionales:
```json
{{
  "identity": {{ ... }},
  "post": {{ ... }},
  "profile": {{ ... }},
  "political_risk": {{ ... }}
}}
```
"""
        return prompt

    def call_deepseek_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Llama a la API de DeepSeek."""
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un analista político experto. Responde SIEMPRE en formato JSON válido."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 8000
        }

        try:
            response = requests.post(
                DEEPSEEK_API_URL,
                headers=headers,
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Extraer JSON de la respuesta
                return self._parse_api_response(content)
            else:
                self.log(f"Error API: {response.status_code} - {response.text}", "error")
                return None

        except requests.exceptions.Timeout:
            self.log("Timeout en la API de DeepSeek", "error")
            return None
        except Exception as e:
            self.log(f"Error llamando API: {e}", "error")
            return None

    def _parse_api_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parsea la respuesta de la API."""
        try:
            # Intentar parsear directamente
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Buscar JSON en bloques de código
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Buscar cualquier JSON válido
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        self.log("No se pudo parsear la respuesta de la API", "error")
        return None

    def process_folder(self, carpeta: Path) -> bool:
        """Procesa una carpeta individual - Solo genera JSON, no HTML."""
        metadata_path = carpeta / "metadata.json"

        try:
            # Leer metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            self.log(f"Procesando: {carpeta.name}")

            # Construir prompt y llamar API
            prompt = self.build_prompt(metadata)
            resultado = self.call_deepseek_api(prompt)

            if not resultado:
                self.log(f"  -> Sin respuesta de API", "warning")
                return False

            # El resultado ahora ES el candidate_record directamente
            # (ya no viene envuelto en {"candidate_record": ...})
            candidate_record = resultado

            # Si viene envuelto, extraerlo
            if "candidate_record" in resultado:
                candidate_record = resultado["candidate_record"]
            elif "identity" not in resultado:
                self.log(f"  -> Respuesta inválida de API", "warning")
                return False

            # Guardar candidate_processed.json
            processed_path = carpeta / "candidate_processed.json"
            with open(processed_path, 'w', encoding='utf-8') as f:
                json.dump(candidate_record, f, ensure_ascii=False, indent=2)
            self.log(f"  -> Guardado: candidate_processed.json")

            return True

        except Exception as e:
            self.log(f"Error procesando {carpeta.name}: {e}", "error")
            return False

    def process_all(self, solo_pendientes: bool = True):
        """Procesa todas las carpetas."""
        self.running = True
        self.processed_count = 0
        self.error_count = 0

        carpetas = self.get_pending_folders() if solo_pendientes else self.get_all_folders()
        total = len(carpetas)

        if total == 0:
            self.log("No hay carpetas pendientes de procesar")
            if self.on_complete:
                self.on_complete(0, 0)
            return

        self.log(f"Procesando {total} carpetas...")

        for i, carpeta in enumerate(carpetas, 1):
            if not self.running:
                self.log("Procesamiento detenido por el usuario")
                break

            if self.on_progress:
                self.on_progress(i, total, carpeta.name)

            if self.process_folder(carpeta):
                self.processed_count += 1
            else:
                self.error_count += 1

        self.running = False
        self.log(f"Completado: {self.processed_count} exitosos, {self.error_count} errores")

        if self.on_complete:
            self.on_complete(self.processed_count, self.error_count)

    def detener(self):
        """Detiene el procesamiento."""
        self.running = False
        self.log("Deteniendo procesamiento...")


def main():
    """Función principal para ejecución desde línea de comandos."""
    import argparse

    parser = argparse.ArgumentParser(description="Procesar candidatos con DeepSeek API")
    parser.add_argument("--all", action="store_true", help="Reprocesar todas las carpetas")
    parser.add_argument("--folder", type=str, help="Procesar una carpeta específica")
    args = parser.parse_args()

    processor = CandidateProcessor()

    if args.folder:
        carpeta = Path(args.folder)
        if carpeta.exists():
            processor.process_folder(carpeta)
        else:
            print(f"Carpeta no encontrada: {args.folder}")
    else:
        processor.process_all(solo_pendientes=not args.all)


if __name__ == "__main__":
    main()
