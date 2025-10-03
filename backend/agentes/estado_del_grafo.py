# backend/agentes/estado_del_grafo.py

from typing import TypedDict, List, Dict, Any, Optional

class EstadoDelGrafo(TypedDict):
    """
    Define la estructura de datos que se comparte y modifica entre los agentes del grafo.

    Actúa como el "expediente digital" del caso a medida que avanza por el sistema.
    Cada agente lee de este estado y escribe sus resultados en él.
    """

    # --- DATOS DE ENTRADA (Del Agente de Atención al Usuario) ---
    historial_conversacion: str
    """La transcripción completa de la conversación inicial con el usuario."""

    rutas_archivos_evidencia: List[str]
    """Una lista de rutas a los archivos de evidencia subidos por el usuario."""

    # --- RESULTADOS DEL AGENTE DE TRIAJE ---
    datos_triaje: Optional[Dict[str, Any]]
    """
    Un diccionario estructurado con los datos extraídos por el Agente de Triaje.
    Ejemplo: {'materia': 'Laboral', 'cuantia_estimada': 5000000, 'estrato': 2}
    """

    es_admisible: Optional[bool]
    """El veredicto final del Agente de Triaje (True si es admisible, False si no)."""

    justificacion_triaje: Optional[str]
    """La explicación del porqué un caso es o no es admisible."""

    # --- RESULTADOS DEL AGENTE DETERMINADOR DE COMPETENCIAS ---
    area_competencia: Optional[str]
    """El área del derecho a la que pertenece el caso (Ej: 'Derecho Privado', 'Derecho Público')."""

    # --- RESULTADOS DEL AGENTE REPARTIDOR ---
    id_estudiante_asignado: Optional[int]
    """El ID del estudiante al que se le ha asignado el caso."""
    
    id_asesor_asignado: Optional[int]
    """El ID del asesor/supervisor asignado al caso."""

    # --- DATOS DE APOYO (Para Agentes Auxiliares) ---
    consulta_juridica_actual: Optional[str]
    """La pregunta específica que un estudiante hace al Agente Jurídico."""
    
    tipo_documento_solicitado: Optional[str]
    """El tipo de documento que un estudiante solicita al Agente Generador de Documentos."""