# backend/agentes/orquestador_del_grafo.py

from langgraph.graph import StateGraph, END
import mimetypes
from .estado_del_grafo import EstadoDelGrafo

# ==============================================================================
# IMPORTAMOS LOS NODOS
# ==============================================================================
from .nodos_del_grafo import (
    nodo_agente_triaje,
    nodo_solicitar_informacion_adicional, 
    nodo_preparar_respuesta_rechazo,
    nodo_agente_analizador_pdf,
    nodo_agente_analizador_audio,
    nodo_agente_determinador_competencias,
    nodo_agente_repartidor,
    nodo_agente_juridico
)

workflow = StateGraph(EstadoDelGrafo)

# Añadimos todos los nodos
workflow.add_node("agente_triaje", nodo_agente_triaje)
workflow.add_node("solicitar_informacion_adicional", nodo_solicitar_informacion_adicional)
workflow.add_node("preparar_respuesta_rechazo", nodo_preparar_respuesta_rechazo)
workflow.add_node("agente_analizador_pdf", nodo_agente_analizador_pdf)
workflow.add_node("agente_analizador_audio", nodo_agente_analizador_audio)
workflow.add_node("agente_determinador_competencias", nodo_agente_determinador_competencias)
workflow.add_node("agente_repartidor", nodo_agente_repartidor)
workflow.add_node("agente_juridico", nodo_agente_juridico)

workflow.set_entry_point("agente_triaje")

# ==============================================================================
# FUNCIÓN DE DECISIÓN MEJORADA CON MANEJO DE ERRORES COMPLETO
# ==============================================================================
def decision_despues_del_triaje(estado: EstadoDelGrafo) -> str:
    """
    Función de decisión mejorada que maneja correctamente todos los casos,
    incluyendo errores y estados incompletos.
    """
    print("\n--- [ORQUESTADOR] Tomando decision despues del triaje ---")
    
    # Verificar si hay un error en el resultado del triaje
    if isinstance(estado.get("resultado_triaje"), dict) and "error" in estado["resultado_triaje"]:
        print(f"--- [ORQUESTADOR] ERROR detectado en el triaje: {estado['resultado_triaje']['error']}")
        print("--- [ORQUESTADOR] Decision: Error en el procesamiento. Enviando a rechazo.")
        return "preparar_respuesta_rechazo"
    
    # Garantizar que haya un resultado_triaje válido
    resultado_triaje = estado.get("resultado_triaje", {})
    
    # Caso 1: Resultado vacío o inválido
    if not resultado_triaje or not isinstance(resultado_triaje, dict):
        print("--- [ORQUESTADOR] ERROR: Resultado de triaje inválido o vacío.")
        # Crear un resultado mínimo para el rechazo
        if "resultado_triaje" not in estado:
            estado["resultado_triaje"] = {
                "admisible": False,
                "justificacion": "Error en el procesamiento del caso. Por favor, contacte al administrador.",
                "hechos_clave": "Error técnico durante el análisis",
                "informacion_suficiente": True
            }
        return "preparar_respuesta_rechazo"
    
    # Caso 2: Manejar casos donde el resultado_triaje no tiene la estructura esperada
    if "admisible" not in resultado_triaje:
        print("--- [ORQUESTADOR] ADVERTENCIA: Resultado de triaje sin campo 'admisible'.")
        resultado_triaje["admisible"] = False
        resultado_triaje["justificacion"] = "Error en el formato de respuesta del sistema de IA."
        resultado_triaje["informacion_suficiente"] = True
        resultado_triaje["hechos_clave"] = "Respuesta no válida del sistema de IA"
        estado["resultado_triaje"] = resultado_triaje
    
    # Caso 3: Información insuficiente
    if not resultado_triaje.get("informacion_suficiente", False):
        print("--- [ORQUESTADOR] Decision: Informacion insuficiente. Solicitando mas datos.")
        return "solicitar_informacion_adicional"
    
    # Caso 4: Caso no admisible
    if not resultado_triaje.get("admisible", False):
        print("--- [ORQUESTADOR] Decision: Caso no admisible. Preparando respuesta de rechazo.")
        return "preparar_respuesta_rechazo"
    
    # Caso 5: Caso admisible - determinar siguiente paso
    print("--- [ORQUESTADOR] Decision: Caso admisible. Continuando con el análisis.")
    
    # Si hay archivos, determinar el tipo de analizador
    rutas_archivos = estado.get("rutas_archivos_evidencia", [])
    if rutas_archivos:
        ruta_archivo = rutas_archivos[0]
        tipo_mime, _ = mimetypes.guess_type(ruta_archivo)
        
        if tipo_mime:
            tipo_mime = tipo_mime.lower()
            if "pdf" in tipo_mime:
                print("--- [ORQUESTADOR] Tipo de archivo detectado: PDF. Dirigiendo al analizador de PDF.")
                return "agente_analizador_pdf"
            if any(t in tipo_mime for t in ["audio", "mp3", "wav", "mpeg"]):
                print("--- [ORQUESTADOR] Tipo de archivo detectado: Audio. Dirigiendo al analizador de audio.")
                return "agente_analizador_audio"
    
    # Por defecto, continuar con la determinación de competencias
    print("--- [ORQUESTADOR] Continuando con determinación de competencias.")
    return "agente_determinador_competencias"

workflow.add_conditional_edges(
    "agente_triaje",
    decision_despues_del_triaje
)

# Conexiones finales
workflow.add_edge("solicitar_informacion_adicional", END)
workflow.add_edge("preparar_respuesta_rechazo", END)
workflow.add_edge("agente_analizador_pdf", "agente_determinador_competencias")
workflow.add_edge("agente_analizador_audio", "agente_determinador_competencias")
workflow.add_edge("agente_determinador_competencias", "agente_repartidor")
workflow.add_edge("agente_repartidor", "agente_juridico")
workflow.add_edge("agente_juridico", END)

# ==============================================================================
# FUNCIÓN DE VALIDACIÓN DE ESTADO FINAL
# ==============================================================================
def validar_estado_final(estado: EstadoDelGrafo) -> EstadoDelGrafo:
    """
    Asegura que el estado final tenga al menos uno de los campos requeridos por LangGraph.
    Esta función se ejecuta justo antes de que el grafo termine su ejecución.
    """
    campos_requeridos = [
        'id_caso', 'rutas_archivos_evidencia', 'texto_adicional_usuario', 
        'resultado_triaje', 'resultado_analisis_documento', 'resultado_analisis_audio',
        'resultado_determinador_competencias', 'resultado_repartidor',
        'resultado_agente_juridico'
    ]
    
    # Verificar si el estado tiene al menos un campo requerido
    tiene_campo_requerido = any(campo in estado and estado[campo] for campo in campos_requeridos)
    
    if not tiene_campo_requerido:
        print("⚠️ [VALIDACIÓN] Estado final no contiene campos requeridos. Añadiendo resultado_triaje por defecto.")
        
        # Asegurar que haya un resultado_triaje mínimo
        if "resultado_triaje" not in estado:
            estado["resultado_triaje"] = {
                "admisible": False,
                "justificacion": "Estado incompleto. Por favor, contacte al administrador.",
                "hechos_clave": "Error en el procesamiento del estado",
                "informacion_suficiente": True
            }
        
        # Asegurar que haya un id_caso
        if "id_caso" not in estado:
            estado["id_caso"] = estado.get("id_caso", 0)
    
    return estado

# Compilar el grafo con validación de estado
class GrafoValidado:
    def __init__(self, grafo_compilado):
        self.grafo_compilado = grafo_compilado
    
    def invoke(self, estado_inicial):
        resultado = self.grafo_compilado.invoke(estado_inicial)
        return validar_estado_final(resultado)

grafo_compilado = GrafoValidado(workflow.compile())
print("SUCCESS (LANGGRAPH): Grafo de admision con manejo de errores robusto compilado exitosamente.")
print("SUCCESS (LANGGRAPH): Validación de estado final habilitada.")