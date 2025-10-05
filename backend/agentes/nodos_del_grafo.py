# backend/agentes/nodos_del_grafo.py

from sqlmodel import Session, select, func
from typing import Dict, Any, Optional

# --- SECCION DE IMPORTACIONES CORREGIDA ---
# Usamos '.' para importar desde la misma carpeta (agentes).
from .estado_del_grafo import EstadoDelGrafo
# Usamos '..' para subir un nivel (a 'backend') y luego entrar a las carpetas correspondientes.
from ..herramientas.herramientas_lenguaje import analizar_evidencia_con_gemini, generar_respuesta_texto
from ..herramientas.herramienta_rag import buscar_en_base_de_conocimiento
from ..herramientas.herramienta_documentos import generar_documento_desde_plantilla
from ..base_de_datos import motor
from ..api.modelos_compartidos import Estudiante, Asesor, Asignacion, Caso, Usuario

# --- NODO 1: AGENTE DE TRIAJE (Estable) ---
def nodo_agente_triaje(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente de Triaje ---")
    rutas_archivos = estado["rutas_archivos_evidencia"]
    id_caso = estado["id_caso"]
    print(f"Agente de Triaje analizando {len(rutas_archivos)} archivo(s) para el caso ID: {id_caso}.")
    prompt_sistema = """
    ERES un asistente legal experto en la regulacion de consultorios juridicos en Colombia.
    TU MISION es analizar la evidencia multimodal (imagenes, documentos, texto) y determinar
    la admisibilidad del caso segun las siguientes REGLAS INQUEBRABLES:
    1.  Solo puedes responder con un objeto JSON valido, sin texto introductorio ni explicaciones.
    2.  El JSON debe tener la siguiente estructura: {"admisible": boolean, "justificacion": "string", "datos_extraidos": {"tipo_documento": "string", "hechos_clave": "string"}}
    3.  Criterios de Admisibilidad: El caso es admisible si la evidencia sugiere un conflicto legal que no sea de competencia penal y que parezca ser de una persona de bajos recursos.
    4.  Extrae los hechos mas importantes del caso en 'hechos_clave'.
    """
    resultado_analisis = analizar_evidencia_con_gemini(
        archivos_locales=rutas_archivos,
        prompt_usuario="Analiza la siguiente evidencia y determina la admisibilidad del caso segun las reglas.",
        prompt_sistema=prompt_sistema
    )
    print("--- Resultado del Agente de Triaje ---")
    print(resultado_analisis)
    return {"resultado_triaje": resultado_analisis}

# --- NODO 2: AGENTE DETERMINADOR DE COMPETENCIAS (Estable) ---
def nodo_agente_determinador_competencias(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente Determinador de Competencias ---")
    resultado_triaje = estado.get("resultado_triaje")
    id_caso = estado["id_caso"]
    if not resultado_triaje or not resultado_triaje.get("admisible"):
        print(f"El caso {id_caso} no es admisible o el triaje fallo. Omitiendo determinacion de competencia.")
        return {"resultado_determinador_competencias": {"area_competencia": "No Aplica - Caso No Admisible"}}
    print(f"Agente Determinador de Competencias clasificando el caso ID: {id_caso}.")
    rutas_archivos = estado["rutas_archivos_evidencia"]
    hechos_clave = resultado_triaje.get("datos_extraidos", {}).get("hechos_clave", "No disponibles")
    prompt_sistema = """
    ERES un jurista experto en la estructura del derecho en Colombia.
    TU MISION es clasificar el caso presentado en una de las siguientes areas de competencia del consultorio juridico.
    REGLAS INQUEBRABLES:
    1.  Solo puedes responder con un objeto JSON valido.
    2.  El JSON debe tener la estructura: {"area_competencia": "string", "justificacion_breve": "string"}
    3.  Las unicas areas de competencia validas son: "Derecho Privado", "Derecho Publico", "Derecho Laboral", "Derecho de Familia", "No Clasificable".
    4.  Basa tu decision en los hechos clave y la evidencia proporcionada.
    """
    prompt_usuario = f"Basado en la evidencia y los hechos clave, clasifica el caso:\nHechos Clave: {hechos_clave}"
    resultado_clasificacion = analizar_evidencia_con_gemini(
        archivos_locales=rutas_archivos,
        prompt_usuario=prompt_usuario,
        prompt_sistema=prompt_sistema
    )
    print("--- Resultado del Agente Determinador de Competencias ---")
    print(resultado_clasificacion)
    return {"resultado_determinador_competencias": resultado_clasificacion}

# --- NODO 3: AGENTE REPARTIDOR (Estable) ---
def encontrar_persona_con_menos_carga(sesion: Session, modelo: Any, area: str) -> Optional[int]:
    declaracion = (
        select(modelo.id, func.count(Asignacion.id_caso).label("carga_trabajo"))
        .join(Asignacion, modelo.id == getattr(Asignacion, f"id_{modelo.__name__.lower()}"), isouter=True)
        .where(modelo.area_especialidad == area)
        .group_by(modelo.id)
        .order_by(func.count(Asignacion.id_caso).asc())
    )
    resultado = sesion.exec(declaracion).first()
    return resultado.id if resultado else None

def nodo_agente_repartidor(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente Repartidor ---")
    id_caso = estado["id_caso"]
    resultado_competencias = estado.get("resultado_determinador_competencias")
    area_competencia = resultado_competencias.get("area_competencia") if resultado_competencias else None
    areas_no_validas = ["No Aplica - Caso No Admisible", "No Clasificable", None]
    if not area_competencia or area_competencia in areas_no_validas:
        print(f"No se puede repartir el caso {id_caso} debido a un area de competencia no valida: {area_competencia}")
        return {"resultado_repartidor": {"id_estudiante_asignado": None, "id_asesor_asignado": None, "detalle": "No se asigno por area de competencia invalida."}}
    print(f"Buscando personal en el area '{area_competencia}' para el caso {id_caso}...")
    try:
        with Session(motor) as sesion_db:
            id_estudiante_seleccionado = encontrar_persona_con_menos_carga(sesion_db, Estudiante, area_competencia)
            id_asesor_seleccionado = encontrar_persona_con_menos_carga(sesion_db, Asesor, area_competencia)
        resultado = {"id_estudiante_asignado": id_estudiante_seleccionado, "id_asesor_asignado": id_asesor_seleccionado, "detalle": f"Asignacion para el area de {area_competencia} procesada."}
        print(f"--- Resultado del Agente Repartidor para caso {id_caso} ---")
        print(resultado)
        return {"resultado_repartidor": resultado}
    except Exception as e:
        print(f"Error critico durante la consulta a la base de datos en el Agente Repartidor: {e}")
        return {"resultado_repartidor": {"id_estudiante_asignado": None, "id_asesor_asignado": None, "detalle": f"Error en la base de datos: {e}"}}

# --- NODO 4: AGENTE JURIDICO (Estable) ---
def nodo_agente_juridico(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente Juridico ---")
    pregunta = estado.get("solicitud_agente_juridico")
    if not pregunta:
        return {"resultado_agente_juridico": "No se proporciono ninguna solicitud para el agente juridico."}
    resultado_competencias = estado.get("resultado_determinador_competencias")
    area_competencia = resultado_competencias.get("area_competencia") if resultado_competencias else None
    if not area_competencia or area_competencia == "No Clasificable":
        return {"resultado_agente_juridico": f"No se pudo ejecutar la busqueda RAG por falta de un area de competencia valida."}
    print(f"Agente Juridico investigando: '{pregunta}' en el area de '{area_competencia}'")
    contexto_recuperado = buscar_en_base_de_conocimiento(consulta=pregunta, area_conocimiento=area_competencia)
    print(f"Contexto recuperado de la base de conocimiento: {contexto_recuperado[:200]}...")
    prompt_final = f"""
    Eres un abogado experto y un asistente de investigacion. Responde la pregunta del usuario de manera clara y fundamentada, utilizando UNICAMENTE el siguiente contexto. No debes inventar informacion ni usar conocimiento externo.
    --- CONTEXTO RECUPERADO ---
    {contexto_recuperado}
    --- FIN DEL CONTEXTO ---
    PREGUNTA DEL USUARIO: {pregunta}
    RESPUESTA FUNDAMENTADA:
    """
    respuesta_sintetizada = generar_respuesta_texto(prompt=prompt_final)
    print("--- Resultado del Agente Juridico ---")
    print(respuesta_sintetizada)
    return {"resultado_agente_juridico": respuesta_sintetizada}

# --- NODO 5: AGENTE GENERADOR DE DOCUMENTOS (Estable) ---
def nodo_agente_generador_documentos(estado: EstadoDelGrafo) -> Dict[str, Any]:
    print("--- Ejecutando Nodo: Agente Generador de Documentos ---")
    id_caso = estado.get("id_caso")
    solicitud = estado.get("solicitud_agente_documentos")
    if not id_caso or not solicitud:
        mensaje_error = "No se puede generar el documento: falta el 'id_caso' o la 'solicitud' en el estado."
        print(f"ERROR: {mensaje_error}")
        return {"resultado_agente_generador_documentos": mensaje_error}
    print(f"Agente Generador de Documentos iniciando para el caso ID: {id_caso}. ¡El ID fue recibido correctamente!")
    tipo_documento = solicitud.get("tipo_documento", "documento_generico")
    try:
        with Session(motor) as sesion_db:
            declaracion = select(Caso, Usuario).join(Usuario).where(Caso.id == id_caso)
            resultado_db = sesion_db.exec(declaracion).one_or_none()
            if not resultado_db:
                return {"resultado_agente_generador_documentos": f"Error: No se encontro el caso con ID {id_caso} en la base de datos."}
            caso, usuario = resultado_db
            datos_plantilla = {
                "nombre_completo": usuario.nombre,
                "cedula": usuario.cedula,
                "email": usuario.email,
                "hechos_del_caso": caso.descripcion_hechos,
            }
            print(f"Datos para la plantilla recuperados: {datos_plantilla}")
            ruta_archivo_generado = generar_documento_desde_plantilla(
                nombre_plantilla=f"{tipo_documento}.docx",
                datos=datos_plantilla,
                id_caso=id_caso
            )
            print(f"--- Resultado del Agente Generador de Documentos ---")
            print(f"Documento generado en: {ruta_archivo_generado}")
            return {"resultado_agente_generador_documentos": ruta_archivo_generado}
    except Exception as e:
        mensaje_error = f"Error critico durante la generacion del documento para el caso {id_caso}: {e}"
        print(f"ERROR: {mensaje_error}")
        return {"resultado_agente_generador_documentos": mensaje_error}