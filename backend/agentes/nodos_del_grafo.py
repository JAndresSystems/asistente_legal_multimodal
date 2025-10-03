from .estado_del_grafo import EstadoDelGrafo
from ..herramientas import herramientas_lenguaje


from ..base_de_datos import obtener_sesion

from ..api.modelos_compartidos import Asignacion, Estudiante, Asesor # Suponiendo estos modelos
def nodo_agente_triaje(estado: EstadoDelGrafo) -> dict:
    """
    Implementa la lógica del Agente de Triaje.

    Este nodo analiza la conversación inicial y la evidencia multimodal para
    determinar si un caso cumple con los requisitos de admisibilidad del
    consultorio jurídico.

    Args:
        estado (EstadoDelGrafo): El estado actual del grafo.

    Returns:
        dict: Un diccionario con los resultados para actualizar el estado del grafo.
    """
    print("\n--- Entrando en el Nodo: Agente de Triaje ---")

    historial_chat = estado["historial_conversacion"]
    rutas_evidencia = estado["rutas_archivos_evidencia"]

    # Creamos el prompt para Gemini, instruyéndolo a actuar como nuestro agente.
    prompt = f"""
    Eres el "Agente de Triaje" de un consultorio jurídico colombiano. Tu única misión
    es analizar la conversación y la evidencia adjunta (imágenes, audios, PDFs) para
    determinar objetivamente si el caso es admisible.

    **Reglas de Admisibilidad (Ley 2113 y Reglamento Interno):**
    1.  **Estrato Socioeconómico:** El solicitante debe ser de estrato ninguno o 1 o 2. Valídalo
        buscando menciones en el texto o analizando recibos de servicios públicos si se adjuntan.
    2.  **Cuantía del Caso:** El valor de las pretensiones no puede superar los 40 Salarios
        Mínimos Legales Mensuales Vigentes (SMLMV). Asume un SMLMV de $1.300.000 COP.
    3.  **Competencia Territorial:** El caso debe haber ocurrido en Norte de Santander.
    4.  **Materia:** No se atienden casos penales (hurto, lesiones personales, etc.) ni de competencia
        de la Jurisdicción Especial para la Paz (JEP).

    **Tu Tarea:**
    1.  Analiza TODA la información proporcionada (texto y archivos).
    2.  Extrae los datos clave: 'materia', 'cuantia_estimada', 'estrato' y 'territorio'. Si un dato no se
        puede determinar, déjalo como "No determinado".
    3.  Toma una decisión final ('es_admisible': true o false).
    4.  Escribe una 'justificacion_triaje' clara y breve explicando tu decisión,
        basada en las reglas.

    **Formato de Respuesta Obligatorio:**
    Debes devolver tu análisis ÚNICAMENTE en formato JSON, sin texto introductorio ni explicaciones
    adicionales. La estructura debe ser la siguiente:
    ```json
    {{
      "datos_triaje": {{
        "materia": "string",
        "cuantia_estimada": "number | string",
        "estrato": "number | string",
        "territorio": "string"
      }},
      "es_admisible": "boolean",
      "justificacion_triaje": "string"
    }}
    ```

    **Conversación a Analizar:**
    ---
    {historial_chat}
    ---
    """

    # Invocamos nuestra herramienta central de Gemini.
    resultado_analisis = herramientas_lenguaje.analizar_evidencia_con_gemini(
        prompt=prompt,
        rutas_archivos=rutas_evidencia
    )

    # Verificamos si hubo un error en la herramienta.
    if "error" in resultado_analisis:
        print(f"    ERROR: El análisis multimodal falló. Causa: {resultado_analisis['error']}")
        # Devolvemos un estado de error para que el grafo pueda manejarlo.
        return {
            "es_admisible": False,
            "justificacion_triaje": f"Fallo técnico en el Agente de Triaje: {resultado_analisis['error']}"
        }

    # Extraemos los resultados del JSON devuelto por el modelo.
    datos_triaje = resultado_analisis.get("datos_triaje", {})
    es_admisible = resultado_analisis.get("es_admisible", False)
    justificacion = resultado_analisis.get("justificacion_triaje", "No se proporcionó justificación.")

    print(f"    Veredicto del Triaje: {'Admisible' if es_admisible else 'No Admisible'}.")
    print(f"    Justificación: {justificacion}")

    # Devolvemos el diccionario para actualizar el estado del grafo.
    return {
        "datos_triaje": datos_triaje,
        "es_admisible": es_admisible,
        "justificacion_triaje": justificacion
    }



# =================================================================================
# NODO 2: AGENTE DETERMINADOR DE COMPETENCIAS
# =================================================================================

def nodo_agente_determinador_competencias(estado: EstadoDelGrafo) -> dict:
    """
    Implementa la lógica del Agente Determinador de Competencias.

    Este nodo se activa solo si el caso es admisible. Su función es clasificar
    el caso en una de las áreas de práctica del consultorio jurídico.

    Args:
        estado (EstadoDelGrafo): El estado actual del grafo.

    Returns:
        dict: Un diccionario con el área de competencia para actualizar el estado.
    """
    print("\n--- Entrando en el Nodo: Agente Determinador de Competencias ---")

    historial_chat = estado["historial_conversacion"]
    rutas_evidencia = estado["rutas_archivos_evidencia"]
    datos_triaje = estado["datos_triaje"]

    # Creamos un prompt específico para la tarea de clasificación.
    prompt = f"""
    Eres el "Agente Determinador de Competencias" de un consultorio jurídico.
    Tu única misión es clasificar el siguiente caso en una de las áreas de práctica definidas.
    Analiza la conversación inicial, los datos ya extraídos por el Agente de Triaje y
    cualquier evidencia adjunta para tomar tu decisión.

    **Áreas de Práctica Válidas:**
    - Derecho Privado (Contratos, arrendamientos, deudas, etc.)
    - Derecho Público (Problemas con el estado, servicios públicos, multas de tránsito)
    - Derecho Laboral (Despidos, contratos de trabajo, liquidaciones)
    - Derecho de Familia (Cuotas alimentarias, divorcios, custodia)
    - Acciones Constitucionales (Derechos de petición, tutelas por derecho a la salud, etc.)
    - Otro (Si no encaja claramente en ninguna de las anteriores)

    **Tu Tarea:**
    1.  Analiza toda la información.
    2.  Escoge UNA de las áreas de práctica de la lista.
    3.  Devuelve tu clasificación ÚNICAMENTE en formato JSON, sin texto introductorio,
        con la siguiente estructura:
        ```json
        {{
          "area_competencia": "string"
        }}
        ```

    **Información del Caso a Clasificar:**
    ---
    **Conversación con el Usuario:**
    {historial_chat}

    **Datos del Triaje Inicial:**
    {datos_triaje}
    ---
    """

    # Reutilizamos nuestra herramienta central de Gemini.
    resultado_analisis = herramientas_lenguaje.analizar_evidencia_con_gemini(
        prompt=prompt,
        rutas_archivos=rutas_evidencia
    )

    if "error" in resultado_analisis:
        print(f"    ERROR: La clasificación de competencia falló. Causa: {resultado_analisis['error']}")
        return {"area_competencia": "Error en clasificación"}

    area_competencia = resultado_analisis.get("area_competencia", "Clasificación no determinada")

    print(f"    Veredicto de Competencia: El caso pertenece a '{area_competencia}'.")

    return {"area_competencia": area_competencia}

# =================================================================================
# NODO 3: AGENTE REPARTIDOR
# =================================================================================

def nodo_agente_repartidor(estado: EstadoDelGrafo) -> dict:
    """
    Implementa la lógica del Agente Repartidor.

    Este nodo consulta la base de datos para encontrar al estudiante y asesor
    con la menor carga de trabajo en el área de competencia asignada.

    Args:
        estado (EstadoDelGrafo): El estado actual del grafo.

    Returns:
        dict: Un diccionario con los IDs del equipo asignado.
    """
    print("\n--- Entrando en el Nodo: Agente Repartidor ---")
    
    area_competencia = estado["area_competencia"]
    if not area_competencia or "Error" in area_competencia:
        print("    ERROR: No hay un área de competencia válida para asignar.")
        return {}

    # --- SIMULACIÓN DE LÓGICA DE BASE DE DATOS ---
    # En una implementación real, aquí se harían consultas SQL complejas
    # para contar casos activos por estudiante/asesor en un área específica.
    # Por ahora, simularemos la lógica para mantener el foco en la arquitectura de agentes.

    print(f"    Acción: Buscando el equipo con menor carga en el área de '{area_competencia}'...")
    
    # Simulación: Suponemos que consultamos la BD y encontramos que el estudiante
    # con ID 123 y el asesor con ID 456 son los más desocupados.
    id_estudiante_simulado = 123
    id_asesor_simulado = 456
    
    print(f"    Resultado: Equipo seleccionado (Estudiante ID: {id_estudiante_simulado}, Asesor ID: {id_asesor_simulado}).")
    
    # En una implementación real, aquí se crearía el registro de la asignación en la BD.
    # sesion.add(nueva_asignacion)
    # sesion.commit()

    return {
        "id_estudiante_asignado": id_estudiante_simulado,
        "id_asesor_asignado": id_asesor_simulado,
    }