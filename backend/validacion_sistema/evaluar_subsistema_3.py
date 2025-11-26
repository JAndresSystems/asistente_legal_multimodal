# backend/validacion_sistema/evaluar_subsistema_3.py
import sys
import os
import time
import uuid
import pandas as pd
from typing import Dict, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import operator

# --- CONFIGURACIÓN DE RUTAS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.append(project_root)

# --- 1. DEFINICIÓN DE UN GRAFO DE PRUEBA (SIMULACIÓN) ---
# Usamos un grafo sintético para aislar la medición de la arquitectura

class EstadoPrueba(TypedDict):
    mensajes: Annotated[list, operator.add]
    contador_pasos: int

def nodo_a(estado):
    # Simula un proceso de pensamiento (latencia mínima)
    time.sleep(0.01) 
    return {"mensajes": ["Paso A completado"], "contador_pasos": 1}

def nodo_b(estado):
    # Simula una búsqueda o validación
    time.sleep(0.01)
    return {"mensajes": ["Paso B completado"], "contador_pasos": 1}

# Construimos el grafo con MEMORIA EN RAM (Para benchmark de velocidad pura)
memoria_checkpointer = MemorySaver()
workflow = StateGraph(EstadoPrueba)
workflow.add_node("nodo_a", nodo_a)
workflow.add_node("nodo_b", nodo_b)
workflow.set_entry_point("nodo_a")
workflow.add_edge("nodo_a", "nodo_b")
workflow.add_edge("nodo_b", END)
app_prueba = workflow.compile(checkpointer=memoria_checkpointer)

# --- LÓGICA DE EVALUACIÓN ---

def ejecutar_auditoria_memoria():
    print("\n" + "="*60)
    print(f" INICIANDO EVALUACIÓN SUBSISTEMA 3 (MEMORIA) ".center(60, "="))
    print("="*60)

    # Identificador de hilo único para esta prueba
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # --- PRUEBA 1: KPI 3.1 INTEGRIDAD DE TRAZABILIDAD ---
    print("\n🔍 1. Evaluando Integridad (KPI 3.1)...")
    
    input_inicial = {"mensajes": ["Inicio del test"], "contador_pasos": 0}
    
    eventos_ejecutados = 0 # Contador de pasos lógicos
    
    # Ejecutamos el grafo paso a paso
    for event in app_prueba.stream(input_inicial, config):
        eventos_ejecutados += 1
        pass
    
    # Consultamos el historial guardado
    historial_guardado = list(app_prueba.get_state_history(config))
    total_snapshots = len(historial_guardado)
    
    print(f"   Pasos Lógicos Ejecutados: {eventos_ejecutados}")
    print(f"   Snapshots en Memoria: {total_snapshots}")
    
    # Cálculo KPI 3.1
    # CORRECCIÓN DEL ERROR: Usamos la variable correcta 'eventos_ejecutados'
    if eventos_ejecutados > 0:
        if total_snapshots >= eventos_ejecutados:
            ite = 1.0
        else:
            ite = total_snapshots / eventos_ejecutados
    else:
        ite = 0.0
        
    res_ite = "✅ ÍNTEGRO" if ite >= 1.0 else "❌ PÉRDIDA DE DATOS"
    print(f"   Resultado: {res_ite}")

    # --- PRUEBA 2: KPI 3.2 LATENCIA DE RECUPERACIÓN ---
    print("\n⏱️ 2. Evaluando Latencia de Recuperación (KPI 3.2)...")
    
    tiempos = []
    # Hacemos 10 mediciones para sacar un promedio estable
    for i in range(10):
        inicio = time.perf_counter() # Cronómetro de alta precisión
        
        # Función crítica: Leer el estado completo de la memoria
        estado_recuperado = app_prueba.get_state(config)
        
        fin = time.perf_counter()
        latencia_ms = (fin - inicio) * 1000 # Convertir a milisegundos
        tiempos.append(latencia_ms)
        # print(f"   Intento {i+1}: {latencia_ms:.4f} ms") # Comentado para limpiar salida
        
    latencia_promedio = sum(tiempos) / len(tiempos)
    
    # --- RESULTADOS FINALES ---
    print("\n" + "="*60)
    print(" RESULTADOS FINALES SUBSISTEMA 3 ".center(60, "="))
    print("="*60)
    
    print(f"\n📊 KPI 3.1: Integridad Trazabilidad (I_TE)")
    print(f"   Resultado: {ite:.4f}")
    print(f"   Meta: 1.0 -> {'APROBADO ✅' if ite >= 1.0 else 'RECHAZADO ❌'}")

    print(f"\n⚡ KPI 3.2: Latencia Recuperación Contexto (L_CTX)")
    print(f"   Promedio: {latencia_promedio:.4f} ms")
    # La meta del PDF es < 200ms
    meta_latencia = 200.0 
    print(f"   Meta: < {meta_latencia} ms -> {'APROBADO ✅' if latencia_promedio < meta_latencia else 'RECHAZADO ❌'}")
    print("="*60)

    # Exportar Excel
    df = pd.DataFrame([
        {"Métrica": "Integridad (I_TE)", "Valor": ite, "Estado": "APROBADO" if ite >=1 else "RECHAZADO"},
        {"Métrica": "Latencia Promedio (ms)", "Valor": f"{latencia_promedio:.4f}", "Estado": "APROBADO" if latencia_promedio < 200 else "RECHAZADO"}
    ])
    
    ruta_excel = os.path.join(current_dir, "reporte_validacion_subsistema_3.xlsx")
    df.to_excel(ruta_excel, index=False)
    print(f"\n📄 Reporte guardado en: {ruta_excel}")

if __name__ == "__main__":
    ejecutar_auditoria_memoria()