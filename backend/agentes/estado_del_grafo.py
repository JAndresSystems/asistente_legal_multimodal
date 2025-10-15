# backend/agentes/estado_del_grafo.py

from typing import TypedDict, List, Dict, Any, Optional

class EstadoDelGrafo(TypedDict):
    """
    Define la estructura de datos que se comparte y modifica entre los agentes.
    Esta version esta expandida para soportar los resultados de analisis
    multimodales especializados.
    """

    # --- DATOS DE ENTRADA PRINCIPALES ---
    id_caso: int
    rutas_archivos_evidencia: List[str]

    texto_adicional_usuario: Optional[str]

    # --- RESULTADOS DE LA CADENA DE PROCESAMIENTO ---
    resultado_triaje: Optional[Dict[str, Any]]
    
    # --- ¡NUEVOS CAMPOS PARA ANALISIS MULTIMODAL! ---
    # Estos campos almacenaran los resultados de los agentes especializados.
    # Los inicializamos como opcionales porque solo uno de ellos se llenara
    # por cada ejecucion del grafo, dependiendo del tipo de evidencia.
    
    resultado_analisis_documento: Optional[Dict[str, Any]]
    """
    Contendra el JSON con la extraccion semantica de un documento PDF.
    Ejemplo: {'partes': ['Juan Perez', 'Inmobiliaria SAS'], 'fecha_clave': '2023-10-05', ...}
    """
    
    resultado_analisis_audio: Optional[Dict[str, Any]]
    """
    Contendra la transcripcion y el resumen de un archivo de audio.
    Ejemplo: {'transcripcion': '...', 'resumen_puntos_clave': '...'}
    """

    # --- RESULTADOS DE AGENTES POSTERIORES (Se mantienen) ---
    resultado_determinador_competencias: Optional[Dict[str, Any]]
    resultado_repartidor: Optional[Dict[str, Any]]
    
    # --- ENTRADAS Y RESULTADOS DE AGENTES AUXILIARES (Se mantienen) ---
    solicitud_agente_juridico: Optional[str]
    solicitud_agente_documentos: Optional[Dict[str, str]]
    resultado_agente_juridico: Optional[str]
    resultado_agente_generador_documentos: Optional[str]