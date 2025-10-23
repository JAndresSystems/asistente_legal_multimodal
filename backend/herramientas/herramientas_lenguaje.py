#C:\react\asistente_legal_multimodal\backend\herramientas\herramientas_lenguaje.py
import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from typing import List, Dict, Any

from .herramienta_multimodal_gemini import preparar_entrada_multimodal

load_dotenv()

# ==============================================================================
# Inicializacion del Modelo de Lenguaje
# ==============================================================================
try:
    llm_multimodal = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
    print("TOOL-SETUP: Modelo Gemini 2.5 Flash inicializado correctamente.")
except Exception as e:
    llm_multimodal = None
    print(f"TOOL-SETUP-ERROR: No se pudo inicializar Gemini. Causa: {e}")


# ==============================================================================
# Herramienta de Analisis Multimodal con Salida Estructurada (JSON)
# ==============================================================================
def analizar_evidencia_con_gemini(prompt_usuario: str, archivos_locales: List[str]) -> Dict[str, Any]:
    """Analiza evidencia multimodal (texto e imagenes/PDFs) y fuerza una respuesta
    del LLM en formato JSON. Es la herramienta principal para agentes que
    necesitan extraer datos estructurados de documentos.

    Args:
        prompt_usuario (str): El prompt o la pregunta a realizar al modelo.
        archivos_locales (List[str]): Una lista de rutas a los archivos locales
                                     que serviran como contexto visual.

    Returns:
        (Dict[str, Any]): Un diccionario de Python parseado desde el JSON
                          devuelto por el modelo.
    """
    if not llm_multimodal:
        return {"error": "El modelo de lenguaje no está disponible."}
        
    try:
        # Usamos el nuevo nombre del parametro en la llamada a la funcion auxiliar
        contenido_listo = preparar_entrada_multimodal(prompt_usuario, archivos_locales)
        mensaje = HumanMessage(content=contenido_listo)
        
        print(f"      TOOL-SYSTEM: -> Invocando a Gemini 2.5 Flash (esperando JSON) con {len(archivos_locales)} archivo(s)...")
        respuesta = llm_multimodal.invoke([mensaje])
        texto_respuesta = respuesta.content.strip()
        
        if texto_respuesta.startswith("```json"):
            texto_respuesta = texto_respuesta[7:-3]
            
        return json.loads(texto_respuesta)
        
    except json.JSONDecodeError:
        error_msg = f"Error: El modelo no devolvió un JSON válido. Respuesta: {texto_respuesta[:200]}"
        print(f"      ERROR-CRITICO: {error_msg}")
        return {"error": error_msg, "respuesta_original": texto_respuesta}
    except Exception as e:
        error_msg = f"Error crítico durante el análisis JSON con Gemini: {e}"
        print(f"      ERROR-CRITICO: {error_msg}")
        return {"error": error_msg}

# ==============================================================================
# Herramienta de Generacion de Texto Plano
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
    if not llm_multimodal:
        return "Error: El modelo de lenguaje no está disponible."
        
    try:
        print(f"      TOOL-SYSTEM: -> Invocando a Gemini 2.5 Flash (esperando TEXTO)...")
        respuesta = llm_multimodal.invoke(prompt)
        return respuesta.content.strip()
    except Exception as e:
        error_msg = f"Error crítico durante la generación de texto con Gemini: {e}"
        print(f"      ERROR-CRITICO: {error_msg}")
        return error_msg