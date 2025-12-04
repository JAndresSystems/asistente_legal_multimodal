# backend/herramientas/herramientas_lenguaje.py
#gemini-3-pro-preview   gemini-2.5-flash
# backend/herramientas/herramientas_lenguaje.py
#gemini-3-pro-preview   gemini-2.5-flash
# backend/herramientas/herramientas_lenguaje.py
import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict, Any

from PIL import Image
import io

from .herramienta_multimodal_gemini import preparar_entrada_multimodal

load_dotenv()

# ==============================================================================
# Definición global del nombre del modelo (evita redundancia)
# Usamos Gemini 3.0, el más inteligente y reciente disponible en diciembre 2025
# ==============================================================================
MODEL_NAME = "gemini-2.5-flash"  # Versión más reciente y avanzada, superior a 2.5-flash en inteligencia y razonamiento

# ==============================================================================
# Modelo Gemini Nativo (Usando la versión más reciente del SDK en diciembre 2025)
# ==============================================================================
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    # Modelo principal para multimodal con JSON forzado
    model_multimodal = genai.GenerativeModel(
        model_name=MODEL_NAME,
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
        generation_config={
            "temperature": 0,
            "response_mime_type": "application/json"  # Forzado para JSON en análisis
        }
    )
    
    # Modelo separado para generación de texto plano (sin JSON mime)
    model_texto = genai.GenerativeModel(
        model_name=MODEL_NAME,
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
        generation_config={
            "temperature": 0,
            "response_mime_type": "text/plain"  # Para respuestas de texto simple
        }
    )
    
    print(f"TOOL-SETUP: Gemini {MODEL_NAME} nativo inicializado correctamente (JSON y texto modes).")
except Exception as e:
    model_multimodal = None
    model_texto = None
    print(f"TOOL-SETUP-ERROR: Fallo al inicializar Gemini nativo: {e}")

# ==============================================================================
# Compresión de imágenes (mantiene tu código original)
# ==============================================================================
def _comprimir_imagen_si_es_necesario(ruta_archivo: str, calidad: int = 80) -> str:
    try:
        with Image.open(ruta_archivo) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=calidad, optimize=True)
            with open(ruta_archivo, "wb") as f:
                f.write(buffer.getvalue())
            print(f"--- [COMPRESOR] Imagen comprimida: {ruta_archivo}")
            return ruta_archivo
    except Exception as e:
        print(f"--- [COMPRESOR] Fallo al comprimir: {e}")
        return ruta_archivo

# ==============================================================================
# Análisis Multimodal (FUNCIONA con audio/video/PDF grandes en 2025)
# ==============================================================================
def analizar_evidencia_con_gemini(prompt_usuario: str, archivos_locales: List[str]) -> Dict[str, Any]:
    if not model_multimodal:
        return {"error": "Modelo Gemini no disponible."}

    try:
        # Comprimir solo imágenes
        rutas_ok = []
        for ruta in archivos_locales:
            if ruta.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                rutas_ok.append(_comprimir_imagen_si_es_necesario(ruta))
            else:
                rutas_ok.append(ruta)

        contenido = preparar_entrada_multimodal(prompt_usuario, rutas_ok)

        print(f"      INVOCANDO Gemini con {len(rutas_ok)} archivo(s)...")
        response = model_multimodal.generate_content(contenido)

        texto = response.text.strip()

        # Limpieza agresiva de caracteres raros
        texto_limpio = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', texto)

        try:
            resultado = json.loads(texto_limpio)
            print("      JSON válido recibido del modelo.")
            return resultado
        except json.JSONDecodeError as e:
            print(f"      JSON FALLÓ: {e}")
            return {"error": "Respuesta no es JSON válido", "respuesta_original": texto_limpio}

    except Exception as e:
        error_msg = f"Error crítico en Gemini: {str(e)}"
        print(f"      {error_msg}")
        return {"error": error_msg}

# ==============================================================================
# Herramienta de Generación de Texto Plano (AHORA EXPORTADA CORRECTAMENTE)
# ==============================================================================
def generar_respuesta_texto(prompt: str) -> str:
    """Toma un prompt de texto y devuelve la respuesta del LLM como un string 
    de texto plano. Ideal para tareas de síntesis o conversacionales, como el 
    Agente de Atencion.
    
    Args:
        prompt (str): El prompt o la pregunta a realizar al modelo.
        
    Returns:
        (str): La respuesta del modelo como una cadena de texto.
    """
    if not model_texto:
        return "Error: El modelo de texto no está disponible."
        
    try:
        print(f"      TOOL-SYSTEM: -> Invocando Gemini (texto plano)...")
        response = model_texto.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        error_msg = f"Error crítico durante la generación de texto con Gemini: {e}"
        print(f"      ERROR-CRITICO: {error_msg}")
        return error_msg