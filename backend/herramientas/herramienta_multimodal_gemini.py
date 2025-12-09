# backend/herramientas/herramienta_multimodal_gemini.py
import os
import time  # <--- NECESARIO PARA LA ESPERA
import mimetypes
from pathlib import Path
from typing import List, Any, Dict
import google.generativeai as genai

# Configuración global (se hace una sola vez)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Definimos un umbral de tamaño (en bytes) para decidir entre inline_data y Files API
TAMANO_UMBRAL_INLINE = 2 * 1024 * 1024  # 2 MB

def _esperar_archivo_activo(archivo_subido):
    """
    Función auxiliar crítica: Espera a que Google termine de procesar el archivo.
    Sin esto, los videos o audios largos darán error 400 'Not ACTIVE'.
    """
    print(f"      [GOOGLE] Esperando a que el archivo {archivo_subido.name} esté activo...")
    archivo = genai.get_file(archivo_subido.name)
    
    # Bucle de espera (Polling)
    while archivo.state.name == "PROCESSING":
        time.sleep(2) # Esperamos 2 segundos antes de volver a preguntar
        archivo = genai.get_file(archivo_subido.name)
        print(".", end="", flush=True) # Indicador visual de espera

    if archivo.state.name != "ACTIVE":
        raise Exception(f"El archivo falló al procesarse en Google. Estado: {archivo.state.name}")
    
    print(f"\n      [GOOGLE] Archivo {archivo_subido.name} listo (ACTIVE).")
    return archivo

def _subir_o_inline(ruta_archivo: str) -> Dict[str, Any]:
    """
    Decide si subir el archivo con Files API o usar inline_data.
    Devuelve un dict compatible con generate_content().
    """
    path = Path(ruta_archivo)
    mime_type, _ = mimetypes.guess_type(ruta_archivo)
    
    if not mime_type:
        print(f"      ALERTA: MIME no detectado para {ruta_archivo}. Omitiendo.")
        return None

    tamano_archivo = path.stat().st_size

    # Criterio: archivos grandes (>TAMANO_UMBRAL_INLINE) o audio/video grandes → Files API
    es_grande = tamano_archivo > TAMANO_UMBRAL_INLINE

    if es_grande:
        try:
            print(f"      SUBIENDO con Files API: {path.name} ({mime_type}, {tamano_archivo} bytes)")
            uploaded = genai.upload_file(path=path, mime_type=mime_type)
            
            # --- CORRECCIÓN CRÍTICA AQUÍ ---
            # Esperamos a que el estado sea ACTIVE antes de devolverlo
            _esperar_archivo_activo(uploaded)
            # -------------------------------

            return {"file_data": {"file_uri": uploaded.uri, "mime_type": mime_type}}
        except Exception as e:
            print(f"      ERROR al subir archivo con Files API: {e}")
            return None
    else:
        # Si no es grande, usar inline_data (para imágenes, PDFs pequeños, audios cortos)
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