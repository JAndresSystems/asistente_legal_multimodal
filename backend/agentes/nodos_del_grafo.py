# backend/agentes/nodos_del_grafo.py

from sqlmodel import Session, select, func
from typing import Dict, Any, Optional

from .estado_del_grafo import EstadoDelGrafo
from ..herramientas.herramientas_lenguaje import analizar_evidencia_con_gemini, generar_respuesta_texto
from ..herramientas.herramienta_rag import buscar_en_base_de_conocimiento
from ..base_de_datos import motor # Eliminamos importaciones no usadas
from ..api.modelos_compartidos import (
    Caso, Asignacion, Estudiante, Asesor, EstadoCaso, AreaEspecialidad)# Eliminamos importaciones no usadas

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
        consulta_contexto = "Reglas de admisibilidad, competencia, beneficiarios y cuantías de los consultorios jurídicos según la Ley 2113. También, qué documentos son esenciales para casos de familia, laboral o civil."
        lista_contexto = buscar_en_base_de_conocimiento(consulta=consulta_contexto)
        contexto_completo = "\n\n---\n\n".join(lista_contexto)
        print(f"--- [AGENTE TRIAJE] Contexto legal y documental recuperado de RAG vectorial.")
    except Exception as e:
        print(f"--- [AGENTE TRIAJE] ERROR: Fallo al buscar en RAG: {e}")
        contexto_completo = "Error: No se pudo recuperar el contexto legal."

    prompt_completo = f"""
    ERES un abogado de triaje para un consultorio juridico gratuito, riguroso pero razonable. Tu mision es calificar casos y pedir la documentacion justa y necesaria. Tu respuesta DEBE ser unicamente un objeto JSON.

    --- CONTEXTO LEGAL Y GUIA DOCUMENTAL ---
    {contexto_completo}
    --- FIN DEL CONTEXTO ---

    --- EVIDENCIA A ANALIZAR ---
    1.  Archivos Adjuntos: {len(rutas_archivos)} archivo(s) proporcionado(s).
    2.  Texto Adicional del Usuario: "{texto_adicional}"
    --- FIN DE LA EVIDENCIA ---

    {'''--- INICIO DE LA MODIFICACIÓN #1: REGLA DE RECURSOS ---'''}
    --- REGLA CRITICA DE RECURSOS Y LIMITES (MUY IMPORTANTE) ---
    1.  ANALIZA MAXIMO 3 ARCHIVOS: Si el usuario ha subido más de 3 archivos, ignora los excedentes y basa tu análisis solo en los 3 primeros. El sistema ya ha limitado los archivos que te entrega, pero esta es una confirmación.
    2.  SE EXTREMADAMENTE CONCISO: Tu "justificacion" y "hechos_clave" deben ser muy breves, directos y al grano para ahorrar recursos.
    {'''--- FIN DE LA MODIFICACIÓN #1 ---'''}

    --- REGLA DE INTERPRETACION JURIDICA ---
    La excepción prevalece sobre la regla general. El Artículo 9 tiene un límite de 50 SMLMV, pero exceptúa los casos de "tránsito". Un caso de accidente de tránsito con reclamación de 50 SMLMV ES ADMISIBLE.

    --- ESTRATEGIA DE SALIDA ---
    Si el usuario indica explícitamente que NO tiene más documentos (ej. "no tengo mas"), DEBES detener el ciclo de preguntas. Establece "informacion_suficiente" como "true" y añade una advertencia en tu "justificacion".
    
    --- REGLA DE FLEXIBILIDAD Y BUENA FE (NUEVO Y MUY IMPORTANTE) ---
    Tu objetivo es pedir los documentos faltantes UNA SOLA VEZ. Después de que hayas hecho una pregunta pidiendo documentos (ej. pidiendo el informe de tránsito), si en la siguiente interacción el usuario sube CUALQUIER archivo (PDF, PNG, JPG), DEBES ASUMIR que ha intentado cumplir tu petición. NO vuelvas a pedir el mismo documento. Considera que con eso es suficiente para esta etapa, marca "informacion_suficiente" como "true" y permite que el caso avance.

    --- INSTRUCCION CRITICA DE JUSTIFICACION ---
    Si y solo si decides que `admisible` es `false`, es OBLIGATORIO que tu `justificacion` contenga una cita textual del `CONTEXTO LEGAL` que respalda tu decisión. Tu explicación debe ser clara y conectar el hecho del caso con la norma.
    (Ejemplo: "El caso no es admisible por superar la cuantía. Fundamento: '...la competencia por cuantía de los consultorios jurídicos no podrá superar los 50 SMLMV...'").

    REGLAS DE DECISION:
    1.  EVALUA ADMISIBILIDAD: ¿El caso es admisible?
    2.  VERIFICA SUFICIENCIA: ¿Tienes los documentos esenciales? Si no, aplica las REGLAS DE SOLICITUD. Si ya pediste y el usuario subió algo, aplica la REGLA DE FLEXIBILIDAD.

    --- REGLAS DE EXCLUSION INQUEBRABLES ---
    1.  CASOS COMERCIALES: RECHAZA cualquier disputa comercial.
    
    REGLAS DE SOLICITUD (Aplica solo la primera vez que falten documentos):
    1.  PIDE MAXIMO 2 DOCUMENTOS: Si faltan documentos, pide solo los 2 más importantes y sé específico (ej. "informe de tránsito y epicrisis médica").

    TAREA:
    Analiza la evidencia y el texto. Devuelve un objeto JSON con la siguiente estructura:
    {{
      "admisible": boolean,
      "justificacion": "string (Si `admisible` es false, DEBE citar el contexto legal como se instruyó)",
      "hechos_clave": "string (Resumen de los hechos)",
      "informacion_suficiente": boolean,
      "pregunta_para_usuario": "string (SOLO si 'informacion_suficiente' es false. De lo contrario, déjalo vacío '')"
    }}
    """
    
    print("--- [AGENTE TRIAJE] Invocando LLM para analisis de admisibilidad...")
    
    # --- INICIO DE LA MODIFICACIÓN #2: BLINDAJE CON TRY-EXCEPT ---
    try:
        # Limitamos la cantidad de archivos enviados a la IA a un máximo de 3.
        archivos_para_analizar = rutas_archivos[:3]
        
        resultado_analisis = analizar_evidencia_con_gemini(
            archivos_locales=archivos_para_analizar,
            prompt_usuario=prompt_completo
        )
        print(f"--- [AGENTE TRIAJE] Analisis completado. Resultado: {resultado_analisis}")
    
    except Exception as e:
        print(f"--- [AGENTE TRIAJE] ERROR-CRITICO: Ha ocurrido una excepcion al llamar a la IA: {e}")
        # Creamos una respuesta de contingencia que no rompa el sistema.
        resultado_analisis_contingencia = {
            "admisible": False,
            "justificacion": "No se pudo completar el análisis de la evidencia. Es posible que los archivos sean demasiado grandes o que haya un problema con el servicio de IA. Por favor, intente con menos archivos o con archivos de menor tamaño.",
            "hechos_clave": "Error en el procesamiento de la IA.",
            "informacion_suficiente": True, # Forzamos a True para detener el flujo.
            "pregunta_para_usuario": ""
        }
        print(f"--- [AGENTE TRIAJE] Generando respuesta de contingencia: {resultado_analisis_contingencia}")
        return {"resultado_triaje": resultado_analisis_contingencia}
    # --- FIN DE LA MODIFICACIÓN #2 ---
        
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

    try:
        print(f"--- [AGENTE COMPETENCIAS] Buscando contexto vectorial para los hechos...")
        # Usamos los hechos del caso para encontrar los fragmentos de ley más relevantes
        lista_contexto = buscar_en_base_de_conocimiento(consulta=hechos_clave_triaje, n_resultados=8)
        contexto_consolidado = "\n\n".join(lista_contexto)
    except Exception as e:
        print(f"--- [AGENTE COMPETENCIAS] ERROR: Fallo al buscar en RAG: {e}")
        contexto_consolidado = "Error al recuperar contexto."

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




def encontrar_persona_con_menos_carga(sesion: Session, modelo: Any, id_area: int) -> Optional[int]:
    """
    Busca en la BD la persona (Estudiante o Asesor) con menos casos asignados
    para un ÁREA DE ESPECIALIDAD específica, usando su ID.
    """
    declaracion = (
        select(modelo.id, func.count(Asignacion.id_caso).label("carga_trabajo"))
        .join(Asignacion, modelo.id == getattr(Asignacion, f"id_{modelo.__name__.lower()}"), isouter=True)
        # La condición ahora usa el ID del área, no un string.
        .where(modelo.id_area_especialidad == id_area)
        .group_by(modelo.id)
        .order_by(func.count(Asignacion.id_caso).asc())
    )
    resultado = sesion.exec(declaracion).first()
    
    # Devuelve el ID de la persona si se encuentra, sino None.
    return resultado.id if resultado else None

def nodo_agente_repartidor(estado: EstadoDelGrafo) -> Dict[str, Any]:
    """
    Nodo que asigna un caso a un estudiante y asesor basándose en el área de competencia
    y la carga de trabajo actual. Además, establece la relación de supervisión permanente.
    """
    print("\n--- [AGENTE REPARTIDOR] Iniciando ejecucion del nodo ---")
    id_caso = estado["id_caso"]
    resultado_competencias = estado.get("resultado_determinador_competencias", {})
    nombre_area = resultado_competencias.get("area_competencia")
    
    if not nombre_area or nombre_area in ["No Clasificable"]:
        print(f"-> ALERTA: Área de competencia inválida ('{nombre_area}'). No se puede asignar.")
        return {"resultado_repartidor": {"detalle": "No se pudo asignar. Area de competencia no valida.", "operacion_db": "omitida"}}

    with Session(motor) as sesion_db:
        area_obj = sesion_db.exec(
            select(AreaEspecialidad).where(AreaEspecialidad.nombre == nombre_area)
        ).first()

        if not area_obj:
            print(f"-> ERROR: El área '{nombre_area}' no se encontró en la base de datos.")
            return {"resultado_repartidor": {"detalle": f"El área '{nombre_area}' no existe. No se pudo asignar.", "operacion_db": "omitida"}}

        id_area_competencia = area_obj.id
        print(f"-> INFO: Área '{nombre_area}' corresponde al ID: {id_area_competencia}.")

        id_estudiante = encontrar_persona_con_menos_carga(sesion_db, Estudiante, id_area_competencia)
        id_asesor = encontrar_persona_con_menos_carga(sesion_db, Asesor, id_area_competencia)
        
        if id_estudiante is not None and id_asesor is not None:
            # --- INICIO DE LA MODIFICACION ---

            # 1. Obtenemos el objeto completo del estudiante para poder actualizarlo.
            estudiante_a_actualizar = sesion_db.get(Estudiante, id_estudiante)
            
            # 2. Si el estudiante existe y no tiene un supervisor permanente...
            if estudiante_a_actualizar and not estudiante_a_actualizar.id_asesor_supervisor:
                # 3. ...le asignamos el asesor de este caso como su supervisor.
                estudiante_a_actualizar.id_asesor_supervisor = id_asesor
                sesion_db.add(estudiante_a_actualizar)
                print(f"-> EXITO (DB): Asignado Asesor ID {id_asesor} como supervisor permanente de Estudiante ID {id_estudiante}.")

            # --- FIN DE LA MODIFICACION ---

            # La lógica original de asignación del caso continúa sin cambios.
            nueva_asignacion = Asignacion(id_caso=id_caso, id_estudiante=id_estudiante, id_asesor=id_asesor)
            sesion_db.add(nueva_asignacion)
            
            caso_a_actualizar = sesion_db.get(Caso, id_caso)
            if caso_a_actualizar:
                caso_a_actualizar.estado = EstadoCaso.PENDIENTE_ACEPTACION
                sesion_db.add(caso_a_actualizar)
                print(f"-> EXITO (DB): Caso {id_caso} actualizado a '{EstadoCaso.PENDIENTE_ACEPTACION.value}'.")
            
            sesion_db.commit()
            
            mensaje_db = f"Asignacion creada en estado 'pendiente' para estudiante {id_estudiante} y asesor {id_asesor}."
            print(f"-> EXITO (DB): Caso {id_caso} ofrecido al equipo.")
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
    """
    Docstring:
    Este nodo actua como un asesor juridico experto que formatea su salida de
    manera estructurada y pedagogica usando Markdown.
    """
    print("\n--- [AGENTE JURIDICO] Iniciando ejecucion del nodo ---")

    pregunta_interactiva = estado.get("pregunta_para_agente_juridico")
    hechos_del_caso = estado.get("hechos_del_caso_para_contexto") or estado.get("resultado_triaje", {}).get("hechos_clave", "")

    if not hechos_del_caso:
        msg = "Ejecucion omitida: No se encontraron hechos del caso para analizar."
        return {"resultado_agente_juridico": {"contenido": msg, "fuentes": []}}

    if pregunta_interactiva:
        print(f"--- [AGENTE JURIDICO] Modo: Interactivo. Pregunta: '{pregunta_interactiva[:50]}...'")
        tarea = f"Resolver la siguiente pregunta específica del estudiante: '{pregunta_interactiva}'"
        instrucciones_adicionales = "Completa todos los puntos de la plantilla de manera detallada pero organizada."
    else:
        print("--- [AGENTE JURIDICO] Modo: Automatico (dentro del grafo).")
        tarea = "Realizar un análisis jurídico inicial y sugerir los posibles caminos a seguir."
        instrucciones_adicionales = "Enfócate en ser muy conciso en la sección 'Estrategia Procesal'."

    consulta_rag = f"Hechos del caso: {hechos_del_caso}\n\nPregunta: {pregunta_interactiva or 'Análisis inicial'}"
    contexto_encontrado = buscar_en_base_de_conocimiento(consulta=consulta_rag)
    contexto_para_prompt = "\n\n---\n\n".join(contexto_encontrado)

    # --- INICIO DE LA MODIFICACION FINAL: EL PROMPT DE TUTOR ESTRUCTURADO ---
    prompt_final = f"""
    Eres un Tutor Jurídico de IA, especializado en Derecho Privado colombiano. Tu propósito es proporcionar respuestas claras, estructuradas y concisas para guiar a estudiantes de derecho.

    --- REGLAS DE ORO (APLICAN A TODAS LAS RESPUESTAS) ---
    1.  **Claridad y Estructura SIEMPRE:** Toda respuesta, sin importar la pregunta, debe estar formateada en Markdown. Utiliza encabezados (`###`), listas (`*` o `1.`) y negritas (`**`) para organizar la información.
    2.  **Concisión Profesional:** Tus respuestas NO DEBEN superar las 200 palabras, a menos que la tarea sea explícitamente un "análisis inicial". Ve directo al grano. Eres un abogado senior, tu tiempo es valioso.
    3.  **Fundamentación Obligatoria:** Siempre que sea posible, cita la base legal de tu respuesta (ej. "según el Art. 2341 C.C.", "conforme a la Ley 1564 de 2012").

    --- CONTEXTO DEL CASO (Tu Memoria) ---
    **Hechos del Caso:**
    {hechos_del_caso}

    **Contexto Jurídico de Apoyo (RAG):**
    {contexto_para_prompt}

    --- TAREA A REALIZAR ---
    **Tarea Específica:** {tarea}

    --- LÓGICA DE RESPUESTA (MUY IMPORTANTE) ---
    *   **Si la "Tarea Específica" es un "análisis jurídico inicial"**, DEBES usar la "PLANTILLA DE ANÁLISIS COMPLETO" que se detalla más abajo.
    *   **Para CUALQUIER OTRA PREGUNTA específica del estudiante**, DEBES usar una estructura simple y directa:
        1.  Un encabezado `### Respuesta a tu Consulta`.
        2.  Una lista de puntos (`*` o `1.`) que respondan directamente a la pregunta, de forma concisa.
        3.  Un encabezado `### Fundamento Legal` donde cites las normas clave.

    --- PLANTILLA A: ANÁLISIS COMPLETO (SOLO PARA ANÁLISIS INICIAL) ---
    ### ANÁLISIS DEL CASO
    **1. Hechos Clave:**
    *   (Resume los hechos en 2-3 puntos).
    **2. Análisis de Competencia:**
    *   **Cuantía:** (Cálculo y conclusión, citando Art. CGP).
    *   **Territorio:** (Juez competente, citando Art. CGP).
    *   **Área de Derecho:** (Confirma el área específica).
    **3. Fundamentos Jurídicos:**
    *   (Lista de 3-4 normas principales).
    **4. Estrategia Procesal:**
    1.  (Primer paso obligatorio).
    2.  (Segundo paso: Pruebas).
    3.  (Tercer paso: Demanda).
    ### ESQUELETO DE LA DEMANDA
    *   **Encabezado:** Juez Civil Municipal de [Ciudad].
    *   **Partes:** Demandante y Demandados.
    *   **Pretensiones:** (Lista concisa de 1 a 4).
    *   **Pruebas Clave:** (Lista de 3-5 pruebas esenciales).
    --- FIN DE LA PLANTILLA A ---
    """
    # --- FIN DE LA MODIFICACION FINAL ---

    contenido_respuesta = generar_respuesta_texto(prompt_final)
    resultado = {"contenido": contenido_respuesta, "fuentes": contexto_encontrado}
    
    print("--- [AGENTE JURIDICO] Respuesta estructurada generada exitosamente.")
    return {"resultado_agente_juridico": resultado}



def nodo_agente_generador_documentos(estado: EstadoDelGrafo) -> Dict[str, Any]:
    return {"resultado_agente_generador_documentos": "Ejecucion omitida en este flujo."}


def nodo_preparar_respuesta_rechazo(estado: EstadoDelGrafo) -> Dict[str, Any]:
    """
    Docstring:
    Este nodo se activa cuando el Agente de Triaje determina que un caso no es
    admisible. Sus funciones son:
    1. Persistir el resultado del rechazo en la base de datos.
    2. Construir un mensaje final, claro y empático para el usuario.
    """
    print("\n--- [AGENTE RECHAZO] Iniciando ejecucion del nodo ---")
    
    # --- INICIO DE LA MODIFICACIÓN ---
    
    # 1. Extraer los datos clave del estado.
    id_caso = estado["id_caso"]
    justificacion_rechazo = estado.get("resultado_triaje", {}).get("justificacion", "No se proporcionó una justificación específica.")
    print(f"--- [AGENTE RECHAZO] Justificacion recibida del triaje: '{justificacion_rechazo}'")

    # 2. Actualizar la base de datos con el estado y la justificación.
    try:
        with Session(motor) as sesion_db:
            caso_a_actualizar = sesion_db.get(Caso, id_caso)
            if caso_a_actualizar:
                caso_a_actualizar.estado = EstadoCaso.RECHAZADO
                caso_a_actualizar.justificacion_rechazo = justificacion_rechazo
                sesion_db.add(caso_a_actualizar)
                sesion_db.commit()
                print(f"--- [AGENTE RECHAZO] (DB): Caso {id_caso} actualizado a '{EstadoCaso.RECHAZADO.value}' con justificación.")
            else:
                print(f"--- [AGENTE RECHAZO] (DB) ADVERTENCIA: No se encontró el caso {id_caso} para actualizar.")
    except Exception as e:
        print(f"--- [AGENTE RECHAZO] (DB) ERROR: Fallo al actualizar la base de datos: {e}")

    # 3. Construir el mensaje final para el usuario usando una plantilla.
    mensaje_final_usuario = (
        "Hemos evaluado la información de su caso y, lamentablemente, no cumple con los criterios "
        "de competencia definidos para nuestro consultorio jurídico. La razón es la siguiente: "
        f"'{justificacion_rechazo}'. Le agradecemos su tiempo y por contactarnos."
    )
    
    print(f"--- [AGENTE RECHAZO] Mensaje final preparado para el usuario.")
    
    # 4. Devolver el mensaje en la clave que el frontend espera.
    return {"respuesta_para_usuario": mensaje_final_usuario}