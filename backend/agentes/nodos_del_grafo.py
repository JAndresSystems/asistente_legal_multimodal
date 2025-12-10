# backend/agentes/nodos_del_grafo.py
import json
import mimetypes # <-- Importante para detectar tipos de archivo
from pathlib import Path # <-- Para manejar rutas de archivos
from sqlmodel import Session, select, func
from typing import Dict, Any, List, Optional

from .estado_del_grafo import EstadoDelGrafo
from ..herramientas.herramientas_lenguaje import analizar_evidencia_con_gemini, generar_respuesta_texto
from ..herramientas.herramienta_rag import buscar_en_base_de_conocimiento
from ..base_de_datos import motor # Eliminamos importaciones no usadas
from ..api.modelos_compartidos import (
    Caso, Asignacion, Estudiante, Asesor, EstadoCaso, AreaEspecialidad)# Eliminamos importaciones no usadas

def _formatear_historial(historial: List[Dict[str, str]]) -> str:
    """Función utilitaria para convertir el historial en un string legible para el LLM."""
    if not historial:
        return "No hay conversación previa."
    
    texto_formateado = ""
    for mensaje in historial:
        rol = "Usuario" if mensaje.get("autor") == "usuario" else "Asistente Camila"
        texto_formateado += f"{rol}: {mensaje.get('texto')}\n"
    return texto_formateado.strip()

# --- NUEVA FUNCIÓN DE APOYO PARA ANALIZAR AUDIOS ---
def _extraer_info_de_audios(rutas_archivos: List[str]) -> str:
    """
    Toma una lista de rutas de archivos, identifica los audios,
    los transcribe y devuelve un string con la información extraída.
    """
    info_multimodal = ""
    for ruta in rutas_archivos:
        tipo_mime, _ = mimetypes.guess_type(ruta)
        if tipo_mime and tipo_mime.startswith('audio/'):
            print(f"--- [FUNCION APOYO] Procesando audio: {ruta}")
            try:
                # Usamos la herramienta de análisis de audio para transcribir
                resultado_audio = analizar_evidencia_con_gemini(
                    prompt_usuario="Escucha atentamente el audio y proporciona una transcripción completa del contenido hablado. Tambien resume brevemente los puntos clave mencionados, especialmente si se menciona la condición socioeconómica (estrato, Sisbén, etc.).",
                    archivos_locales=[ruta]
                )
                
                if "error" not in resultado_audio:
                    transcripcion = resultado_audio.get("transcripcion_completa", "")
                    resumen_audio = resultado_audio.get("resumen_puntos_clave", "")
                    if transcripcion:
                        info_multimodal += f"\n\n[Transcripción de {Path(ruta).name}]: {transcripcion}"
                        if resumen_audio:
                            info_multimodal += f"\n[Resumen de {Path(ruta).name}]: {resumen_audio}"
                        print(f"--- [FUNCION APOYO] Audio transcrito: {Path(ruta).name}")
                else:
                    print(f"--- [FUNCION APOYO] ERROR al transcribir audio '{ruta}': {resultado_audio.get('error', 'Error desconocido')}")
                    
            except Exception as e:
                print(f"--- [FUNCION APOYO] ERROR inesperado al procesar audio '{ruta}': {e}")
    
    return info_multimodal.lstrip("\n") # Quitamos el salto de línea inicial si no hay info
# --- FIN DE LA FUNCIÓN DE APOYO ---

# --- INICIO DEL CAMBIO FINAL Y DEFINITIVO ---

def nodo_agente_triaje(estado: dict) -> dict:
    """
    Nodo principal del Agente de Triaje ("Camila").
    VERSIÓN CORREGIDA: Lógica estricta de validación de hechos y uso de RAG para justificación.
    MEJORA: Ahora analiza activamente el contenido de los audios para extraer información crítica
    y la incluye en el contexto del prompt. Tambien analiza imagenes/PDFs buscando documentos clave
    como Sisben o cedula, actualizando su estado interno y respondiendo explicitamente sobre ellos.
    """
    print("\n--- [AGENTE TRIAJE] Iniciando ejecucion del nodo ---")
    
    rutas_archivos = estado.get("rutas_archivos_evidencia", [])
    descripcion_hechos = estado.get("descripcion_hechos", "")
    historial_chat = estado.get("historial_chat", [])
    
    ultimo_mensaje_usuario = ""
    # Recuperamos el último mensaje para detectar la intención de cierre
    if historial_chat:
        ultimo_mensaje_usuario = historial_chat[-1].get("texto", "")

    # --- ANALISIS ACTIVO DE CONTENIDO MULTIMEDIA (AUDIOS, IMAGENES, PDFs) ---
    # Procesamos audios para obtener transcripciones y agregarlas al contexto
    info_audios_extraida = _extraer_info_de_audios(rutas_archivos)
    
    # Procesamos imagenes/PDFs buscando info critica (esto es un ejemplo simple)
    info_documentos_extraida = ""
    sisben_visto = False
    cedula_vista = False
    estrato_detectado = None
    for ruta in rutas_archivos:
        tipo_mime, _ = mimetypes.guess_type(ruta)
        if tipo_mime and (tipo_mime.startswith('image/') or tipo_mime == 'application/pdf'):
            print(f"--- [AGENTE TRIAJE] Analizando documento: {ruta}")
            try:
                # Usamos la herramienta de análisis de documentos para extraer info
                resultado_doc = analizar_evidencia_con_gemini(
                    prompt_usuario="Analiza este documento. Si es un certificado del Sisbén, extrae el estrato y el nombre del titular. Si es una cédula, extrae el número y el nombre. Resume brevemente los datos clave.",
                    archivos_locales=[ruta]
                )
                
                if "error" not in resultado_doc:
                    tipo_doc_identificado = resultado_doc.get("tipo_documento_identificado", "")
                    partes_doc = resultado_doc.get("partes_involucradas", [])
                    resumen_objeto = resultado_doc.get("resumen_del_objeto", "")
                    
                    if "Sisbén" in tipo_doc_identificado or "sisben" in resumen_objeto.lower():
                        sisben_visto = True
                        # Intentamos extraer el estrato del resumen o de las partes
                        for parte in partes_doc:
                            if "estrato" in parte.lower():
                                import re
                                match = re.search(r'estrato\s*(\d+)', parte.lower())
                                if match:
                                    estrato_detectado = match.group(1)
                                    break
                        info_documentos_extraida += f"\n[Documento Analizado: {Path(ruta).name}] Certificado Sisbén detectado. Estrato: {estrato_detectado}. Nombre en documento: {partes_doc[0] if partes_doc else 'No identificado'}. "
                        print(f"--- [AGENTE TRIAJE] Sisbén detectado en {ruta}, Estrato: {estrato_detectado}")
                    
                    elif "Cédula" in tipo_doc_identificado or "Identidad" in resumen_objeto:
                        cedula_vista = True
                        info_documentos_extraida += f"\n[Documento Analizado: {Path(ruta).name}] Cédula de ciudadanía detectada. Nombre en documento: {partes_doc[0] if partes_doc else 'No identificado'}. "
                        print(f"--- [AGENTE TRIAJE] Cédula detectada en {ruta}")
                    
                    if resumen_objeto:
                         info_documentos_extraida += f"\n[Resumen de {Path(ruta).name}]: {resumen_objeto}. "
                        
                else:
                     print(f"--- [AGENTE TRIAJE] ERROR al analizar documento '{ruta}': {resultado_doc.get('error', 'Error desconocido')}")
                    
            except Exception as e:
                print(f"--- [AGENTE TRIAJE] ERROR inesperado al procesar documento '{ruta}': {e}")
    
    # Actualizamos la descripción de hechos con la info de los audios y documentos
    descripcion_hechos_completa = descripcion_hechos
    if info_audios_extraida:
        descripcion_hechos_completa += "\n\nInformación extraída de audios:\n" + info_audios_extraida
        print(f"--- [AGENTE TRIAJE] Descripción de hechos actualizada con info de audios.")
    if info_documentos_extraida:
        descripcion_hechos_completa += "\n\nInformación extraída de documentos:\n" + info_documentos_extraida
        print(f"--- [AGENTE TRIAJE] Descripción de hechos actualizada con info de documentos.")

    try:
        # Construimos una consulta enriquecida para el RAG
        # Usamos la descripción actualizada que incluye info de audios y documentos
        consulta_contexto = f"Reglas de admisibilidad (Ley 2113 de 2021) y Requisitos legales y documentos obligatorios para casos de: {descripcion_hechos_completa}"
        contexto_rag = buscar_en_base_de_conocimiento(consulta=consulta_contexto)
        contexto_completo = "\n\n---\n\n".join(contexto_rag)
        print(f"--- [AGENTE TRIAJE] Contexto legal recuperado (RAG): {len(contexto_rag)} fragmentos.")
    except Exception as e:
        print(f"--- [AGENTE TRIAJE] ERROR: Fallo al buscar en RAG: {e}")
        contexto_completo = "No se pudo recuperar el contexto legal."

    # --- INICIO DEL PROMPT CORREGIDO Y RAZONADO ---
    prompt_sistema_triaje = f"""
    Eres "Camila", un agente de triaje jurídico experto, estricto pero amable. Tu función es determinar si un caso puede ser admitido en un consultorio jurídico según la Ley 2113 de 2021.

    --- REGLA DE CITAS Y FUENTES ---
    Al citar el contexto legal, elimina cualquier extensión de archivo (.txt, .pdf). Indica siempre que la jurisprudencia o norma fue recuperada de la "Base de Datos Vectorial Chroma DB".

    --- TUS HERRAMIENTAS DE VERDAD (CONTEXTO LEGAL RAG) ---
    {contexto_completo}
    --- FIN CONTEXTO ---

    --- INFORMACIÓN EXTRAÍDA DE AUDIOS (si aplica) ---
    {info_audios_extraida}
    --- FIN INFORMACIÓN EXTRAÍDA ---

    --- INFORMACIÓN EXTRAÍDA DE DOCUMENTOS (si aplica) ---
    {info_documentos_extraida}
    --- FIN INFORMACIÓN EXTRAÍDA ---

    --- ESTADO DEL CASO ---
    1. Hechos del Caso: "{descripcion_hechos_completa}"
    2. Archivos Entregados: {len(rutas_archivos)} archivos ({[Path(r).name for r in rutas_archivos]}).
    3. Lo que acaba de decir el usuario: "{ultimo_mensaje_usuario}"

    --- REGLAS DE ADMISIBILIDAD LEGAL (VERIFICA ESTO ESTRUCTURADAMENTE) ---

    1. **VALIDACIÓN DE EXISTENCIA (CRÍTICO):**
    - Si el campo "Hechos del Caso" está VACÍO o es trivial (ej. "hola", "ayuda"), y el usuario dice "no tengo más datos", TU DECISIÓN DEBE SER "NO_ADMISSIBLE".
    - Razón: No se puede abrir un expediente jurídico sin hechos fácticos.
    - Mensaje: Explica que sin una narración de los hechos es jurídicamente imposible ayudarle.

    2. **VERIFICACIÓN DE DOCUMENTOS OBLIGATORIOS:**
    - Para admisión, se requiere EVIDENCIA de la condición socioeconómica del solicitante (Sisbén o recibo de servicio público).
    - EVALÚA SI ESTA INFORMACIÓN YA FUE PROPORCIONADA EN LOS DOCUMENTOS ANALIZADOS: Se detectó Sisbén (Estrato {estrato_detectado}) o se mencionó en audios.
    - EVALÚA SI LA CÉDULA YA FUE VISTA: Se detectó cédula en documentos subidos.
    - Si NO tienes evidencia de la condición socioeconómica (y no fue detectada arriba) o no tienes la cédula (y no fue detectada arriba), TU DECISIÓN DEBE SER "FALTA_INFORMACION".
    - Mensaje: "Para poder continuar con su caso, necesitamos que nos proporcione un documento que acredite su condición socioeconómica, como su certificado del Sisbén o un recibo de servicio público (agua, luz, gas) reciente." o "También necesitamos su cédula de ciudadanía.". Incluye explícitamente si ya viste un documento (por ejemplo: "Ya vi el certificado del Sisbén que adjuntó, donde se confirma que es estrato {estrato_detectado}."). Si viste un audio donde dijo su estrato, menciona: "Ya escuché en el audio que usted mencionó ser estrato {estrato_detectado}."

    3. **ANÁLISIS DE CIERRE FORZADO ("No tengo más"):**
    - Si el usuario indica que NO tiene más pruebas/datos...
    - ...PERO SÍ tienes hechos claros, al menos 1 documento relevante (contrato, cédula -si fue vista-, etc.) Y evidencia de condición socioeconómica (si fue vista o mencionada), DECISIÓN -> "ADMISSIBLE".
    - ...Y los hechos son confusos, no hay NINGUNA evidencia obligatoria o falta evidencia de condición socioeconómica (y no fue detectada), DECISIÓN -> "NO_ADMISSIBLE".

    4. **ANÁLISIS DE PROGRESO (Flujo Normal):**
    - Si tienes hechos claros pero faltan documentos mencionados en tu Contexto Legal (ej. Cédula -si no fue vista-, IPAT, Historia Clínica) o falta evidencia de condición socioeconómica (si no fue detectada), DECISIÓN -> "FALTA_INFORMACION".
    - Pide Específicamente lo que falta basándote en la ley.

    5. **ANÁLISIS DE CONTENIDO MULTIMEDIA:**
    - Si hay audios entre los archivos, debes interpretar su contenido para identificar información relevante como la condición socioeconómica del usuario, declaraciones importantes o hechos adicionales.
    - Si un audio revela que el usuario es de estrato 7 o afirma no tener Sisbén, esto es CRÍTICO para la decisión de admisibilidad.

    6. **CASOS EXCLUIDOS O RESTRINGIDOS (REGLA DE ORO - LEY 2113 DE 2021):**
    - **Estado Civil:** Si el caso trata sobre matrimonio, divorcio, filiación, etc., TU DECISIÓN DEBE SER "NO_ADMISSIBLE". Razón: Son derechos irrenunciables e indisponibles.
    - **Cuantía:** Si la pretensión supera los 50 SMLMV (Salarios Mínimos) en civil, TU DECISIÓN DEBE SER "NO_ADMISSIBLE" (salvo mínima cuantía).
    - **Procedimientos Administrativos:** Casos ante Superintendencias, procesos sancionatorios administrativos o policivos verbales abreviados están excluidos.
    - **Otros:** Asuntos que requieren apoderado judicial específico (contra funcionarios de alto rango) o temas no contemplados en la ley.

    --- FORMATO DE RESPUESTA OBLIGATORIO ---
    DEBES RESPONDER ÚNICAMENTE CON UN OBJETO JSON CON ESTA ESTRUCTURA EXACTA:
    {{
        "resumen_evidencia": "Resumen técnico de lo recibido, incluyendo análisis del contenido de audios y documentos si los hubiera. Menciona específicamente si se encontró información sobre condición socioeconómica o cédula en los documentos o audios.",
        "decision_triaje": "ADMISSIBLE | NO_ADMISSIBLE | FALTA_INFORMACION",
        "justificacion": "Análisis interno técnico citando la ley o el motivo. Debe incluir análisis de condición socioeconómica y fundamentación legal basada en el contexto RAG. NO cites nombres de archivos, sino las leyes y artículos específicos como 'Ley 2113 de 2021, Artículo 8' o 'Ley 2113 de 2021, Capítulo II'. Menciona si se encontró información sobre condición socioeconómica o cédula en los documentos o audios y cómo afectó la decisión.",
        "mensaje_para_usuario": "EXPLICACIÓN CLARA PARA EL CIUDADANO. Si ACEPTAS: Di 'Tu caso fue aceptado porque [Razón basada en hechos/ley]'. Si RECHAZAS: Di 'No podemos aceptar el caso porque [Razón: faltan hechos/documentos/condición socioeconómica/según la Ley 2113 de 2021]'. Si PIDE MÁS INFO: Di 'Necesitamos [documento específico] para continuar.' y MENCIONA EXPLÍCITAMENTE si YA SE DETECTÓ ALGUNO (por ejemplo: 'Ya vi el certificado del Sisbén donde se confirma que es estrato {estrato_detectado}.' o 'Ya escuché en el audio que mencionó ser estrato {estrato_detectado}.').",
        "hechos_clave": "Resumen jurídico de los hechos (MÁX 2 PÁRRAFOS). Si decides ADMISSIBLE, este campo NO puede estar vacío."
    }}
    NO AGREGUES NADA MÁS QUE EL OBJETO JSON. NO USES MARCADORES DE CÓDIGO. RESPONDE DIRECTAMENTE CON EL JSON.
    """
    # --- FIN DEL PROMPT ---
    
    try:
        print(f"--- [AGENTE TRIAJE] Invocando herramienta multimodal con {len(rutas_archivos)} archivos...")
        # La herramienta analiza el prompt (que ahora incluye info de docs/audios) y los archivos
        resultado_analisis = analizar_evidencia_con_gemini(
            prompt_usuario=prompt_sistema_triaje,
            archivos_locales=rutas_archivos
        )
        print("--- [AGENTE TRIAJE] Análisis multimodal completado.")
        
        if "error" in resultado_analisis:
            raise Exception(f"La herramienta de análisis devolvió un error: {resultado_analisis['error']}")
        
        # --- SALVAGUARDA DE COHERENCIA ---
        decision = resultado_analisis.get("decision_triaje")
        hechos = resultado_analisis.get("hechos_clave")
        
        # Si el agente dice ADMISSIBLE pero no generó hechos (porque estaba vacío), corregimos a NO_ADMISSIBLE
        if decision == "ADMISSIBLE" and (not hechos or len(hechos) < 10):
            print("--- [AGENTE TRIAJE] CORRECCIÓN AUTOMÁTICA: Admisible sin hechos -> Cambiando a NO_ADMISSIBLE.")
            resultado_analisis["decision_triaje"] = "NO_ADMISSIBLE"
            resultado_analisis["mensaje_para_usuario"] = "He revisado la información, pero no encontré una descripción clara de los hechos del caso. Sin narración de lo sucedido, no podemos proceder legalmente. Por favor, descríbeme qué ocurrió."
            resultado_analisis["justificacion"] = "Fallo de consistencia: Se intentó admitir un caso sin descripción de hechos válida."

        # Si hay hechos pero el agente olvidó llenarlos en el JSON, usamos el del estado
        elif decision == "ADMISSIBLE" and not hechos:
             resultado_analisis["hechos_clave"] = descripcion_hechos_completa

        return {"resultado_triaje": resultado_analisis}

    except Exception as e:
        print(f"--- [AGENTE TRIAJE] ERROR CRÍTICO en el nodo: {e}")
        resultado_contingencia = {
            "resumen_evidencia": "Error técnico durante el análisis.",
            "decision_triaje": "FALTA_INFORMACION", # Default seguro: pedir que intente de nuevo
            "justificacion": f"Excepción no controlada: {str(e)}",
            "mensaje_para_usuario": "Lo siento, tuve un problema técnico analizando tus archivos. ¿Podrías intentar describir los hechos nuevamente o subir los documentos de uno en uno?",
            "hechos_clave": ""
        }
        return {"resultado_triaje": resultado_contingencia}

# --- FIN DEL CAMBIO FINAL Y DEFINITIVO ---

# ... (El resto del archivo nodos_del_grafo.py permanece igual) ...

# --- FIN DEL CAMBIO FINAL Y DEFINITIVO ---


def nodo_solicitar_informacion_adicional(estado: EstadoDelGrafo) -> Dict[str, Any]:
    """
    Docstring:
    Este nodo es el CORAZÓN de "Camila". Comunica la necesidad de más
    documentos de forma amable y le indica al frontend que la conversación DEBE continuar.
    VERSIÓN SIMPLIFICADA: Ya no necesita parsear el JSON, lo recibe como un diccionario
    directamente desde el orquestador.
    """
    print("\n--- [AGENTE SOLICITUD - CORAZÓN] Iniciando ejecucion del nodo ---")
    
    try:
        # Gracias a la corrección en el orquestador, ahora podemos leer esto directamente.
        resultado_triaje_dict = estado.get("resultado_triaje", {})
        mensaje_para_usuario = resultado_triaje_dict.get("mensaje_para_usuario", "Necesito más información, pero no pude generar un mensaje específico.")

    except Exception as e:
        print(f"--- [AGENTE SOLICITUD - CORAZÓN] ERROR al procesar resultado: {e}")
        mensaje_para_usuario = "Parece que necesito más información, pero he encontrado un problema al generar mi respuesta. ¿Podrías intentar adjuntar los documentos que consideres relevantes?"

    print(f"--- [AGENTE SOLICITUD - CORAZÓN] Respuesta conversacional obtenida: '{mensaje_para_usuario}'")
    
    return {
        "respuesta_para_usuario": mensaje_para_usuario, 
        "flujo_terminado": False
    }

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
     --- REGLA DE CITAS ---
    Basate en la "Base de Datos Vectorial Chroma DB". NUNCA menciones nombres de archivos con extensión (.txt, .pdf).
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
     --- REGLA DE CITAS Y FUENTES ---
    Al citar el contexto legal, elimina cualquier extensión de archivo (.txt, .pdf). Indica siempre que la jurisprudencia o norma fue recuperada de la "Base de Datos Vectorial Chroma DB".
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
    Este nodo se activa para un caso no admisible. Persiste el rechazo en la BD,
    construye un mensaje empático y le indica al frontend que el flujo TERMINÓ SIN ÉXITO.
    """
    print("\n--- [AGENTE RECHAZO] Iniciando ejecucion del nodo ---")
    
    id_caso = estado["id_caso"]
    justificacion_rechazo = estado.get("resultado_triaje", {}).get("justificacion", "No se proporcionó una justificación específica.")
    print(f"--- [AGENTE RECHAZO] Justificacion recibida: '{justificacion_rechazo}'")

    try:
        with Session(motor) as sesion_db:
            caso_a_actualizar = sesion_db.get(Caso, id_caso)
            if caso_a_actualizar:
                caso_a_actualizar.estado = EstadoCaso.RECHAZADO
                caso_a_actualizar.justificacion_rechazo = justificacion_rechazo
                sesion_db.add(caso_a_actualizar)
                sesion_db.commit()
                print(f"--- [AGENTE RECHAZO] (DB): Caso {id_caso} actualizado a '{EstadoCaso.RECHAZADO.value}'.")
    except Exception as e:
        print(f"--- [AGENTE RECHAZO] (DB) ERROR: {e}")

    mensaje_final_usuario = (
        "Hemos evaluado la información de su caso y, lamentablemente, no cumple con los criterios "
        "de competencia de nuestro consultorio en este momento. La razón es la siguiente: "
        f"'{justificacion_rechazo}'. Le agradecemos su tiempo."
    )
    
    print(f"--- [AGENTE RECHAZO] Mensaje final preparado.")
    
    # Le decimos al frontend que el flujo TERMINÓ y que el caso NO fue admitido.
    return {
        "respuesta_para_usuario": mensaje_final_usuario,
        "flujo_terminado": True,
        "caso_admitido": False
    }



def nodo_preparar_respuesta_aceptacion(estado: EstadoDelGrafo) -> Dict[str, Any]:
    """
    Docstring:
    Este nodo se activa cuando un caso es admitido. Construye un mensaje transparente
    y le indica al frontend que el flujo TERMINÓ CON ÉXITO.
    """
    print("\n--- [AGENTE ACEPTACIÓN] Iniciando ejecucion del nodo ---")
    
    resultado_triaje = estado.get("resultado_triaje", {})
    justificacion_aceptacion = resultado_triaje.get("justificacion", "Su caso ha sido admitido.")
    mensaje_usuario = resultado_triaje.get("mensaje_para_usuario", "")
    
    # Extraemos la justificación legal específica del agente de triaje
    # que está basada en la base de datos de conocimiento (Chroma DB)
    mensaje_final_usuario = (
        f"¡Buenas noticias! {mensaje_usuario} "
        "Hemos verificado que su caso cumple con los requisitos de admisibilidad según la Ley 2113 de 2021. "
        "A partir de este momento, nuestro equipo interno comenzará el proceso de clasificación y asignación a un estudiante. "
        "Puede seguir el estado de su caso desde su panel principal."
    )
    
    print(f"--- [AGENTE ACEPTACIÓN] Mensaje final preparado basado en justificación legal: {justificacion_aceptacion}")
    
    # Le decimos al frontend que el flujo TERMINÓ y que el caso SÍ fue admitido.
    return {
        "respuesta_para_usuario": mensaje_final_usuario,
        "flujo_terminado": True,
        "caso_admitido": True
    }