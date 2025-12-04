# backend/herramientas/herramienta_multimodal_gemini.py
import os
import mimetypes
from pathlib import Path
from typing import List, Any, Dict
import google.generativeai as genai

# Configuración global (se hace una sola vez)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Definimos un umbral de tamaño (en bytes) para decidir entre inline_data y Files API
# Ejemplo: 2 MB. Archivos por debajo de este tamaño se envían como inline_data si son compatibles.
# Ajusta este valor según tus necesidades y tolerancia a latencia.
TAMANO_UMBRAL_INLINE = 2 * 1024 * 1024  # 2 MB en bytes

def _subir_o_inline(ruta_archivo: str) -> Dict[str, Any]:
    """
    Decide si subir el archivo con Files API o usar inline_data.
    Devuelve un dict compatible con generate_content().
    Ahora considera el tamaño del archivo para audios/vídeos pequeños.
    """
    path = Path(ruta_archivo)
    mime_type, _ = mimetypes.guess_type(ruta_archivo)
    
    if not mime_type:
        print(f"      ALERTA: MIME no detectado para {ruta_archivo}. Omitiendo.")
        return None

    tamano_archivo = path.stat().st_size

    # Criterio: archivos grandes (>TAMANO_UMBRAL_INLINE) o audio/video grandes → Files API
    # Los audios/vídeos pequeños ahora pueden usar inline_data para mayor velocidad.
    es_grande = tamano_archivo > TAMANO_UMBRAL_INLINE
    es_audio_video = mime_type.startswith(('audio/', 'video/'))

    # OPCIÓN 1: Usar Files API para archivos grandes o cualquier audio/video (comportamiento anterior)
    # if es_grande or es_audio_video:

    # OPCIÓN 2: Usar Files API solo para archivos grandes (independientemente del tipo)
    # Esto permitiría audios/vídeos pequeños usar inline_data.
    if es_grande:
        try:
            print(f"      SUBIENDO con Files API: {path.name} ({mime_type}, {tamano_archivo} bytes)")
            uploaded = genai.upload_file(path=path, mime_type=mime_type)
            # Devuelve dict con file_data (nuevo formato)
            return {"file_data": {"file_uri": uploaded.uri, "mime_type": mime_type}}
        except Exception as e:
            print(f"      ERROR al subir archivo con Files API: {e}")
            # Si falla la subida, podrías intentar inline_data como fallback, pero
            # si era grande, es probable que inline_data también falle por tamaño.
            # Por ahora, retornamos None si falla la subida.
            return None
    else:
        # Si no es grande, usar inline_data (para imágenes, PDFs pequeños, y audios/vídeos pequeños)
        try:
            with open(path, "rb") as f:
                data = f.read()
            print(f"      ENVIANDO inline: {path.name} ({mime_type}, {tamano_archivo} bytes)")
            return {
                "inline_data": {
                    "mime_type": mime_type,
                    "data": data
                }
            }
        except Exception as e:
            print(f"      ERROR leyendo inline {ruta_archivo}: {e}")
            return None

def preparar_entrada_multimodal(prompt_texto: str, rutas_archivos: List[str]) -> List[Any]:
    """
    Prepara la lista de contenido para Gemini (nativo).
    Formato actualizado: texto + dicts inline_data/file_data.
    """
    contenido = [prompt_texto]

    for ruta in rutas_archivos:
        if not Path(ruta).exists():
            print(f"      ARCHIVO NO ENCONTRADO: {ruta}")
            continue

        parte = _subir_o_inline(ruta)
        if parte:
            contenido.append(parte)

    return contenido