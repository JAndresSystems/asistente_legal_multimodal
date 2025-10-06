from sqlmodel import Session, select, func
from typing import Dict, Any, Optional

from .estado_del_grafo import EstadoDelGrafo
from ..herramientas.herramientas_lenguaje import analizar_evidencia_con_gemini, generar_respuesta_texto
from ..herramientas.herramienta_rag import buscar_en_base_de_conocimiento
from ..herramientas.herramienta_documentos import generar_documento_desde_plantilla
from ..base_de_datos import motor
from ..api.modelos_compartidos import Estudiante, Asesor, Asignacion, Caso, Usuario

# --- (Nodos 1, 2.A y 2.B permanecen igual que en la corrección anterior) ---
def nodo_agente_triaje(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente de Triaje ---")
    rutas_archivos = estado["rutas_archivos_evidencia"]
    prompt_sistema = """
    ERES un asistente legal experto. Analiza la evidencia para determinar la admisibilidad del caso.
    REGLAS:
    1. Responde solo con un JSON valido: {"admisible": bool, "justificacion": "string", "hechos_clave": "string"}
    2. Criterios: No penal y de bajos recursos.
    """
    prompt_usuario = "Analiza la evidencia y determina la admisibilidad del caso."
    prompt_completo = f"{prompt_sistema}\n\n{prompt_usuario}"
    resultado_analisis = analizar_evidencia_con_gemini(
        archivos_locales=rutas_archivos,
        prompt_usuario=prompt_completo
    )
    return {"resultado_triaje": resultado_analisis}

def nodo_agente_analizador_pdf(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente Analizador de PDFs ---")
    rutas_archivos = estado["rutas_archivos_evidencia"]
    prompt_sistema = """
    ERES una API de extraccion juridica. Analiza el PDF y devuelve un JSON con la estructura:
    {"tipo_documento_identificado": "string", "partes_involucradas": ["string"], "fechas_clave": ["string"], "resumen_del_objeto": "string", "puntos_relevantes": ["string"]}
    """
    prompt_usuario = "Extrae la informacion semantica clave del documento legal."
    prompt_completo = f"{prompt_sistema}\n\n{prompt_usuario}"
    resultado_extraccion = analizar_evidencia_con_gemini(
        archivos_locales=rutas_archivos,
        prompt_usuario=prompt_completo
    )
    return {"resultado_analisis_documento": resultado_extraccion}

def nodo_agente_analizador_audio(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente Analizador de Audio ---")
    rutas_archivos = estado["rutas_archivos_evidencia"]
    prompt_sistema = """
    ERES una API de procesamiento de audio. Escucha la grabacion y devuelve un JSON con la estructura:
    {"transcripcion_completa": "string", "resumen_puntos_clave": "string"}
    """
    prompt_usuario = "Escucha, transcribe y resume los puntos clave de la grabacion."
    prompt_completo = f"{prompt_sistema}\n\n{prompt_usuario}"
    resultado_analisis = analizar_evidencia_con_gemini(
        archivos_locales=rutas_archivos,
        prompt_usuario=prompt_completo
    )
    return {"resultado_analisis_audio": resultado_analisis}


# --- NODO 3: AGENTE DETERMINADOR DE COMPETENCIAS (MEJORADO CON RAG) ---
def nodo_agente_determinador_competencias(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente Determinador de Competencias ---")
    hechos_clave_triaje = estado.get("resultado_triaje", {}).get("hechos_clave", "")
    analisis_documento = estado.get("resultado_analisis_documento")
    analisis_audio = estado.get("resultado_analisis_audio")
    
    contexto_para_analisis = f"Hechos iniciales: {hechos_clave_triaje}\n"
    if analisis_documento:
        contexto_para_analisis += f"Info de documento: {analisis_documento.get('resumen_del_objeto', '')}\n"
    if analisis_audio:
        contexto_para_analisis += f"Info de audio: {analisis_audio.get('resumen_puntos_clave', '')}\n"

    # --- INICIO DE LA MEJORA CON RAG ---
    # Buscamos casos similares para enriquecer el prompt (Case-Based Reasoning)
    contexto_rag = buscar_en_base_de_conocimiento(
        consulta=hechos_clave_triaje, 
        area_competencia="derecho_privado" # Esto podria ser dinamico en el futuro
    )
    # --- FIN DE LA MEJORA CON RAG ---

    prompt_sistema = """
    ERES un jurista experto. Clasifica el caso en un area.
    REGLAS:
    1. Responde solo con JSON: {"area_competencia": "string", "justificacion_breve": "string"}
    2. Areas validas: "Derecho Privado", "Derecho Publico", "Derecho Laboral", "Derecho de Familia", "No Clasificable".
    """
    prompt_usuario = f"Considerando los siguientes ejemplos de casos clasificados: \n---EJEMPLOS---\n{contexto_rag}\n---FIN EJEMPLOS---\n\n Basado en el siguiente contexto del nuevo caso, clasificalo:\n{contexto_para_analisis}"
    prompt_completo = f"{prompt_sistema}\n\n{prompt_usuario}"

    resultado_clasificacion = analizar_evidencia_con_gemini(
        archivos_locales=[], prompt_usuario=prompt_completo
    )
    return {"resultado_determinador_competencias": resultado_clasificacion}


# --- (Nodo Repartidor y Juridico permanecen igual) ---
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
    resultado_competencias = estado.get("resultado_determinador_competencias", {})
    area_competencia = resultado_competencias.get("area_competencia")
    if not area_competencia or area_competencia in ["No Clasificable"]:
        return {"resultado_repartidor": {"detalle": "No se asigno por area invalida."}}
    with Session(motor) as sesion_db:
        id_estudiante = encontrar_persona_con_menos_carga(sesion_db, Estudiante, area_competencia)
        id_asesor = encontrar_persona_con_menos_carga(sesion_db, Asesor, area_competencia)
    resultado = {"id_estudiante_asignado": id_estudiante, "id_asesor_asignado": id_asesor}
    return {"resultado_repartidor": resultado}

def nodo_agente_juridico(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente Juridico ---")
    pregunta = estado.get("solicitud_agente_juridico")
    area = estado.get("resultado_determinador_competencias", {}).get("area_competencia")
    if not pregunta or not area:
        return {"resultado_agente_juridico": "Faltan datos (pregunta o area) para la consulta."}
    contexto_rag = buscar_en_base_de_conocimiento(consulta=pregunta, area_competencia=area)
    prompt = f"Contexto: {contexto_rag}\n\nPregunta: {pregunta}\n\nRespuesta fundamentada:"
    respuesta = generar_respuesta_texto(prompt=prompt)
    return {"resultado_agente_juridico": respuesta}

# --- NODO 6: AGENTE GENERADOR DE DOCUMENTOS (CORREGIDO) ---
def nodo_agente_generador_documentos(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente Generador de Documentos ---")
    id_caso = estado.get("id_caso")
    solicitud = estado.get("solicitud_agente_documentos")
    if not id_caso or not solicitud:
        return {"resultado_agente_generador_documentos": "Falta id_caso o solicitud."}

    with Session(motor) as sesion_db:
        caso, usuario = sesion_db.exec(select(Caso, Usuario).join(Usuario).where(Caso.id == id_caso)).one()
        datos_plantilla = {"nombre_completo": usuario.nombre, "cedula": usuario.cedula, "hechos_del_caso": caso.descripcion_hechos}
    
    # --- INICIO DE LA CORRECCION ---
    # El nombre del argumento correcto en la herramienta es 'datos_reemplazo'
    ruta_archivo = generar_documento_desde_plantilla(
        nombre_plantilla=f"{solicitud.get('tipo_documento')}.docx",
        datos_reemplazo=datos_plantilla, 
        id_caso=str(id_caso)
    )
    # --- FIN DE LA CORRECCION ---

    return {"resultado_agente_generador_documentos": ruta_archivo}