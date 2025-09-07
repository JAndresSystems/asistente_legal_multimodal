# backend/herramientas/herramientas_audio.py

import os
from pathlib import Path
from dotenv import load_dotenv
import torch
import librosa
from transformers import AutoProcessor, AutoModelForCTC

# --- CONFIGURACIÓN ---
load_dotenv()

# El identificador del modelo de Facebook AI. Es público y no necesita token.
MODEL_ID = "facebook/wav2vec2-base-960h"

# --- CARGA DEL MODELO (PUEDE TARDAR UN POCO LA PRIMERA VEZ) ---
try:
    print(f"TOOL-SETUP: Cargando el procesador de audio desde '{MODEL_ID}'...")
    procesador = AutoProcessor.from_pretrained(MODEL_ID)
    
    print(f"TOOL-SETUP: Cargando el modelo de audio '{MODEL_ID}' en memoria...")
    # AutoModelForCTC es la clase correcta para este tipo de modelo.
    modelo_asr = AutoModelForCTC.from_pretrained(MODEL_ID)
    
    print(f"TOOL-SETUP: Modelo de audio cargado correctamente.")
    
except Exception as e:
    print(f"TOOL-SETUP-ERROR: No se pudo cargar el modelo de audio. Causa: {e}")
    procesador = None
    modelo_asr = None

def procesar_audio(ruta_archivo: str) -> str:
    """
    Procesa un archivo de audio transcribiéndolo con el modelo Wav2Vec2 local.
    """
    print(f"      TOOL-SYSTEM: -> Iniciando procesamiento de audio local con '{MODEL_ID}' para {ruta_archivo}")
    
    if not modelo_asr or not procesador:
        return "Error: El modelo de audio no está cargado. Revisa los logs de inicio."
        
    try:
        # 1. Cargar el audio y asegurarse de que esté en el formato correcto (16kHz mono)
        # Esto es crucial para que el modelo funcione bien.
        audio_array, _ = librosa.load(ruta_archivo, sr=16000, mono=True)
        
        print(f"      TOOL-SYSTEM: -> Audio cargado y re-muestreado a 16kHz.")
        
        # 2. Preparar el audio para el modelo
        inputs = procesador(audio_array, sampling_rate=16000, return_tensors="pt")
        
        # 3. Realizar la inferencia (la transcripción)
        with torch.no_grad():
            logits = modelo_asr(**inputs).logits

        # 4. Decodificar la salida para obtener el texto
        ids_predichos = torch.argmax(logits, dim=-1)
        transcripcion = procesador.batch_decode(ids_predichos)[0]
        
        print("      TOOL-SYSTEM: -> Transcripción completada.")
        return transcripcion.upper() # El modelo fue entrenado en mayúsculas.
        
    except Exception as e:
        if "ffmpeg" in str(e).lower() or "WinError 2" in str(e):
            return "Error: FFMPEG no está instalado. Instala FFMPEG para procesar audio."
        print(f"      ERROR-CRITICO: Fallo durante el procesamiento de audio con Wav2Vec2: {e}")
        return f"Error crítico durante el procesamiento de audio: {e}"