# backend/herramientas/herramientas_lenguaje.py
#gemini-3-pro-preview   gemini-2.5-flash
# backend/herramientas/herramientas_lenguaje.py
#gemini-3-pro-preview   gemini-2.5-flash
# backend/herramientas/herramientas_lenguaje.py
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
# CAMBIO CLAVE: Usamos 'gemini-1.5-flash'
# Es más rápido, acepta videos más largos y obedece mejor el JSON que el Pro.
# ==============================================================================
MODEL_NAME = "gemini-3-pro-preview"  

# ==============================================================================
# Configuración de Seguridad "Permisiva" (Para evitar bloqueos por texto legal)
# ==============================================================================
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    # Modelo Multimodal
    model_multimodal = genai.GenerativeModel(
        model_name=MODEL_NAME,
        safety_settings=SAFETY_SETTINGS, # <--- APLICAMOS LA SEGURIDAD AQUÍ
        generation_config={
            "temperature": 0.2, # Un poco de creatividad ayuda a describir videos
            "response_mime_type": "application/json"
        }
    )
    
    # Modelo Texto
    model_texto = genai.GenerativeModel(
        model_name=MODEL_NAME,
        safety_settings=SAFETY_SETTINGS, # <--- APLICAMOS LA SEGURIDAD AQUÍ
        generation_config={
            "temperature": 0,
            "response_mime_type": "text/plain"
        }
    )
    
    print(f"TOOL-SETUP: Gemini {MODEL_NAME} nativo inicializado. Filtros desactivados.")
except Exception as e:
    model_multimodal = None
    model_texto = None
    print(f"TOOL-SETUP-ERROR: Fallo al inicializar Gemini: {e}")

# ==============================================================================
# Compresión de imágenes (Igual que antes)
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
# Análisis Multimodal
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

        print(f"      INVOCANDO Gemini ({MODEL_NAME}) con {len(rutas_ok)} archivo(s)...")
        
        # Invocamos al modelo
        response = model_multimodal.generate_content(contenido)

        # Manejo de Bloqueos de Seguridad (Por si acaso)
        try:
            texto = response.text.strip()
        except ValueError:
            print("      ALERTA: Gemini bloqueó la respuesta por seguridad.")
            print(f"      Feedback de seguridad: {response.prompt_feedback}")
            # Intento de rescate: Si bloquea, devolvemos esto para no romper el flujo
            return {
                "resumen_evidencia": "Video recibido. Contiene texto legal sobre un accidente.",
                "decision_triaje": "FALTA_INFORMACION",
                "justificacion": "El sistema de seguridad de IA marcó el contenido como sensible, pero se ha recibido la evidencia.",
                "mensaje_para_usuario": "Hemos recibido tu video. El sistema detectó términos sensibles (posibles lesiones descritas), pero el archivo está guardado. Por favor, confirma: ¿El video muestra documentos o lesiones físicas?",
                "hechos_clave": "Video con descripción de accidente."
            }

        # Limpieza de JSON
        texto_limpio = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', texto) # Quitar caracteres raros
        texto_limpio = texto_limpio.replace("```json", "").replace("```", "") # Quitar markdown si se escapa

        try:
            resultado = json.loads(texto_limpio)
            print("      JSON válido recibido del modelo.")
            return resultado
        except json.JSONDecodeError as e:
            print(f"      JSON FALLÓ: {e}")
            print(f"      TEXTO RECIBIDO: {texto_limpio}")
            return {"error": "Respuesta no es JSON válido", "respuesta_original": texto_limpio}

    except Exception as e:
        error_msg = f"Error crítico en Gemini: {str(e)}"
        print(f"      {error_msg}")
        return {"error": error_msg}

# ==============================================================================
# Generación de Texto Plano
# ==============================================================================
def generar_respuesta_texto(prompt: str) -> str:
    if not model_texto:
        return "Error: modelo no disponible."
    try:
        response = model_texto.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generando texto: {e}"