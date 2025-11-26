# backend/herramientas/herramientas_lenguaje.py
#gemini-3-pro-preview   gemini-2.5-flash


# backend/herramientas/herramientas_lenguaje.py
import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from typing import List, Dict, Any
from PIL import Image
import io
import langchain 

# --- PARCHE DE COMPATIBILIDAD ---
if not hasattr(langchain, 'verbose'):
    langchain.verbose = False
if not hasattr(langchain, 'debug'):
    langchain.debug = False
if not hasattr(langchain, 'llm_cache'):
    langchain.llm_cache = None
# --------------------------------

from .herramienta_multimodal_gemini import preparar_entrada_multimodal

load_dotenv()

# Usamos Flash por velocidad. Ajustamos safety settings para que no bloquee imágenes médicas.
try:
    llm_multimodal = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )
    print("TOOL-SETUP: Modelo Gemini 2.5 Flash inicializado.")
except Exception as e:
    llm_multimodal = None
    print(f"TOOL-SETUP-ERROR: {e}")

def _comprimir_imagen_si_es_necesario(ruta_archivo: str, calidad: int = 80) -> str:
    try:
        with Image.open(ruta_archivo) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=calidad, optimize=True)
            with open(ruta_archivo, "wb") as f:
                f.write(buffer.getvalue())
            return ruta_archivo
    except Exception:
        return ruta_archivo

def analizar_evidencia_con_gemini(prompt_usuario: str, archivos_locales: List[str]) -> Dict[str, Any]:
    if not llm_multimodal:
        return {"error": "Modelo no disponible."}
        
    try:
        rutas_procesadas = []
        for ruta in archivos_locales:
            if ruta.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                rutas_procesadas.append(_comprimir_imagen_si_es_necesario(ruta))
            else:
                rutas_procesadas.append(ruta)

        contenido = preparar_entrada_multimodal(prompt_usuario, rutas_procesadas)
        mensaje = HumanMessage(content=contenido)
        
        print(f"      TOOL-SYSTEM: -> Invocando Gemini ({len(rutas_procesadas)} archivos)...")
        respuesta = llm_multimodal.invoke([mensaje])
        texto_crudo = respuesta.content.strip()
        
        # 1. INTENTO DE LIMPIEZA ESTÁNDAR (Si viene como bloque de código)
        texto_limpio = texto_crudo
        if "```json" in texto_crudo:
            # Extraemos solo lo que está dentro de los bloques ```json ... ```
            partes = texto_crudo.split("```json")
            if len(partes) > 1:
                texto_limpio = partes[1].split("```")[0].strip()
        elif "```" in texto_crudo:
            texto_limpio = texto_crudo.split("```")[1].strip()

        return json.loads(texto_limpio)
        
    except json.JSONDecodeError:
        # --- ESTRATEGIA DE RESCATE INTELIGENTE V3 ---
        print(f"      ALERTA: Gemini mezcló texto y JSON. Intentando separar...")
        
        # Caso Típico: "Hola soy Camila... {json}"
        # Buscamos dónde empieza el primer '{' y dónde termina el último '}'
        inicio_json = texto_crudo.find('{')
        fin_json = texto_crudo.rfind('}')
        
        if inicio_json != -1 and fin_json != -1:
            try:
                json_part = texto_crudo[inicio_json:fin_json+1]
                data = json.loads(json_part)
                # Si logramos extraer el JSON, usamos ese.
                return data
            except:
                pass # Si falla, seguimos al plan B
        
        # Plan B: Si no hay JSON válido, usamos todo el texto como mensaje
        return {
            "admisible": False,
            "justificacion": "Respuesta conversacional recuperada.",
            "hechos_clave": "Análisis en curso.",
            "informacion_suficiente": False,
            "pregunta_para_usuario": texto_crudo # Mostramos lo que dijo Camila
        }
        
    except Exception as e:
        print(f"      ERROR-CRITICO: {e}")
        return {"error": str(e)}

def generar_respuesta_texto(prompt: str) -> str:
    if not llm_multimodal: return "Error modelo."
    try:
        return llm_multimodal.invoke(prompt).content.strip()
    except Exception as e:
        return str(e)