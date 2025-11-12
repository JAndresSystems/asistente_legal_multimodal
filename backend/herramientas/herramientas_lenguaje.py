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
    """Analiza evidencia multimodal (texto, imágenes, PDFs) y maneja audio mediante transcripción.
    Devuelve un objeto JSON con el análisis estructurado."""
    if not llm_multimodal:
        return {"error": "El modelo de lenguaje no está disponible."}
    
    try:
        # 1. Preparar contenido multimodal inicial con el prompt
        contenido_para_analisis = [{"type": "text", "text": prompt_usuario}]
        archivos_procesados = []
        errores_procesamiento = []
        texto_transcrito_audio = ""
        
        # 2. Procesar cada archivo según su tipo
        for ruta_archivo in archivos_locales:
            tipo_mime, _ = mimetypes.guess_type(ruta_archivo)
            nombre_archivo = os.path.basename(ruta_archivo)
            
            if not tipo_mime:
                errores_procesamiento.append(f"Archivo no reconocido: {nombre_archivo}")
                continue
                
            # Manejar PDFs e imágenes directamente con Gemini
            if tipo_mime == 'application/pdf' or tipo_mime.startswith('image/'):
                print(f"📄/🖼️ Procesando {tipo_mime} directamente con Gemini: {nombre_archivo}")
                try:
                    # Usar tu función existente para preparar la entrada multimodal
                    contenido_multimodal = preparar_entrada_multimodal("", [ruta_archivo])
                    if len(contenido_multimodal) > 1:  # Si se añadió contenido multimodal
                        contenido_para_analisis.extend(contenido_multimodal[1:])  # Excluir el prompt vacío
                        archivos_procesados.append(f"✅ {nombre_archivo} ({tipo_mime.split('/')[1]})")
                except Exception as e:
                    errores_procesamiento.append(f"Error procesando {nombre_archivo}: {str(e)}")
            
            # Manejar audio: transcripción primero, luego enviar texto a Gemini
            elif tipo_mime.startswith('audio/'):
                print(f"🎵 Detectado archivo de audio para transcripción: {nombre_archivo}")
                try:
                    # Transcribir audio localmente
                    texto_transcrito = transcribir_audio_local(ruta_archivo)
                    if texto_transcrito:
                        texto_transcrito_audio += f"\n\n--- TRANSCRIPCIÓN DE AUDIO: {nombre_archivo} ---\n{texto_transcrito}"
                        archivos_procesados.append(f"✅ Audio transcrito: {nombre_archivo}")
                    else:
                        errores_procesamiento.append(f"No se pudo transcribir el audio: {nombre_archivo}")
                except Exception as e:
                    errores_procesamiento.append(f"Error transcribiendo {nombre_archivo}: {str(e)}")
            
            # Manejar videos: extraer audio y transcribir
            elif tipo_mime.startswith('video/'):
                print(f"🎬 Detectado archivo de video para extracción de audio: {nombre_archivo}")
                try:
                    # Extraer audio del video y transcribir
                    texto_transcrito = extraer_y_transcribir_video(ruta_archivo)
                    if texto_transcrito:
                        texto_transcrito_audio += f"\n\n--- TRANSCRIPCIÓN DE VIDEO: {nombre_archivo} ---\n{texto_transcrito}"
                        archivos_procesados.append(f"✅ Video transcrito: {nombre_archivo}")
                    else:
                        errores_procesamiento.append(f"No se pudo transcribir el video: {nombre_archivo}")
                except Exception as e:
                    errores_procesamiento.append(f"Error procesando video {nombre_archivo}: {str(e)}")
            
            else:
                errores_procesamiento.append(f"Formato no compatible: {nombre_archivo} ({tipo_mime})")
        
        # 3. Añadir transcripciones de audio/video al contenido si existen
        if texto_transcrito_audio:
            contenido_para_analisis.append({"type": "text", "text": texto_transcrito_audio})
        
        # 4. Si no hay contenido multimodal válido después del procesamiento
        if len(contenido_para_analisis) == 1 and (errores_procesamiento or not archivos_procesados):
            return {
                "error": "sin_contenido_valido",
                "archivos_procesados": archivos_procesados,
                "errores": errores_procesamiento,
                "mensaje": "No se pudo procesar ningún archivo válido. Por favor, suba archivos PDF, JPG, PNG o describa su caso por escrito."
            }
        
        # 5. Invocar a Gemini con el contenido preparado
        mensaje = HumanMessage(content=contenido_para_analisis)
        print(f"✨ Invocando Gemini con {len(contenido_para_analisis)} elementos para análisis")
        
        respuesta = llm_multimodal.invoke([mensaje])
        texto_respuesta = respuesta.content.strip()
        
        # 6. Limpiar y parsear la respuesta JSON
        if texto_respuesta.startswith("```json"):
            texto_respuesta = texto_respuesta[7:-3].strip()
        
        try:
            resultado = json.loads(texto_respuesta)
            # Añadir información de procesamiento
            if archivos_procesados or errores_procesamiento:
                resultado["metadatos_procesamiento"] = {
                    "archivos_procesados": archivos_procesados,
                    "errores": errores_procesamiento
                }
            return resultado
        except json.JSONDecodeError:
            return {
                "error": "respuesta_invalida",
                "mensaje": "Gemini no devolvió una respuesta en formato JSON válido",
                "respuesta_original": texto_respuesta,
                "archivos_procesados": archivos_procesados,
                "errores": errores_procesamiento
            }
    
    except Exception as e:
        error_msg = f"Error crítico durante el análisis multimodal: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "error": "error_critico",
            "mensaje": "Error interno al procesar los archivos. Por favor, intente nuevamente o describa su caso por escrito.",
            "detalle": error_msg,
            "solucion": "Para archivos de audio/video, asegúrese de que estén en formato compatible o describa su caso por escrito."
        }

# Funciones auxiliares para transcripción de audio/video
def transcribir_audio_local(ruta_audio: str) -> str:
    """Transcribe un archivo de audio local usando SpeechRecognition."""
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(ruta_audio) as source:
            audio_data = recognizer.record(source)
            return recognizer.recognize_google(audio_data, language='es-CO')
    except ImportError:
        print("⚠️ SpeechRecognition no está instalado. Instale con: pip install SpeechRecognition pydub")
        return None
    except Exception as e:
        print(f"❌ Error transcribiendo audio: {str(e)}")
        return None

def extraer_y_transcribir_video(ruta_video: str) -> str:
    """Extrae el audio de un video y lo transcribe."""
    try:
        from pydub import AudioSegment
        import tempfile
        
        # Crear archivo temporal para el audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            ruta_audio_temp = temp_audio.name
        
        # Convertir video a audio
        audio = AudioSegment.from_file(ruta_video)
        audio.export(ruta_audio_temp, format='wav')
        
        # Transcribir el audio
        texto_transcrito = transcribir_audio_local(ruta_audio_temp)
        
        # Limpiar archivo temporal
        os.unlink(ruta_audio_temp)
        return texto_transcrito
    except ImportError:
        print("⚠️ pydub no está instalado. Instale con: pip install pydub")
        return None
    except Exception as e:
        print(f"❌ Error procesando video: {str(e)}")
        return None
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