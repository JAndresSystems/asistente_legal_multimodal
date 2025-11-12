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
# Herramienta de Analisis Multimodal mejorada
# ==============================================================================
def analizar_evidencia_con_gemini(prompt_usuario: str, archivos_locales: List[str]) -> Dict[str, Any]:
    """Analiza evidencia multimodal con manejo robusto de errores y extracción de texto para PDFs."""
    if not llm_multimodal:
        return {"error": "El modelo de lenguaje no está disponible."}
    
    try:
        # Preparar contenido inicial con el prompt
        contenido_para_analisis = [{"type": "text", "text": prompt_usuario}]
        archivos_procesados = []
        errores_procesamiento = []
        texto_transcrito_audio = ""
        
        for ruta_archivo in archivos_locales:
            tipo_mime, _ = mimetypes.guess_type(ruta_archivo)
            nombre_archivo = os.path.basename(ruta_archivo)
            
            if not tipo_mime:
                errores_procesamiento.append(f"Archivo no reconocido: {nombre_archivo}")
                continue
                
            # Manejo ESPECÍFICO para PDFs - EXTRAER TEXTO
            if tipo_mime == 'application/pdf':
                print(f"📄 Procesando PDF: {nombre_archivo}")
                try:
                    # EXTRAER TEXTO DEL PDF
                    reader = PdfReader(ruta_archivo)
                    texto_pdf = ""
                    for page in reader.pages:
                        texto_extraido = page.extract_text() or ""
                        if texto_extraido.strip():
                            texto_pdf += texto_extraido + "\n\n"
                    
                    if texto_pdf.strip():
                        contenido_para_analisis.append(f"--- CONTENIDO DEL PDF {nombre_archivo} ---\n{texto_pdf}")
                        archivos_procesados.append(f"✅ PDF procesado: {nombre_archivo}")
                        print(f"✅ Texto extraído exitosamente de {nombre_archivo} ({len(texto_pdf)} caracteres)")
                    else:
                        errores_procesamiento.append(f"No se pudo extraer texto del PDF: {nombre_archivo}")
                        print(f"❌ No se pudo extraer texto del PDF: {nombre_archivo}")
                except Exception as pdf_e:
                    error_msg = f"Error al procesar PDF {nombre_archivo}: {str(pdf_e)}"
                    errores_procesamiento.append(error_msg)
                    print(f"❌ {error_msg}")
            
            # Manejo para IMÁGENES - enviar directamente
            elif tipo_mime.startswith('image/'):
                print(f"🖼️ Procesando imagen: {nombre_archivo}")
                try:
                    contenido_imagen = preparar_entrada_multimodal("", [ruta_archivo])
                    if len(contenido_imagen) > 1:
                        contenido_para_analisis.extend(contenido_imagen[1:])
                        archivos_procesados.append(f"✅ Imagen procesada: {nombre_archivo}")
                except Exception as img_e:
                    errores_procesamiento.append(f"Error procesando imagen {nombre_archivo}: {str(img_e)}")
                    print(f"❌ Error procesando imagen {nombre_archivo}: {str(img_e)}")
            
            # Manejo para AUDIO - transcribir localmente
            elif tipo_mime.startswith('audio/'):
                print(f"🎵 Procesando audio: {nombre_archivo}")
                try:
                    texto_transcrito = transcribir_audio_local(ruta_archivo)
                    if texto_transcrito:
                        texto_transcrito_audio += f"\n\n--- TRANSCRIPCIÓN DE AUDIO: {nombre_archivo} ---\n{texto_transcrito}"
                        archivos_procesados.append(f"✅ Audio transcrito: {nombre_archivo}")
                    else:
                        errores_procesamiento.append(f"No se pudo transcribir el audio: {nombre_archivo}")
                except Exception as e:
                    errores_procesamiento.append(f"Error transcribiendo {nombre_archivo}: {str(e)}")
            
            # Manejo para VIDEO - extraer audio y transcribir
            elif tipo_mime.startswith('video/'):
                print(f"🎬 Procesando video: {nombre_archivo}")
                try:
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
        
        # Añadir transcripciones de audio/video si existen
        if texto_transcrito_audio:
            contenido_para_analisis.append({"type": "text", "text": texto_transcrito_audio})
        
        # Si no hay contenido válido después del procesamiento
        if len(contenido_para_analisis) == 1 and (errores_procesamiento or not archivos_procesados):
            print("⚠️ No se pudo procesar ningún archivo válido")
            return {
                "error": "sin_contenido_valido",
                "archivos_procesados": archivos_procesados,
                "errores": errores_procesamiento,
                "mensaje": "No se pudo procesar ningún archivo válido. Por favor, suba archivos PDF, JPG, PNG o describa su caso por escrito.",
                "resultado_triaje": {
                    "admisible": False,
                    "justificacion": "Error en el procesamiento de archivos. Por favor, verifique los formatos de los archivos subidos.",
                    "hechos_clave": "No se pudieron extraer hechos debido a errores de procesamiento",
                    "informacion_suficiente": True
                }
            }
        
        # Invocar a Gemini con el contenido preparado
        print(f"✨ Invocando Gemini con {len(contenido_para_analisis)} elementos para análisis")
        mensaje = HumanMessage(content=contenido_para_analisis)
        respuesta = llm_multimodal.invoke([mensaje])
        texto_respuesta = respuesta.content.strip()
        
        # Limpiar y parsear la respuesta JSON
        if texto_respuesta.startswith("```json"):
            texto_respuesta = texto_respuesta[7:-3].strip()
        
        try:
            resultado = json.loads(texto_respuesta)
            # Asegurar que haya un resultado_triaje válido
            if "resultado_triaje" not in resultado:
                resultado["resultado_triaje"] = {
                    "admisible": False,
                    "justificacion": "Respuesta no estructurada correctamente desde IA",
                    "hechos_clave": "Error en el formato de respuesta",
                    "informacion_suficiente": True
                }
            
            # Añadir información de procesamiento
            if archivos_procesados or errores_procesamiento:
                resultado["metadatos_procesamiento"] = {
                    "archivos_procesados": archivos_procesados,
                    "errores": errores_procesamiento
                }
            
            return resultado
        except json.JSONDecodeError as json_e:
            error_msg = f"Error parsing JSON: {str(json_e)}"
            print(f"❌ {error_msg}")
            return {
                "error": "respuesta_invalida",
                "mensaje": "Gemini no devolvió una respuesta en formato JSON válido",
                "detalle": str(json_e),
                "respuesta_original": texto_respuesta[:200] + "..." if len(texto_respuesta) > 200 else texto_respuesta,
                "archivos_procesados": archivos_procesados,
                "errores": errores_procesamiento,
                "resultado_triaje": {
                    "admisible": False,
                    "justificacion": "Error en el formato de respuesta del sistema de IA. Por favor, contacte al administrador.",
                    "hechos_clave": "Respuesta no válida del sistema de IA",
                    "informacion_suficiente": True
                }
            }
    
    except Exception as e:
        error_msg = f"Error crítico durante el análisis multimodal: {str(e)}"
        print(f"❌ {error_msg}")
        # Siempre devolver un resultado con resultado_triaje para evitar errores en LangGraph
        return {
            "error": "error_critico",
            "mensaje": "Error interno al procesar los archivos. Por favor, intente nuevamente o describa su caso por escrito.",
            "detalle": str(e),
            "resultado_triaje": {
                "admisible": False,
                "justificacion": "Error en el formato de respuesta del sistema de IA. Por favor, contacte al administrador.",
                "hechos_clave": "Error técnico durante el procesamiento",
                "informacion_suficiente": True
            }
        }

# Funciones auxiliares para transcripción (mantener las existentes)
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
    """Toma un prompt de texto y devuelve la respuesta del LLM como un string de texto plano."""
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