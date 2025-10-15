# backend/agentes/nodos_del_grafo.py

from sqlmodel import Session, select, func
from typing import Dict, Any, Optional

from .estado_del_grafo import EstadoDelGrafo
from ..herramientas.herramientas_lenguaje import analizar_evidencia_con_gemini, generar_respuesta_texto
from ..herramientas.herramienta_rag import buscar_en_base_de_conocimiento
from ..base_de_datos import motor # Eliminamos importaciones no usadas
from ..api.modelos_compartidos import Estudiante, Asesor, Asignacion # Eliminamos importaciones no usadas

def nodo_agente_triaje(estado: EstadoDelGrafo) -> Dict[str, Any]:
    """
    Docstring:
    Este nodo actua como el primer filtro de admisibilidad formal, solicitando
    informacion de forma gradual si es necesario.
    """
    print("\n--- [AGENTE TRIAJE] Iniciando ejecucion del nodo ---")
    rutas_archivos = estado["rutas_archivos_evidencia"]
    print(f"--- [AGENTE TRIAJE] Analizando evidencias: {rutas_archivos}")
    texto_adicional = estado.get("texto_adicional_usuario", "")
    print(f"--- [AGENTE TRIAJE] Analizando {len(rutas_archivos)} archivos y texto adicional: '{texto_adicional[:50]}...'")

    try:
        # Hacemos una consulta amplia para obtener todo el contexto de una vez.
        consulta_contexto = "Cuales son las competencias y beneficiarios de los consultorios juridicos y cuales son las evidencias esenciales por tipo de caso?"
        lista_contexto = buscar_en_base_de_conocimiento(
            consulta=consulta_contexto,
            area_competencia="admisibilidad"
        )
        # La variable se llama 'contexto_completo'
        contexto_completo = "\n\n---\n\n".join(lista_contexto)
        print(f"--- [AGENTE TRIAJE] Contexto legal y documental recuperado de RAG.")
    except Exception as e:
        print(f"--- [AGENTE TRIAJE] ERROR: Fallo al buscar en RAG 'admisibilidad': {e}")
        contexto_completo = "Error: No se pudo recuperar la guia de documentos."

    prompt_completo = f"""
    ERES un abogado de triaje... Tu respuesta DEBE ser unicamente un objeto JSON.

    --- CONTEXTO LEGAL Y GUIA DOCUMENTAL ---
    {contexto_completo}
    --- FIN DEL CONTEXTO ---

    --- EVIDENCIA A ANALIZAR ---
    1.  Archivos Adjuntos: {len(rutas_archivos)} archivo(s) proporcionado(s).
    2.  Texto Adicional del Usuario: "{texto_adicional}"
    --- FIN DE LA EVIDENCIA ---

    REGLAS DE DECISION:
    1.  EVALUA ADMISIBILIDAD: Determina si el caso es admisible segun la Ley 2113.
    2.  VERIFICA SUFICIENCIA: Revisa si tienes los documentos esenciales para el tipo de caso, segun la "GUIA DE EVIDENCIAS ESENCIALES".

    REGLAS DE SOLICITUD (MUY IMPORTANTE):
    1.  PRIORIDAD MAXIMA: Si el documento de identidad (cedula) no esta presente entre las evidencias, PIDE UNICAMENTE LA CEDULA. Tu pregunta debe ser solo sobre eso.
    2.  SOLICITUD GRADUAL: Si la cedula ya esta, pero faltan otros documentos importantes para el tipo de caso (ej. informe de transito para un accidente), PIDE SOLO LOS 2 DOCUMENTOS MAS IMPORTANTES que falten. No pidas mas de dos a la vez. Formula una sola pregunta clara.
    3.  FINALIZACION: Si la cedula y los documentos mas importantes ya estan presentes, considera que la 'informacion_suficiente' es 'true'.

    TAREA:
    Analiza TODA la evidencia proporcionada (archivos y texto) y devuelve un objeto JSON con la siguiente estructura:
    {{
      "admisible": boolean,
      "justificacion": "string (Explica tu decision de admisibilidad)",
      "hechos_clave": "string (Resumen de los hechos)",
      "informacion_suficiente": boolean,
      "pregunta_para_usuario": "string (Si 'informacion_suficiente' es false, formula una pregunta siguiendo las 'REGLAS DE SOLICITUD'. Si es true, deja este campo vacio '')"
    }}
    """
    
    print("--- [AGENTE TRIAJE] Invocando LLM para analisis de admisibilidad...")
    resultado_analisis = analizar_evidencia_con_gemini(
        archivos_locales=rutas_archivos,
        prompt_usuario=prompt_completo
    )
    print(f"--- [AGENTE TRIAJE] Analisis completado. Resultado: {resultado_analisis}")
    return {"resultado_triaje": resultado_analisis}


# ==============================================================================
# INICIO DE LA MODIFICACION: Nuevo nodo para solicitar mas informacion
# ==============================================================================
def nodo_solicitar_informacion_adicional(estado: EstadoDelGrafo) -> Dict[str, Any]:
    """
    Docstring:
    Este nodo se activa cuando el Agente de Triaje determina que la
    informacion no es suficiente. Su unica funcion es tomar la pregunta
    generada por el triaje y prepararla para ser enviada de vuelta al usuario.
    """
    print("\n--- [AGENTE SOLICITUD] Iniciando ejecucion del nodo ---")
    
    pregunta_generada = estado.get("resultado_triaje", {}).get("pregunta_para_usuario", "")
    
    print(f"--- [AGENTE SOLICITUD] Se enviara la siguiente pregunta al usuario: '{pregunta_generada}'")
    
    # En un futuro, este nodo podria añadir la pregunta a una lista de mensajes
    # para que el frontend la muestre en la interfaz de chat.
    # Por ahora, simplemente actualizamos el estado.
    return {"respuesta_para_usuario": pregunta_generada}
# ==============================================================================
# FIN DE LA MODIFICACION
# ==============================================================================

def nodo_agente_analizador_pdf(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente Analizador de PDFs ---")
    rutas_archivos = estado["rutas_archivos_evidencia"]
    prompt_completo = """
    ERES una API de extraccion de datos. Tu unica funcion es devolver un JSON.
    JSON: {"tipo_documento_identificado": "string", "partes_involucradas": ["string"], "fechas_clave": ["string"], "resumen_del_objeto": "string", "puntos_relevantes": ["string"]}
    Analiza el documento y responde.
    """
    resultado_extraccion = analizar_evidencia_con_gemini(
        archivos_locales=rutas_archivos,
        prompt_usuario=prompt_completo
    )
    return {"resultado_analisis_documento": resultado_extraccion}

def nodo_agente_analizador_audio(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente Analizador de Audio ---")
    rutas_archivos = estado["rutas_archivos_evidencia"]
    prompt_completo = """
    ERES una API de transcripcion. Tu unica funcion es devolver un JSON.
    JSON: {"transcripcion_completa": "string", "resumen_puntos_clave": "string"}
    Escucha, transcribe y resume la grabacion.
    """
    resultado_analisis = analizar_evidencia_con_gemini(
        archivos_locales=rutas_archivos,
        prompt_usuario=prompt_completo
    )
    return {"resultado_analisis_audio": resultado_analisis}

def nodo_agente_determinador_competencias(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente Determinador de Competencias ---")
    hechos_clave_triaje = estado.get("resultado_triaje", {}).get("hechos_clave", "")
    contexto_para_analisis = f"Hechos del caso: {hechos_clave_triaje}"
    
    prompt_completo = f"""
    Clasifica el caso. Responde solo con JSON. No incluyas texto antes o despues del JSON.
    JSON: {{"area_competencia": "string", "justificacion_breve": "string"}}
    AREAS VALIDAS: "Derecho Privado", "Derecho Publico", "Derecho Laboral", "Derecho de Familia", "No Clasificable".
    CASO: {contexto_para_analisis}
    """
    resultado_clasificacion = analizar_evidencia_con_gemini(
        archivos_locales=[], prompt_usuario=prompt_completo
    )
    return {"resultado_determinador_competencias": resultado_clasificacion}

def encontrar_persona_con_menos_carga(sesion: Session, modelo: Any, area: str) -> Optional[int]:
    declaracion = (
        select(modelo.id, func.count(Asignacion.id_caso).label("carga_trabajo"))
        .join(Asignacion, modelo.id == getattr(Asignacion, f"id_{modelo.__name__.lower()}"), isouter=True)
        .where(modelo.area_especialidad == area)
        .group_by(modelo.id).order_by(func.count(Asignacion.id_caso).asc())
    )
    resultado = sesion.exec(declaracion).first()
    return resultado.id if resultado else None

def nodo_agente_repartidor(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente Repartidor ---")
    id_caso = estado["id_caso"]
    resultado_competencias = estado.get("resultado_determinador_competencias", {})
    area_competencia = resultado_competencias.get("area_competencia")
    
    if not area_competencia or area_competencia in ["No Clasificable"]:
        return {"resultado_repartidor": {"detalle": "No se pudo asignar. Area de competencia no valida.", "operacion_db": "omitida"}}

    with Session(motor) as sesion_db:
        id_estudiante = encontrar_persona_con_menos_carga(sesion_db, Estudiante, area_competencia)
        id_asesor = encontrar_persona_con_menos_carga(sesion_db, Asesor, area_competencia)
        
        if id_estudiante is not None and id_asesor is not None:
            nueva_asignacion = Asignacion(
                id_caso=id_caso,
                id_estudiante=id_estudiante,
                id_asesor=id_asesor
            )
            sesion_db.add(nueva_asignacion)
            sesion_db.commit()
            mensaje_db = "Asignacion creada exitosamente en la base de datos."
            print(f"-> EXITO (DB): Caso {id_caso} asignado a Estudiante {id_estudiante} y Asesor {id_asesor}.")
        else:
            mensaje_db = "No se encontraron estudiantes o asesores disponibles en el area."
            print(f"-> ALERTA (DB): No se pudo realizar la asignacion para el caso {id_caso}.")

    resultado = {
        "id_estudiante_asignado": id_estudiante, 
        "id_asesor_asignado": id_asesor,
        "operacion_db": mensaje_db
    }
    return {"resultado_repartidor": resultado}

def nodo_agente_juridico(estado: EstadoDelGrafo) -> Dict[str, Any]:
    return {"resultado_agente_juridico": "Ejecucion omitida en este flujo."}

def nodo_agente_generador_documentos(estado: EstadoDelGrafo) -> Dict[str, Any]:
    return {"resultado_agente_generador_documentos": "Ejecucion omitida en este flujo."}