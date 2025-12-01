# backend/herramientas/herramientas_lenguaje.py
#gemini-3-pro-preview   gemini-2.5-flash
# Ubicación: backend/herramientas/herramientas_lenguaje.py
# Ubicación: backend/herramientas/herramientas_lenguaje.py
import os
import json
import base64
import re  # <--  Importamos el módulo de expresiones regulares
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from typing import List, Dict, Any
from pathlib import Path
import mimetypes
import fitz  # PyMuPDF

load_dotenv()

# --- INICIALIZACIÓN DEL MODELO DE LENGUAJE ---
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

# --- FUNCIONES AUXILIARES ---

def _preparar_entrada_multimodal_imagenes(prompt_texto: str, rutas_imagenes: List[str]) -> List[Dict[str, Any]]:
    """
    Prepara el contenido para Gemini, incluyendo un prompt de texto y
    codificando las imágenes en base64 en el formato correcto que la librería espera.
    """
    contenido_multimodal = [{"type": "text", "text": prompt_texto}]
    for ruta in rutas_imagenes:
        try:
            tipo_mime, _ = mimetypes.guess_type(ruta)
            if not tipo_mime or not tipo_mime.startswith("image/"):
                continue
            with open(ruta, "rb") as f:
                contenido_binario = f.read()
            contenido_multimodal.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{tipo_mime};base64,{base64.b64encode(contenido_binario).decode('utf-8')}"
                }
            })
        except Exception as e:
            print(f"      ERROR-IMAGEN: No se pudo procesar la imagen {ruta}: {e}")
    return contenido_multimodal

def _extraer_texto_de_pdf(ruta_archivo: str) -> str:
    """
    Abre un archivo PDF y extrae todo su contenido de texto.
    """
    try:
        texto_completo = ""
        with fitz.open(ruta_archivo) as doc:
            for pagina in doc:
                texto_completo += pagina.get_text()
        print(f"      INFO-PDF: Texto extraído exitosamente de {Path(ruta_archivo).name}")
        return texto_completo
    except Exception as e:
        print(f"      ERROR-PDF: No se pudo extraer texto de {ruta_archivo}: {e}")
        return ""

# --- FUNCIONES PRINCIPALES ---

def analizar_evidencia_con_gemini(prompt_usuario: str, archivos_locales: List[str]) -> Dict[str, Any]:
    """
    Función de análisis multimodal reconstruida y robusta.
    """
    if not llm_multimodal:
        return {"error": "El modelo de IA no está disponible."}
        
    try:
        rutas_imagenes = []
        textos_de_pdfs = []

        for ruta in archivos_locales:
            tipo_mime, _ = mimetypes.guess_type(ruta)
            if tipo_mime == "application/pdf":
                texto_pdf = _extraer_texto_de_pdf(ruta)
                if texto_pdf:
                    header = f"\n\n--- INICIO CONTENIDO DEL DOCUMENTO '{Path(ruta).name}' ---\n"
                    footer = f"\n--- FIN CONTENIDO DEL DOCUMENTO '{Path(ruta).name}' ---"
                    textos_de_pdfs.append(header + texto_pdf + footer)
            elif tipo_mime and tipo_mime.startswith("image/"):
                rutas_imagenes.append(ruta)

        prompt_enriquecido = prompt_usuario
        if textos_de_pdfs:
            prompt_enriquecido += "\n\n" + "\n".join(textos_de_pdfs)

        contenido_para_gemini = _preparar_entrada_multimodal_imagenes(prompt_enriquecido, rutas_imagenes)
        mensaje = HumanMessage(content=contenido_para_gemini)
        
        print(f"      TOOL-SYSTEM: -> Invocando Gemini ({len(rutas_imagenes)} imágenes y {len(textos_de_pdfs)} PDFs procesados)...")
        respuesta = llm_multimodal.invoke([mensaje])
        texto_crudo = respuesta.content.strip()
        
        match = re.search(r'\{.*\}', texto_crudo, re.DOTALL)
        if match:
            texto_limpio = match.group(0)
            return json.loads(texto_limpio)
        else:
            raise json.JSONDecodeError("No se encontró un objeto JSON en la respuesta.", texto_crudo, 0)
        
    except Exception as e:
        print(f"      ERROR-CRITICO en analizar_evidencia_con_gemini: {e}")
        return {"error": str(e)}

def generar_respuesta_texto(prompt: str) -> str:
    if not llm_multimodal: return "Error: El modelo de IA no está disponible."
    try:
        return llm_multimodal.invoke(prompt).content.strip()
    except Exception as e:
        return str(e)