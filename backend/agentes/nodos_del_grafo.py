from sqlmodel import Session, select, func
from ..base_de_datos import motor
from ..api.modelos_compartidos import Asignacion, Estudiante, Asesor
from .estado_del_grafo import EstadoDelGrafo
from ..herramientas import herramientas_lenguaje

# =================================================================================
# NODO 1: AGENTE DE TRIAJE (PROMPT REFORZADO)
# =================================================================================
def nodo_agente_triaje(estado: EstadoDelGrafo) -> dict:
    print("\n--- Entrando en el Nodo: Agente de Triaje ---")
    historial_chat = estado["historial_conversacion"]
    rutas_evidencia = estado["rutas_archivos_evidencia"]

    # --- PROMPT REFORZADO ---
    prompt = f"""
    Eres un servicio API automatizado llamado "Agente de Triaje". Tu única función es analizar
    información y devolver un objeto JSON. No eres un asistente conversacional. No saludes.

    **Reglas de Admisibilidad:**
    1. Estrato Socioeconómico: 1 o 2.
    2. Cuantía: Menor a 40 SMLMV (SMLMV = $1,300,000 COP).
    3. Territorio: Cúcuta, Norte de Santander.
    4. Materia: No penal, no JEP.

    **Tarea:**
    Analiza la siguiente información y la evidencia adjunta. Extrae los datos, decide la
    admisibilidad y justifica tu decisión.

    **Información del Caso:**
    ---
    {historial_chat}
    ---

    **Instrucción Final OBLIGATORIA:**
    Tu respuesta debe ser EXCLUSIVAMENTE un bloque de código JSON válido, sin texto
    introductorio, sin explicaciones adicionales y sin usar markdown (```json).
    La estructura debe ser:
    {{
      "datos_triaje": {{"materia": "string", "cuantia_estimada": "number | string", "estrato": "number | string", "territorio": "string"}},
      "es_admisible": "boolean",
      "justificacion_triaje": "string"
    }}
    """
    
    resultado_analisis = herramientas_lenguaje.analizar_evidencia_con_gemini(prompt=prompt, rutas_archivos=rutas_evidencia)
    
    if "error" in resultado_analisis:
        print(f"    ERROR: El análisis multimodal falló. Causa: {resultado_analisis['error']}")
        return {"es_admisible": False, "justificacion_triaje": f"Fallo técnico: {resultado_analisis['error']}"}
    
    datos_triaje = resultado_analisis.get("datos_triaje", {})
    es_admisible = resultado_analisis.get("es_admisible", False)
    justificacion = resultado_analisis.get("justificacion_triaje", "No se proporcionó justificación.")
    
    print(f"    Veredicto del Triaje: {'Admisible' if es_admisible else 'No Admisible'}.")
    print(f"    Justificación: {justificacion}")
    
    return {"datos_triaje": datos_triaje, "es_admisible": es_admisible, "justificacion_triaje": justificacion}

# =================================================================================
# NODO 2: AGENTE DETERMINADOR DE COMPETENCIAS (PROMPT REFORZADO)
# =================================================================================
def nodo_agente_determinador_competencias(estado: EstadoDelGrafo) -> dict:
    print("\n--- Entrando en el Nodo: Agente Determinador de Competencias ---")
    historial_chat = estado["historial_conversacion"]
    rutas_evidencia = estado["rutas_archivos_evidencia"]
    datos_triaje = estado["datos_triaje"]

    # --- PROMPT REFORZADO ---
    prompt = f"""
    Eres un servicio API de clasificación llamado "Agente Determinador de Competencias".
    Tu única función es analizar un caso y devolver un objeto JSON. No eres un asistente
    conversacional. No saludes.

    **Áreas de Práctica Válidas:**
    - Derecho Privado
    - Derecho Público
    - Derecho Laboral
    - Derecho de Familia
    - Acciones Constitucionales
    - Otro

    **Tarea:**
    Analiza la información del caso y clasifícalo en UNA de las áreas de práctica válidas.

    **Información del Caso:**
    ---
    **Conversación:** {historial_chat}
    **Datos del Triaje:** {datos_triaje}
    ---

    **Instrucción Final OBLIGATORIA:**
    Tu respuesta debe ser EXCLUSIVAMENTE un bloque de código JSON válido, sin texto
    introductorio y sin usar markdown (```json). La estructura debe ser:
    {{
      "area_competencia": "string"
    }}
    """
    
    resultado_analisis = herramientas_lenguaje.analizar_evidencia_con_gemini(prompt=prompt, rutas_archivos=rutas_evidencia)
    
    if "error" in resultado_analisis:
        print(f"    ERROR: La clasificación de competencia falló. Causa: {resultado_analisis['error']}")
        return {"area_competencia": "Error en clasificación"}
        
    area_competencia = resultado_analisis.get("area_competencia", "Clasificación no determinada")
    
    print(f"    Veredicto de Competencia: El caso pertenece a '{area_competencia}'.")
    
    return {"area_competencia": area_competencia}

# =================================================================================
# NODO 3: AGENTE REPARTIDOR (LÓGICA REAL - Sin cambios)
# =================================================================================
def nodo_agente_repartidor(estado: EstadoDelGrafo) -> dict:
    # ... (El código de este nodo se mantiene exactamente igual)
    print("\n--- Entrando en el Nodo: Agente Repartidor (Lógica Real) ---")
    area_competencia = estado["area_competencia"]
    if not area_competencia or "Error" in area_competencia:
        print(f"    ERROR: No hay un área de competencia válida ('{area_competencia}') para asignar.")
        return {}
    id_estudiante_asignado = None
    id_asesor_asignado = None
    try:
        with Session(motor) as sesion:
            print(f"    Acción: Consultando la base de datos para el área de '{area_competencia}'...")
            subconsulta_asesor = (select(Asignacion.id_asesor, func.count(Asignacion.id_caso).label("total_casos")).group_by(Asignacion.id_asesor).subquery())
            consulta_asesor = (select(Asesor.id_asesor).join(subconsulta_asesor, Asesor.id_asesor == subconsulta_asesor.c.id_asesor, isouter=True).where(Asesor.area_competencia == area_competencia).order_by(func.coalesce(subconsulta_asesor.c.total_casos, 0)).limit(1))
            resultado_asesor = sesion.exec(consulta_asesor).first()
            if resultado_asesor: id_asesor_asignado = resultado_asesor
            subconsulta_estudiante = (select(Asignacion.id_estudiante, func.count(Asignacion.id_caso).label("total_casos")).group_by(Asignacion.id_estudiante).subquery())
            consulta_estudiante = (select(Estudiante.id_estudiante).join(subconsulta_estudiante, Estudiante.id_estudiante == subconsulta_estudiante.c.id_estudiante, isouter=True).where(Estudiante.area_competencia == area_competencia).order_by(func.coalesce(subconsulta_estudiante.c.total_casos, 0)).limit(1))
            resultado_estudiante = sesion.exec(consulta_estudiante).first()
            if resultado_estudiante: id_estudiante_asignado = resultado_estudiante
            if not id_estudiante_asignado or not id_asesor_asignado:
                print("    ADVERTENCIA: No se encontró un equipo completo disponible en esta área.")
                return {}
            print(f"    Resultado: Equipo seleccionado (Estudiante ID: {id_estudiante_asignado}, Asesor ID: {id_asesor_asignado}).")
            return {"id_estudiante_asignado": id_estudiante_asignado, "id_asesor_asignado": id_asesor_asignado}
    except Exception as e:
        print(f"    ERROR CRÍTICO durante la consulta a la base de datos: {e}")
        return {}