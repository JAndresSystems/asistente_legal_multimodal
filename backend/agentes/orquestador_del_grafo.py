# backend/agentes/orquestador_del_grafo.py

from langgraph.graph import StateGraph, END
from .estado_del_grafo import EstadoDelGrafo
from .nodos_del_grafo import (
    nodo_procesador_evidencia,
    nodo_investigador_analista,
    nodo_sintetizador_estrategico,
    nodo_guardian_calidad
)

print("SETUP-LANGGRAPH: Creando el grafo de agentes...")

# --- FUNCIÓN DE DECISIÓN 1: PUNTO DE CONTROL INICIAL (SINTAXIS CORREGIDA) ---
def clasificar_resultado_del_procesamiento(estado: EstadoDelGrafo) -> str:
    """
    Después de procesar la evidencia, decide si continuar o finalizar.
    Usa la sintaxis de objeto (estado.atributo), que es la correcta para este grafo.
    """
    print("\n--- Entrando en el Punto de Control Inicial ---")
    
    # La forma correcta de acceder al estado es como un objeto.
    texto_extraido = estado.texto_extraido
    
    if texto_extraido and not texto_extraido.startswith("Error"):
        print("    Decisión: El procesamiento fue exitoso. Continuando.")
        return "continuar"
    else:
        print("    Decisión: El procesamiento inicial falló. Finalizando el flujo de trabajo.")
        return "finalizar"

# --- FUNCIÓN DE DECISIÓN 2: SUPERVISOR DE CALIDAD (BASADO EN TU CÓDIGO ORIGINAL) ---
def supervisor_de_calidad(estado: EstadoDelGrafo) -> str:
    """
    Actúa como un supervisor inteligente para decidir el siguiente paso,
    usando la sintaxis de objeto (estado.atributo).
    """
    print("\n--- Entrando en el Supervisor de Calidad ---")
    
    # Verificamos si los datos necesarios existen.
    if not estado.borrador_estrategia or "Error" in estado.borrador_estrategia:
        print("    Decisión: Faltan datos críticos. Finalizando.")
        return "finalizar"
    
    # Lógica del veredicto.
    veredicto = estado.verificacion_calidad
    if veredicto and veredicto.get("verificado"): # .get() se usa aquí porque 'veredicto' SÍ es un diccionario
        print("    Decisión: ¡El borrador cumple los estándares! Finalizando.")
        return "finalizar"

    # Lógica del límite de intentos.
    MAXIMOS_INTENTOS = 2
    intentos = estado.intentos_correccion
    if intentos >= MAXIMOS_INTENTOS:
        print(f"    Decisión: Límite de {MAXIMOS_INTENTOS} intentos alcanzado. Finalizando.")
        return "finalizar"
    
    print(f"    Decisión: El borrador NO cumple (Intento {intentos}). Devolviendo para corrección.")
    return "corregir"

# --- CONSTRUCCIÓN DEL GRAFO (CORREGIDO Y SIMPLIFICADO) ---

flujo_de_trabajo = StateGraph(EstadoDelGrafo)

# 1. Añadir los nodos
flujo_de_trabajo.add_node("procesador_evidencia", nodo_procesador_evidencia)
flujo_de_trabajo.add_node("investigador_analista", nodo_investigador_analista)
flujo_de_trabajo.add_node("sintetizador_estrategico", nodo_sintetizador_estrategico)
flujo_de_trabajo.add_node("guardian_de_calidad", nodo_guardian_calidad)

# 2. Definir el punto de entrada
flujo_de_trabajo.set_entry_point("procesador_evidencia")

# 3. Definir las conexiones
flujo_de_trabajo.add_conditional_edges(
    "procesador_evidencia",
    clasificar_resultado_del_procesamiento,
    {
        "continuar": "investigador_analista",
        "finalizar": END
    }
)
flujo_de_trabajo.add_edge("investigador_analista", "sintetizador_estrategico")
flujo_de_trabajo.add_edge("sintetizador_estrategico", "guardian_de_calidad")

flujo_de_trabajo.add_conditional_edges(
    "guardian_de_calidad",
    supervisor_de_calidad,
    {
        "corregir": "sintetizador_estrategico",
        "finalizar": END
    }
)
print("SETUP-LANGGRAPH: Conexiones y bucles definidos.")

# 4. Compilar el grafo
try:
    grafo_compilado = flujo_de_trabajo.compile()
    print("SETUP-LANGGRAPH: ¡Grafo de agentes compilado y listo para usar!")
except Exception as e:
    print(f"SETUP-LANGGRAPH-ERROR: ¡No se pudo compilar el grafo! Causa: {e}")
    grafo_compilado = None
