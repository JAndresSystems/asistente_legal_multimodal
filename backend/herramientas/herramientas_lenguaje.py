# backend/herramientas/herramientas_lenguaje.py

import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from typing import List, Dict, Any
import mimetypes
from pypdf import PdfReader
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
    """Versión robusta que maneja múltiples formatos de archivos y errores multimodales."""
    if not llm_multimodal:
        return {"error": "El modelo de lenguaje no está disponible."}
    
    try:
        # 1. Validación y clasificación de archivos antes de procesar
        archivos_procesables = []
        archivos_no_procesables = []
        texto_extraido = ""
        
        for archivo in archivos_locales:
            # Validar tipo MIME
            tipo_mime, _ = mimetypes.guess_type(archivo)
            
            if not tipo_mime:
                archivos_no_procesables.append({
                    "archivo": archivo,
                    "razon": "Tipo de archivo no reconocido"
                })
                continue
            
            # Clasificar por tipo de procesamiento
            if tipo_mime.startswith('application/pdf'):
                try:
                    # Extracción de texto para PDFs
                    reader = PdfReader(archivo)
                    contenido_pdf = ''.join(page.extract_text() or "" for page in reader.pages)
                    if contenido_pdf.strip():
                        texto_extraido += f"\n\n--- CONTENIDO PDF: {os.path.basename(archivo)} ---\n{contenido_pdf}"
                    else:
                        archivos_no_procesables.append({
                            "archivo": archivo,
                            "razon": "No se pudo extraer texto del PDF"
                        })
                except Exception as pdf_e:
                    archivos_no_procesables.append({
                        "archivo": archivo,
                        "razon": f"Error al procesar PDF: {str(pdf_e)}"
                    })
            
            elif tipo_mime.startswith('image/'):
                # Imágenes se procesan directamente con Gemini
                archivos_procesables.append(archivo)
            
            elif tipo_mime.startswith('audio/') or tipo_mime.startswith('video/'):
                # Archivos multimedia no compatibles directamente
                archivos_no_procesables.append({
                    "archivo": archivo,
                    "razon": "Formato de audio/video no compatible. Por favor transcribe el contenido como texto."
                })
            
            else:
                archivos_no_procesables.append({
                    "archivo": archivo,
                    "razon": f"Formato no compatible: {tipo_mime}"
                })

        # 2. Construir el prompt final con contenido procesable
        contenido_para_gemini = [prompt_usuario]
        
        if texto_extraido:
            contenido_para_gemini.append(texto_extraido)
        
        # Solo añadir imágenes si hay
        if archivos_procesables:
            contenido_para_gemini.extend(preparar_entrada_multimodal("", archivos_procesables)[1:])

        mensaje = HumanMessage(content=contenido_para_gemini)
        
        print(f"      TOOL-SYSTEM: -> Invocando Gemini 2.5 Flash con {len(archivos_procesables)} archivos procesables...")
        respuesta = llm_multimodal.invoke([mensaje])
        texto_respuesta = respuesta.content.strip()
        
        # Limpiar formato JSON si es necesario
        if texto_respuesta.startswith("```json"):
            texto_respuesta = texto_respuesta[7:-3].strip()
        
        # Parsear respuesta JSON
        try:
            resultado = json.loads(texto_respuesta)
            
            # Añadir información sobre archivos no procesables
            if archivos_no_procesables:
                if "advertencias" not in resultado:
                    resultado["advertencias"] = []
                
                for archivo in archivos_no_procesables:
                    resultado["advertencias"].append(
                        f"Archivo no procesado: {os.path.basename(archivo['archivo'])} - {archivo['razon']}"
                    )
            
            return resultado
            
        except json.JSONDecodeError as json_e:
            return {
                "error": f"JSON inválido en respuesta de Gemini: {str(json_e)}",
                "respuesta_original": texto_respuesta,
                "archivos_no_procesables": archivos_no_procesables
            }
    
    except Exception as e:
        error_msg = f"Error crítico durante el análisis multimodal: {str(e)}"
        print(f"      ERROR-CRITICO: {error_msg}")
        
        return {
            "error": error_msg,
            "tipo_error": "error_multimodal",
            "mensaje_usuario": (
                "Error al procesar archivos multimedia. Por favor, asegúrese de subir solo archivos "
                "en formato PDF, JPG o PNG. Los archivos de audio deben ser transcritos como texto."
            )
        }

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