import base64
import mimetypes
from pathlib import Path
from typing import List, Dict, Any

def _leer_archivo_como_base64(ruta_archivo: str) -> str:
    """
    Abre un archivo, lee sus bytes y lo codifica en base64.
    Esta es la forma en que los modelos de IA "ven" los archivos.
    """
    try:
        # Usamos Path para manejar las rutas de forma robusta
        path = Path(ruta_archivo)
        with open(path, "rb") as f:
            # Leemos los bytes del archivo
            bytes_del_archivo = f.read()
            # Codificamos esos bytes en una cadena de texto base64
            return base64.b64encode(bytes_del_archivo).decode("utf-8")
    except Exception as e:
        print(f"      ERROR-IO: No se pudo leer el archivo {ruta_archivo}: {e}")
        return "" # Devolvemos una cadena vacía si hay un error

def preparar_entrada_multimodal(prompt_texto: str, rutas_archivos: List[str]) -> List[Dict[str, Any]]:
    """
    Docstring:
    Esta es la función CRÍTICA del sistema multimodal.
    Toma el prompt de texto y una lista de rutas de archivos, y los convierte
    en el formato exacto que LangChain/Gemini necesita para el análisis multimodal.

    CORRECCIÓN DEFINITIVA: Ahora SÍ lee los archivos del disco y los codifica en base64.
    """
    # El contenido siempre empieza con el prompt de texto del usuario.
    contenido_final = [{"type": "text", "text": prompt_texto}]

    for ruta in rutas_archivos:
        # Obtenemos el tipo MIME del archivo (ej. 'image/png', 'application/pdf')
        tipo_mime, _ = mimetypes.guess_type(ruta)
        
        # Leemos el archivo y lo convertimos a base64
        datos_base64 = _leer_archivo_como_base64(ruta)

        if not tipo_mime or not datos_base64:
            # Si no podemos determinar el tipo o leer el archivo, lo omitimos.
            print(f"      ALERTA-MULTIMODAL: Omitiendo archivo {ruta} (tipo o contenido inválido).")
            continue

        # Añadimos el archivo al contenido en el formato que Gemini espera.
        # La "fuente" (source) contiene el tipo de archivo y los datos codificados.
        contenido_final.append(
            {
                "type": "image_url", # Langchain usa "image_url" genéricamente para datos binarios
                "image_url": {
                    "mime_type": tipo_mime,
                    "data": datos_base64,
                },
            }
        )

    return contenido_final