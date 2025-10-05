import os
from docx import Document
from typing import Dict
from datetime import datetime

# Definimos la ruta base donde se encuentran nuestras plantillas.
RUTA_BASE_PLANTILLAS = os.path.join(
    os.path.dirname(__file__), 
    '..', 
    'datos', 
    'plantillas_documentos'
)

# Definimos la ruta donde se guardarán los documentos generados.
RUTA_SALIDA_DOCUMENTOS = os.path.join(
    os.path.dirname(__file__),
    '..',
    'archivos_subidos' # Guardaremos los documentos generados junto a la evidencia.
)


def generar_documento_desde_plantilla(
    nombre_plantilla: str, 
    datos_reemplazo: Dict[str, str], 
    id_caso: str
) -> str:
    """
    Genera un documento .docx a partir de una plantilla y un diccionario de datos.

    Args:
        nombre_plantilla (str): El nombre del archivo de la plantilla (ej. "derecho_de_peticion.docx").
        datos_reemplazo (Dict[str, str]): Un diccionario donde las claves son los marcadores
                                           de posición en la plantilla y los valores son el
                                           texto con el que se reemplazarán.
        id_caso (str): El ID del caso, para guardar el documento en la carpeta correcta.

    Returns:
        str: La ruta del archivo del documento generado, o un mensaje de error.
    """
    try:
        ruta_plantilla = os.path.join(RUTA_BASE_PLANTILLAS, nombre_plantilla)
        if not os.path.exists(ruta_plantilla):
            return f"Error: La plantilla '{nombre_plantilla}' no fue encontrada."

        # Abrimos el documento de la plantilla.
        documento = Document(ruta_plantilla)
        
        # Agregamos datos automáticos que pueden ser útiles.
        datos_reemplazo['{{FECHA_ACTUAL}}'] = datetime.now().strftime("%d de %B de %Y")
        datos_reemplazo['{{ID_CASO}}'] = id_caso

        # Iteramos sobre todos los párrafos del documento.
        for parrafo in documento.paragraphs:
            for clave, valor in datos_reemplazo.items():
                # Buscamos y reemplazamos cada marcador de posición.
                # La función 'replace' es simple pero efectiva para este caso de uso.
                if clave in parrafo.text:
                    # Usamos .replace() para reemplazar todas las ocurrencias.
                    texto_inline = parrafo.runs
                    # Reconstruimos el párrafo para mantener el formato.
                    for i in range(len(texto_inline)):
                        if clave in texto_inline[i].text:
                            texto_inline[i].text = texto_inline[i].text.replace(clave, valor)

        # (Opcional) Iterar sobre tablas si las plantillas las tuvieran.
        # for tabla in documento.tables:
        #     for fila in tabla.rows:
        #         for celda in fila.cells:
        #             for clave, valor in datos_reemplazo.items():
        #                 if clave in celda.text:
        #                     celda.text = celda.text.replace(clave, valor)

        # Creamos la ruta de salida y guardamos el nuevo documento.
        ruta_carpeta_caso = os.path.join(RUTA_SALIDA_DOCUMENTOS, id_caso)
        os.makedirs(ruta_carpeta_caso, exist_ok=True)
        
        nombre_archivo_salida = f"generado_{nombre_plantilla.replace('.docx', '')}_{datetime.now().strftime('%Y%m%d')}.docx"
        ruta_salida = os.path.join(ruta_carpeta_caso, nombre_archivo_salida)
        
        documento.save(ruta_salida)
        
        print(f"SUCCESS (DOCGEN): Documento generado y guardado en: {ruta_salida}")
        return ruta_salida

    except Exception as e:
        error_msg = f"Error crítico durante la generación del documento: {e}"
        print(f"ERROR (DOCGEN): {error_msg}")
        return error_msg