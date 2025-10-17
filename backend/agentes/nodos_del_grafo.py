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
    ERES un abogado de triaje para un consultorio juridico gratuito, riguroso pero razonable. Tu mision es calificar casos y pedir la documentacion justa y necesaria. Tu respuesta DEBE ser unicamente un objeto JSON.

    --- CONTEXTO LEGAL Y GUIA DOCUMENTAL ---
    {contexto_completo}
    --- FIN DEL CONTEXTO ---

    --- EVIDENCIA A ANALIZAR ---
    1.  Archivos Adjuntos: {len(rutas_archivos)} archivo(s) proporcionado(s).
    2.  Texto Adicional del Usuario: "{texto_adicional}"
    --- FIN DE LA EVIDENCIA ---

    --- REGLA DE INTERPRETACION JURIDICA ---
    La excepción prevalece sobre la regla general. El Artículo 9 tiene un límite de 50 SMLMV, pero exceptúa los casos de "tránsito". Un caso de accidente de tránsito con reclamación de 50 SMLMV ES ADMISIBLE.

    --- ESTRATEGIA DE SALIDA ---
    Si el usuario indica explícitamente que NO tiene más documentos (ej. "no tengo mas"), DEBES detener el ciclo de preguntas. Establece "informacion_suficiente" como "true" y añade una advertencia en tu "justificacion".
    
    --- REGLA DE FLEXIBILIDAD Y BUENA FE (NUEVO Y MUY IMPORTANTE) ---
    Tu objetivo es pedir los documentos faltantes UNA SOLA VEZ. Después de que hayas hecho una pregunta pidiendo documentos (ej. pidiendo el informe de tránsito), si en la siguiente interacción el usuario sube CUALQUIER archivo (PDF, PNG, JPG), DEBES ASUMIR que ha intentado cumplir tu petición. NO vuelvas a pedir el mismo documento. Considera que con eso es suficiente para esta etapa, marca "informacion_suficiente" como "true" y permite que el caso avance.

    REGLAS DE DECISION:
    1.  EVALUA ADMISIBILIDAD: ¿El caso es admisible?
    2.  VERIFICA SUFICIENCIA: ¿Tienes los documentos esenciales? Si no, aplica las REGLAS DE SOLICITUD. Si ya pediste y el usuario subió algo, aplica la REGLA DE FLEXIBILIDAD.

    --- REGLAS DE EXCLUSION INQUEBRANTABLES ---
    1.  CASOS COMERCIALES: RECHAZA cualquier disputa comercial.
    
    REGLAS DE SOLICITUD (Aplica solo la primera vez que falten documentos):
    1.  PIDE MAXIMO 2 DOCUMENTOS: Si faltan documentos, pide solo los 2 más importantes y sé específico (ej. "informe de tránsito y epicrisis médica").

    TAREA:
    Analiza la evidencia y el texto. Devuelve un objeto JSON con la siguiente estructura:
    {{
      "admisible": boolean,
      "justificacion": "string (Explica tu decisión)",
      "hechos_clave": "string (Resumen de los hechos)",
      "informacion_suficiente": boolean,
      "pregunta_para_usuario": "string (SOLO si 'informacion_suficiente' es false. De lo contrario, déjalo vacío '')"
    }}
    """
    
    print("--- [AGENTE TRIAJE] Invocando LLM para analisis de admisibilidad...")
    resultado_analisis = analizar_evidencia_con_gemini(
        archivos_locales=rutas_archivos,
        prompt_usuario=prompt_completo
    )
    print(f"--- [AGENTE TRIAJE] Analisis completado. Resultado: {resultado_analisis}")
    return {"resultado_triaje": resultado_analisis}



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
    """
    Docstring:
    Analiza los hechos de un caso admitido y lo clasifica en una de las
    areas de practica del consultorio (Privado, Publico, Laboral, Penal).
    Utiliza RAG para consultar multiples bases de conocimiento especializadas.
    """
    print("\n--- [AGENTE COMPETENCIAS] Iniciando ejecucion del nodo ---")
    
    # 1. Obtener los hechos del caso, que es nuestra consulta principal.
    hechos_clave_triaje = estado.get("resultado_triaje", {}).get("hechos_clave", "")
    if not hechos_clave_triaje:
        print("--- [AGENTE COMPETENCIAS] ALERTA: No se encontraron hechos clave. Terminando.")
        return {"resultado_determinador_competencias": {"area_competencia": "No Clasificable", "justificacion_breve": "No se proporcionó un resumen de los hechos para analizar."}}

    print(f"--- [AGENTE COMPETENCIAS] Hechos a clasificar: '{hechos_clave_triaje[:100]}...'")

    # 2. Consultar CADA base de conocimiento de competencia.
    areas_de_competencia = ["derecho_privado", "derecho_publico", "derecho_penal", "derecho_laboral"]
    contexto_consolidado = ""
    for area in areas_de_competencia:
        try:
            print(f"--- [AGENTE COMPETENCIAS] Buscando contexto en el area: {area}...")
            # Usamos los hechos del caso como consulta para el RAG
            lista_contexto_area = buscar_en_base_de_conocimiento(
                consulta=hechos_clave_triaje,
                area_competencia=area
            )
            contexto_area = "\n\n".join(lista_contexto_area)
            contexto_consolidado += f"--- CONTEXTO DE {area.upper()} ---\n{contexto_area}\n\n"
        except Exception as e:
            print(f"--- [AGENTE COMPETENCIAS] ERROR: Fallo al buscar en RAG '{area}': {e}")
            contexto_consolidado += f"--- CONTEXTO DE {area.upper()} ---\nError al recuperar informacion.\n\n"
    
    print("--- [AGENTE COMPETENCIAS] Contexto de todas las areas recuperado.")

    # 3. Construir el prompt final para la decisión.
    prompt_completo = f"""
    ERES un abogado experto clasificador. Tu única función es analizar los hechos de un caso y, basándote en el contexto legal proporcionado para cada área, determinar a cuál pertenece. Responde únicamente con un objeto JSON.

    --- HECHOS DEL CASO A CLASIFICAR ---
    "{hechos_clave_triaje}"
    --- FIN DE LOS HECHOS ---

    --- CONTEXTO LEGAL DE LAS ÁREAS DE PRÁCTICA ---
    {contexto_consolidado}
    --- FIN DEL CONTEXTO LEGAL ---

    TAREA:
    Compara los "HECHOS DEL CASO" con el "CONTEXTO LEGAL" de cada área. Elige el área que mejor se ajuste al caso.

    AREAS VALIDAS para tu respuesta: "Derecho Privado", "Derecho Publico", "Derecho Laboral", "Derecho Penal", "No Clasificable".

    Devuelve un objeto JSON con la siguiente estructura:
    {{
      "area_competencia": "string (una de las AREAS VALIDAS)",
      "justificacion_breve": "string (Explica brevemente por qué elegiste esa área, basándote en el contexto)"
    }}
    """

    print("--- [AGENTE COMPETENCIAS] Invocando LLM para clasificacion final...")
    resultado_clasificacion = analizar_evidencia_con_gemini(
        archivos_locales=[], prompt_usuario=prompt_completo
    )
    print(f"--- [AGENTE COMPETENCIAS] Clasificacion completada. Resultado: {resultado_clasificacion}")

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


def nodo_preparar_respuesta_rechazo(estado: EstadoDelGrafo) -> Dict[str, Any]:
    """
    Docstring:
    Este nodo se activa cuando el Agente de Triaje determina que un caso no es
    admisible. Su funcion es tomar la justificacion del rechazo y construir
    un mensaje final, claro y empatico para comunicarselo al usuario.

    Args:
        estado (EstadoDelGrafo): El estado actual del grafo, que contiene el
                                 resultado del nodo de triaje.

    Returns:
        Dict[str, Any]: Un diccionario que actualiza el estado del grafo con
                        la clave 'respuesta_para_usuario', conteniendo el
                        mensaje de rechazo.
    """
    print("\n--- [AGENTE RECHAZO] Iniciando ejecucion del nodo ---")
    
    # 1. Extraer la justificacion del rechazo del estado del grafo.
    justificacion_rechazo = estado.get("resultado_triaje", {}).get("justificacion", "No se proporciono una justificacion especifica.")
    print(f"--- [AGENTE RECHAZO] Justificacion recibida del triaje: '{justificacion_rechazo}'")
    
    # 2. Construir el mensaje final para el usuario usando una plantilla.
    mensaje_final_usuario = (
        "Hemos evaluado la informacion de su caso y, lamentablemente, no cumple con los criterios "
        "de competencia definidos para nuestro consultorio juridico por la siguiente razon: "
        f"'{justificacion_rechazo}'. Le agradecemos su tiempo y por contactarnos."
    )
    
    print(f"--- [AGENTE RECHAZO] Mensaje final preparado para el usuario.")
    
    # 3. Devolver el mensaje en la clave que el frontend espera.
    return {"respuesta_para_usuario": mensaje_final_usuario}