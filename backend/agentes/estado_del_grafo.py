# backend/agentes/estado_del_grafo.py

from typing import TypedDict, List, Dict, Any, Optional

class EstadoDelGrafo(TypedDict):
    """
    Define la estructura de datos que se comparte y modifica entre los agentes.

    Este es el "expediente digital" del caso. Actua como un contrato que
    todos los agentes deben seguir. Cada agente tiene sus propios "cajones"
    (atributos) para leer la informacion que necesita y escribir sus resultados.
    El uso de 'Optional' indica que muchos de estos campos estaran vacios al
    inicio y se iran llenando a medida que el caso avanza por el grafo.
    """

    # --- DATOS DE ENTRADA PRINCIPALES ---
    # Informacion con la que se inicia el proceso del grafo.
    id_caso: int
    """
    El identificador unico del caso en la base de datos PostgreSQL.
    Es el dato mas importante para garantizar la persistencia.
    """

    rutas_archivos_evidencia: List[str]
    """
    Una lista que contiene las rutas locales donde se guardaron los
    archivos de evidencia (PDF, imagenes, audios) subidos por el usuario.
    """

    # --- RESULTADOS DEL AGENTE DE TRIAJE ---
    # Campos que son escritos exclusivamente por el 'nodo_agente_triaje'.
    resultado_triaje: Optional[Dict[str, Any]]
    """
    El diccionario JSON completo devuelto por el modelo de IA tras el triaje.
    Contiene la decision de admisibilidad y los datos extraidos.
    Ejemplo: {'admisible': True, 'justificacion': '...', 'datos_extraidos': {...}}
    """

    # --- RESULTADOS DEL AGENTE DETERMINADOR DE COMPETENCIAS ---
    # Campo escrito exclusivamente por el 'nodo_agente_determinador_competencias'.
    resultado_determinador_competencias: Optional[Dict[str, Any]]
    """
    El diccionario JSON devuelto por el modelo de IA que clasifica el area.
    Ejemplo: {'area_competencia': 'Derecho Privado', 'sub_area': 'Contratos'}
    """

    # --- RESULTADOS DEL AGENTE REPARTIDOR ---
    # Campos escritos exclusivamente por el 'nodo_agente_repartidor'.
    resultado_repartidor: Optional[Dict[str, Any]]
    """
    Diccionario con los IDs del personal asignado tras consultar la base de datos.
    Ejemplo: {'id_estudiante_asignado': 12, 'id_asesor_asignado': 4}
    """

    # --- ENTRADAS PARA AGENTES AUXILIARES (SIMULADAS POR AHORA) ---
    # Informacion que simula una peticion de un estudiante a los agentes de apoyo.
    solicitud_agente_juridico: Optional[str]
    """
    La pregunta especifica que se le hara al Agente Juridico.
    Ejemplo: 'Cuales son las causales de divorcio en Colombia?'
    """

    solicitud_agente_documentos: Optional[Dict[str, str]]
    """
    La peticion especifica para el Agente Generador de Documentos.
    Ejemplo: {'tipo_documento': 'derecho_de_peticion', 'destinatario': 'EPS SaludTotal'}
    """

    # --- RESULTADOS DE AGENTES AUXILIARES ---
    # Campos escritos por los agentes de apoyo al final del flujo.
    resultado_agente_juridico: Optional[str]
    """
    La respuesta en texto plano generada por el Agente Juridico.
    """

    resultado_agente_generador_documentos: Optional[str]
    """
    La ruta al archivo .docx final generado por el Agente de Documentos.
    """