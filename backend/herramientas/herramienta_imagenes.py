# backend/herramientas/herramienta_imagenes.py
from PIL import Image
import io

def comprimir_imagen_si_es_necesario(ruta_archivo: str, max_size_kb: int = 512, calidad: int = 85) -> str:
    """
    Comprime una imagen para reducir su tamaño en bytes, lo que disminuye drasticamente
    los tokens generados en la conversion a base64.
    """
    try:
        # Abre la imagen desde la ruta del archivo
        with Image.open(ruta_archivo) as img:
            # Convierte la imagen a RGB si es necesario (ej. para formatos como PNG con transparencia)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Crea un buffer en memoria para guardar la imagen comprimida
            buffer_en_memoria = io.BytesIO()
            img.save(buffer_en_memoria, format='JPEG', quality=calidad, optimize=True)
            
            # Sobreescribe el archivo original con su version comprimida
            with open(ruta_archivo, "wb") as f:
                f.write(buffer_en_memoria.getvalue())

            print(f"--- [COMPRESOR] Imagen {ruta_archivo} comprimida exitosamente")
            return ruta_archivo

    except Exception as e:
        print(f"--- [COMPRESOR] ADVERTENCIA: No se pudo comprimir la imagen {ruta_archivo}. Error: {e}. Se usará el original.")
        return ruta_archivo