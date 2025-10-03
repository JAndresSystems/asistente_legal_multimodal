import base64
import mimetypes
from typing import List, Dict, Any

def preparar_entrada_multimodal(prompt_texto: str, rutas_archivos: List[str]) -> List[Dict[str, Any]]:
    """
    Prepara una lista de contenidos en el formato multimodal correcto y definitivo,
    compatible con LangChain para el envío directo de cualquier tipo de archivo a Gemini.
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

            # --- LA SOLUCIÓN BASADA EN LA EVIDENCIA DE SUS IMÁGENES ---
            # La librería LangChain espera un diccionario con el tipo "media"
            # para archivos genéricos como PDF, audio, video, etc.
            parte_archivo = {
                "type": "media",
                "mime_type": tipo_mime,
                "data": datos_codificados
            }
            
            contenido_multimodal.append(parte_archivo)

        except FileNotFoundError:
            print(f"Error: El archivo en la ruta {ruta} no fue encontrado.")
        except Exception as e:
            print(f"Error procesando el archivo {ruta}: {e}")

    return contenido_multimodal