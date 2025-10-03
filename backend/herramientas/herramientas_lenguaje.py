import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from typing import List, Dict, Any

from .herramienta_multimodal_gemini import preparar_entrada_multimodal

# --- CONFIGURACIÓN INICIAL ---
load_dotenv()

# --- INICIALIZACIÓN DEL MODELO DE LENGUAJE ---
try:
    # CORRECCIÓN DEFINITIVA: Se establece el modelo correcto y no negociable.
    llm_multimodal = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    print("TOOL-SETUP: Modelo Gemini 2.5 Flash inicializado correctamente.")
except Exception as e:
    llm_multimodal = None
    print(f"TOOL-SETUP-ERROR: No se pudo inicializar Gemini. Causa: {e}")

# =================================================================================
# FUNCIÓN CLAVE PARA LA NUEVA ARQUITECTURA
# =================================================================================

def analizar_evidencia_con_gemini(prompt: str, rutas_archivos: List[str]) -> Dict[str, Any]:
    """
    Analiza evidencia multimodal y devuelve una respuesta ESTRUCTURADA en JSON.

    Esta es la función central para interactuar con Gemini. Prepara los datos,
    invoca al modelo y se asegura de devolver un diccionario de Python (parseando
    la respuesta JSON del modelo), en lugar de texto plano.

    Args:
        prompt (str): La instrucción o pregunta para el modelo de IA.
        rutas_archivos (List[str]): Lista de rutas a los archivos de evidencia.

    Returns:
        Dict[str, Any]: La respuesta del modelo como un diccionario de Python.
                        Si hay un error, devuelve un diccionario con una clave 'error'.
    """
    if not llm_multimodal:
        return {"error": "El modelo de lenguaje Gemini no está disponible."}

    try:
        contenido_listo = preparar_entrada_multimodal(prompt, rutas_archivos)
        mensaje = HumanMessage(content=contenido_listo)
        
        print(f"      TOOL-SYSTEM: -> Invocando a Gemini 2.5 Flash con {len(rutas_archivos)} archivo(s)...")
        respuesta = llm_multimodal.invoke([mensaje])
        
        # El modelo DEBE devolver un JSON. Lo limpiamos y lo parseamos.
        texto_respuesta = respuesta.content.strip()
        
        # Limpieza para asegurar que es un JSON válido (quitando ```json y ```)
        if texto_respuesta.startswith("```json"):
            texto_respuesta = texto_respuesta[7:]
        if texto_respuesta.endswith("```"):
            texto_respuesta = texto_respuesta[:-3]
        
        return json.loads(texto_respuesta)

    except json.JSONDecodeError:
        error_msg = "Error: El modelo no devolvió un JSON válido."
        print(f"      ERROR-CRITICO: {error_msg} Respuesta recibida: {texto_respuesta[:200]}")
        return {"error": error_msg, "respuesta_bruta": texto_respuesta}
    except Exception as e:
        error_msg = f"Error crítico durante el análisis con Gemini: {e}"
        print(f"      ERROR-CRITICO: {error_msg}")
        return {"error": error_msg}