#C:\react\asistente_legal_multimodal\backend\herramientas\herramientas_lenguaje.py
import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from typing import List, Dict, Any


from PIL import Image
import io

from .herramienta_multimodal_gemini import preparar_entrada_multimodal

load_dotenv()

# ==============================================================================
# Inicializacion del Modelo de Lenguaje
#gemini-3-pro-preview  gemini-2.5-flash
# ==============================================================================
try:
    llm_multimodal = ChatGoogleGenerativeAI(model="gemini-3-pro-preview", google_api_key=os.getenv("GOOGLE_API_KEY"))
    print("TOOL-SETUP: Modelo Gemini 2.5 Flash inicializado correctamente.")
except Exception as e:
    llm_multimodal = None
    print(f"TOOL-SETUP-ERROR: No se pudo inicializar Gemini. Causa: {e}")



def _comprimir_imagen_si_es_necesario(ruta_archivo: str, calidad: int = 80) -> str:
    """
    Funcion interna para comprimir una imagen y sobreescribirla en formato JPEG.
    Reduce drasticamente los tokens de la conversion a base64.
    """
    try:
        # Abre la imagen
        with Image.open(ruta_archivo) as img:
            # Convierte a RGB para asegurar compatibilidad con JPEG
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Crea un buffer en memoria para guardar la imagen comprimida
            buffer_en_memoria = io.BytesIO()
            img.save(buffer_en_memoria, format='JPEG', quality=calidad, optimize=True)
            
            # Sobreescribe el archivo original con su version comprimida
            with open(ruta_archivo, "wb") as f:
                f.write(buffer_en_memoria.getvalue())

            print(f"--- [COMPRESOR] Imagen {ruta_archivo} comprimida exitosamente.")
            return ruta_archivo
    except Exception as e:
        print(f"--- [COMPRESOR] ADVERTENCIA: No se pudo comprimir la imagen {ruta_archivo}. Error: {e}. Se usará el original.")
        return ruta_archivo





# ==============================================================================
# Herramienta de Analisis Multimodal con Salida Estructurada (JSON)
# ==============================================================================
def analizar_evidencia_con_gemini(prompt_usuario: str, archivos_locales: List[str]) -> Dict[str, Any]:
    """Analiza evidencia multimodal (texto e imagenes/PDFs) y fuerza una respuesta
    del LLM en formato JSON."""
    if not llm_multimodal:
        return {"error": "El modelo de lenguaje no está disponible."}
        
    try:
        # --- INICIO DE LA MODIFICACIÓN #3: PASO DE COMPRESIÓN PREVIO ---
        rutas_procesadas = []
        for ruta in archivos_locales:
            if ruta.lower().endswith(('.png', '.jpg', '.jpeg')):
                # Si es una imagen, la comprimimos antes de cualquier otra cosa
                ruta_comprimida = _comprimir_imagen_si_es_necesario(ruta)
                rutas_procesadas.append(ruta_comprimida)
            else:
                # Si no es una imagen (ej. PDF, audio), la dejamos como está
                rutas_procesadas.append(ruta)
        # --- FIN DE LA MODIFICACIÓN #3 ---

        # Usamos las rutas ya procesadas (comprimidas si era necesario)
        contenido_listo = preparar_entrada_multimodal(prompt_usuario, rutas_procesadas)
        mensaje = HumanMessage(content=contenido_listo)
        
        print(f"      TOOL-SYSTEM: -> Invocando a Gemini 1.5 Flash (esperando JSON) con {len(rutas_procesadas)} archivo(s)...")
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