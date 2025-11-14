#C:\react\asistente_legal_multimodal\backend\herramientas\herramienta_multimodal_gemini.py
import base64
import mimetypes
from typing import List, Dict, Any

def preparar_entrada_multimodal(prompt_texto: str, rutas_archivos: List[str]) -> List[Dict[str, Any]]:
    """
    Prepara una lista de contenidos en el formato multimodal correcto,
    compatible con la versión actual de LangChain para los modelos Gemini 1.5.
    """
    # El contenido siempre comienza con la parte de texto.
    contenido_multimodal = [{"type": "text", "text": prompt_texto}]

    for ruta in rutas_archivos:
        try:
            tipo_mime, _ = mimetypes.guess_type(ruta)
            if tipo_mime is None:
                print(f"Advertencia: No se pudo determinar el tipo MIME para {ruta}. Se omitirá.")
                continue

            with open(ruta, "rb") as f:
                datos_archivo = f.read()

            datos_codificados = base64.b64encode(datos_archivo).decode('utf-8')

            # --- INICIO DE LA CORRECCIÓN CLAVE ---
            # La versión actual de la librería LangChain para Gemini 1.5
            # espera un diccionario que contenga directamente 'mime_type' y 'data'
            # para los archivos, sin el campo "type": "media".
            parte_archivo = {
                "mime_type": tipo_mime,
                "data": datos_codificados
            }
            # --- FIN DE LA CORRECCIÓN CLAVE ---
            
            contenido_multimodal.append(parte_archivo)

        except FileNotFoundError:
            print(f"Error: El archivo en la ruta {ruta} no fue encontrado.")
        except Exception as e:
            print(f"Error procesando el archivo {ruta}: {e}")

    return contenido_multimodal