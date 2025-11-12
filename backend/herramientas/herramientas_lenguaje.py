# backend/herramientas/herramientas_lenguaje.py

import os
import json
import base64
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
        # 1. Validar y procesar archivos antes de enviar a Gemini
        contenido_para_analisis = [prompt_usuario]
        archivos_no_procesables = []
        
        for archivo in archivos_locales:
            tipo_mime, _ = mimetypes.guess_type(archivo)
            
            if not tipo_mime:
                archivos_no_procesables.append(f"Archivo no reconocido: {os.path.basename(archivo)}")
                continue
            
            # Manejar PDFs: extraer texto en lugar de enviar el archivo binario
            if tipo_mime == 'application/pdf':
                try:
                    reader = PdfReader(archivo)
                    texto_pdf = ""
                    for page in reader.pages:
                        texto_extraido = page.extract_text()
                        if texto_extraido:
                            texto_pdf += texto_extraido + "\n\n"
                    
                    if texto_pdf.strip():
                        contenido_para_analisis.append(f"--- CONTENIDO DEL PDF {os.path.basename(archivo)} ---\n{texto_pdf}")
                    else:
                        archivos_no_procesables.append(f"No se pudo extraer texto del PDF: {os.path.basename(archivo)}")
                except Exception as pdf_e:
                    archivos_no_procesables.append(f"Error al procesar PDF {os.path.basename(archivo)}: {str(pdf_e)}")
            
            # Manejar imágenes: enviar directamente a Gemini
            elif tipo_mime.startswith('image/'):
                try:
                    # Preparar el archivo de imagen para Gemini
                    with open(archivo, "rb") as f:
                        datos_imagen = f.read()
                    
                    # Añadir imagen al contenido
                    contenido_para_analisis.append({
                        "type": "media",
                        "mime_type": tipo_mime,
                        "data": base64.b64encode(datos_imagen).decode('utf-8')
                    })
                except Exception as img_e:
                    archivos_no_procesables.append(f"Error al procesar imagen {os.path.basename(archivo)}: {str(img_e)}")
            
            # Rechazar otros formatos con mensaje claro
            else:
                archivos_no_procesables.append(f"Formato no compatible: {os.path.basename(archivo)} (tipo: {tipo_mime})")

        # 2. Invocar a Gemini con el contenido procesado
        mensaje = HumanMessage(content=contenido_para_analisis)
        print(f"✨ Enviando a Gemini con {len(contenido_para_analisis)} elementos para análisis")
        
        respuesta = llm_multimodal.invoke([mensaje])
        texto_respuesta = respuesta.content.strip()
        
        # 3. Procesar respuesta JSON
        if texto_respuesta.startswith("```json"):
            texto_respuesta = texto_respuesta[7:-3].strip()
        
        try:
            resultado = json.loads(texto_respuesta)
            
            # Añadir advertencias si hay archivos no procesables
            if archivos_no_procesables:
                if "advertencias" not in resultado:
                    resultado["advertencias"] = []
                resultado["advertencias"].extend(archivos_no_procesables)
            
            return resultado
            
        except json.JSONDecodeError as json_e:
            return {
                "error": "Respuesta no válida de Gemini",
                "detalle": str(json_e),
                "respuesta_original": texto_respuesta[:200] + "..." if len(texto_respuesta) > 200 else texto_respuesta
            }
    
    except Exception as e:
        error_msg = f"Error crítico durante el análisis: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "error": "Error interno al procesar los archivos",
            "mensaje_usuario": "Por favor, asegúrese de subir archivos en formato PDF, JPG o PNG. Los archivos deben estar en buen estado y no dañados.",
            "detalle_tecnico": error_msg
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