# backend/herramientas/herramienta_documentos.py
import os
from docx import Document
from typing import Dict
from datetime import datetime

# --- INICIO DE LA MODIFICACION: Ruta de plantillas robusta ---
# Construimos una ruta absoluta al directorio de plantillas para evitar errores.
RUTA_BASE_PLANTILLAS = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 
    '..', 
    'datos', 
    'plantillas_documentos'
))
# --- FIN DE LA MODIFICACION ---

RUTA_SALIDA_DOCUMENTOS = os.path.join(
    os.path.dirname(__file__),
    '..',
    'archivos_subidos'
)

def generar_documento_desde_plantilla(
    nombre_plantilla: str, 
    datos_reemplazo: Dict[str, str], 
    id_caso: str
) -> str:
    try:
        ruta_plantilla = os.path.join(RUTA_BASE_PLANTILLAS, nombre_plantilla)
        print(f"DEBUG (DOCGEN): Intentando abrir plantilla en: {ruta_plantilla}")
        if not os.path.exists(ruta_plantilla):
            return f"Error: La plantilla '{nombre_plantilla}' no fue encontrada en la ruta esperada."

        documento = Document(ruta_plantilla)
        
        datos_reemplazo['{{FECHA_ACTUAL}}'] = datetime.now().strftime("%d de %B de %Y")
        datos_reemplazo['{{ID_CASO}}'] = id_caso

        for parrafo in documento.paragraphs:
            for clave, valor in datos_reemplazo.items():
                if clave in parrafo.text:
                    texto_inline = parrafo.runs
                    for i in range(len(texto_inline)):
                        if clave in texto_inline[i].text:
                            texto_inline[i].text = texto_inline[i].text.replace(clave, valor)

        ruta_carpeta_caso = os.path.join(RUTA_SALIDA_DOCUMENTOS, id_caso)
        os.makedirs(ruta_carpeta_caso, exist_ok=True)
        
        nombre_archivo_salida = f"generado_{nombre_plantilla.replace('.docx', '')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx"
        ruta_salida = os.path.join(ruta_carpeta_caso, nombre_archivo_salida)
        
        documento.save(ruta_salida)
        
        print(f"SUCCESS (DOCGEN): Documento generado y guardado en: {ruta_salida}")
        return ruta_salida

    except Exception as e:
        error_msg = f"Error crítico durante la generación del documento: {e}"
        print(f"ERROR (DOCGEN): {error_msg}")
        return error_msg