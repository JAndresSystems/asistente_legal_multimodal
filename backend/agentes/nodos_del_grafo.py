from sqlmodel import Session, select, func
from typing import Dict, Any, Optional

from .estado_del_grafo import EstadoDelGrafo
from ..herramientas.herramientas_lenguaje import analizar_evidencia_con_gemini, generar_respuesta_texto
from ..herramientas.herramienta_rag import buscar_en_base_de_conocimiento
from ..herramientas.herramienta_documentos import generar_documento_desde_plantilla
from ..base_de_datos import motor
from ..api.modelos_compartidos import Estudiante, Asesor, Asignacion, Caso, Usuario

# --- (Nodos 1, 2.A y 2.B permanecen igual) ---
def nodo_agente_triaje(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente de Triaje ---")
    rutas_archivos = estado["rutas_archivos_evidencia"]
    prompt_completo = """
    ERES un asistente legal experto en admisibilidad. Tu unica funcion es devolver un JSON.
    JSON: {"admisible": bool, "justificacion": "string", "hechos_clave": "string"}
    REGLAS: Admisible si no es penal y es de bajos recursos.
    Analiza la evidencia y responde.
    """
    resultado_analisis = analizar_evidencia_con_gemini(
        archivos_locales=rutas_archivos,
        prompt_usuario=prompt_completo
    )
    return {"resultado_triaje": resultado_analisis}

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


# --- NODO 3: AGENTE DETERMINADOR DE COMPETENCIAS (PROMPT FINAL) ---
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


# --- NODO 4: AGENTE REPARTIDOR (CON LOGICA DE ESCRITURA EN BD) ---
def encontrar_persona_con_menos_carga(sesion: Session, modelo: Any, area: str) -> Optional[int]:
    # ... (esta funcion auxiliar no cambia)
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
        
        # --- INICIO DE LA CORRECCION FINAL ---
        if id_estudiante is not None and id_asesor is not None:
            # 1. Crear la instancia de la asignacion
            nueva_asignacion = Asignacion(
                id_caso=id_caso,
                id_estudiante=id_estudiante,
                id_asesor=id_asesor
            )
            # 2. Añadir y confirmar en la base de datos
            sesion_db.add(nueva_asignacion)
            sesion_db.commit()
            mensaje_db = "Asignacion creada exitosamente en la base de datos."
            print(f"-> EXITO (DB): Caso {id_caso} asignado a Estudiante {id_estudiante} y Asesor {id_asesor}.")
        else:
            mensaje_db = "No se encontraron estudiantes o asesores disponibles en el area."
            print(f"-> ALERTA (DB): No se pudo realizar la asignacion para el caso {id_caso}.")
        # --- FIN DE LA CORRECCION FINAL ---

    resultado = {
        "id_estudiante_asignado": id_estudiante, 
        "id_asesor_asignado": id_asesor,
        "operacion_db": mensaje_db
    }
    return {"resultado_repartidor": resultado}


# --- (Agentes Juridico y Generador de Documentos permanecen igual) ---
def nodo_agente_juridico(estado: EstadoDelGrafo) -> Dict[str, Any]:
    # ...
    return {"resultado_agente_juridico": "Ejecucion omitida en este flujo."}

def nodo_agente_generador_documentos(estado: EstadoDelGrafo) -> Dict[str, Any]:
    # ...
    return {"resultado_agente_generador_documentos": "Ejecucion omitida en este flujo."}