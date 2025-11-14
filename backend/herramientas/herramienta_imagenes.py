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
            
            # Si el tamaño de la imagen comprimida es menor que el original, usamos la comprimida
            # (Esta logica es una simplificacion, para el caso real, siempre la usaremos)
            # En un futuro, se puede comparar tamaños para ser mas eficiente.
            
            # Devolvemos la ruta original, pero la idea es que la proxima funcion
            # lea los bytes del buffer en lugar del archivo original.
            # Por simplicidad ahora, vamos a sobrescribir el archivo con su version comprimida
            
            ruta_comprimida = f"{ruta_archivo.split('.')[0]}_comprimido.jpg"
            with open(ruta_comprimida, "wb") as f:
                f.write(buffer_en_memoria.getvalue())

            print(f"--- [COMPRESOR] Imagen {ruta_archivo} comprimida y guardada en {ruta_comprimida}")
            return ruta_comprimida

    except Exception as e:
        print(f"--- [COMPRESOR] ADVERTENCIA: No se pudo comprimir la imagen {ruta_archivo}. Error: {e}. Se usara el original.")
        return ruta_archivo