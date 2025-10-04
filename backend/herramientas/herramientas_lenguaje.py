import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from typing import List, Dict, Any

from .herramienta_multimodal_gemini import preparar_entrada_multimodal

load_dotenv()

try:
    llm_multimodal = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
    print("TOOL-SETUP: Modelo Gemini 2.5 Flash inicializado correctamente.")
except Exception as e:
    llm_multimodal = None
    print(f"TOOL-SETUP-ERROR: No se pudo inicializar Gemini. Causa: {e}")

# --- FUNCIÓN ESPECIALIZADA EN DEVOLVER JSON ---
def analizar_evidencia_con_gemini(prompt: str, rutas_archivos: List[str]) -> Dict[str, Any]:
    """Analiza evidencia y FUERZA una respuesta en formato JSON."""
    if not llm_multimodal: return {"error": "El modelo de lenguaje no está disponible."}
    try:
        contenido_listo = preparar_entrada_multimodal(prompt, rutas_archivos)
        mensaje = HumanMessage(content=contenido_listo)
        print(f"      TOOL-SYSTEM: -> Invocando a Gemini 2.5 Flash (esperando JSON) con {len(rutas_archivos)} archivo(s)...")
        respuesta = llm_multimodal.invoke([mensaje])
        texto_respuesta = respuesta.content.strip()
        if texto_respuesta.startswith("```json"): texto_respuesta = texto_respuesta[7:-3]
        return json.loads(texto_respuesta)
    except json.JSONDecodeError:
        error_msg = f"Error: El modelo no devolvió un JSON válido. Respuesta: {texto_respuesta[:200]}"
        print(f"      ERROR-CRITICO: {error_msg}")
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Error crítico durante el análisis JSON con Gemini: {e}"
        print(f"      ERROR-CRITICO: {error_msg}")
        return {"error": error_msg}

# --- NUEVA FUNCIÓN GENÉRICA PARA DEVOLVER TEXTO PLANO ---
def generar_respuesta_texto(prompt: str) -> str:
    """
    Toma un prompt de texto y devuelve la respuesta del LLM como un string de texto plano.
    Ideal para tareas de síntesis o conversacionales.
    """
    if not llm_multimodal: return "Error: El modelo de lenguaje no está disponible."
    try:
        print(f"      TOOL-SYSTEM: -> Invocando a Gemini 2.5 Flash (esperando TEXTO)...")
        respuesta = llm_multimodal.invoke(prompt)
        return respuesta.content.strip()
    except Exception as e:
        error_msg = f"Error crítico durante la generación de texto con Gemini: {e}"
        print(f"      ERROR-CRITICO: {error_msg}")
        return error_msg