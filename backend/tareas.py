# Ubicación: backend/tareas.py

import json
from sqlmodel import Session
from .api.modelos_compartidos import Caso, EstadoCaso
from .agentes.orquestador_del_grafo import grafo_compilado
from .agentes.estado_del_grafo import EstadoDelGrafo

def procesar_evidencia_sincrono(id_caso: int, texto_adicional_usuario: str, sesion: Session):
    """
    Docstring:
    Función SÍNCRONA que procesa un CASO COMPLETO.
    VERSIÓN FINAL CORREGIDA: Garantiza que la descripción de hechos completa y
    el historial de conversación se pasen al grafo en cada ejecución.
    """
    print(f"Iniciando procesamiento SÍNCRONO para el CASO ID: {id_caso}")
    
    caso = None
    try:
        caso = sesion.get(Caso, id_caso)
        if not caso:
            raise ValueError(f"No se pudo encontrar el Caso {id_caso}")

        # 1. Cargar la memoria a largo plazo desde la base de datos
        inventario_existente = caso.inventario_documentos or []
        historial_existente = caso.historial_conversacion or []
        rutas_archivos = [ev.ruta_archivo for ev in caso.evidencias]
        
        print(f"MEMORIA: Inventario de documentos leído de BD: {len(inventario_existente)} items")
        print(f"MEMORIA: Historial de conversación leído de BD: {len(historial_existente)} mensajes")
        
        # 2. Construir el estado inicial para el grafo
        #    La clave 'descripcion_hechos' siempre usará la del caso.
        #    El 'texto_adicional_usuario' se añade al historial como un nuevo mensaje.
        estado_inicial = {
            "id_caso": id_caso,
            "descripcion_hechos": caso.descripcion_hechos,
            "rutas_archivos_evidencia": rutas_archivos,
            "inventario_documentos": inventario_existente,
            "historial_chat": historial_existente
        }
        
        # Si el usuario escribió algo en esta interacción, lo añadimos como el último mensaje.
        if texto_adicional_usuario:
            estado_inicial["historial_chat"].append({
                "autor": "usuario",
                "texto": texto_adicional_usuario
            })

        print(f"CONTEXTO: Pasando descripción y {len(estado_inicial['historial_chat'])} mensajes al agente.")
        print(f"El agente analizará un total de {len(rutas_archivos)} evidencia(s).")
        
        # 3. Invocar el grafo
        estado_final = grafo_compilado.invoke(estado_inicial)
        print("El grafo de LangGraph completó su ejecución.")

        # 4. Actualizar la base de datos con los resultados y la nueva memoria
        reporte_dict = {
            "TRIEJE": estado_final.get('resultado_triaje'),
            "COMPETENCIA": estado_final.get('resultado_determinador_competencias'),
            "ASIGNACION": estado_final.get('resultado_repartidor'),
        }
        
        reporte_dict_limpio = {k: v for k, v in reporte_dict.items() if v is not None}
        caso.reporte_consolidado = json.dumps(reporte_dict_limpio, indent=2, ensure_ascii=False)
        
        # Guardamos la memoria actualizada de vuelta en la BD
        caso.inventario_documentos = estado_final.get("inventario_documentos", inventario_existente)
        caso.historial_conversacion = estado_final.get("historial_chat", historial_existente)
        print(f"MEMORIA: Guardando {len(caso.historial_conversacion)} mensajes en la BD.")

        resultado_triaje = estado_final.get('resultado_triaje', {})
        if resultado_triaje.get('decision_triaje') == "NO_ADMISIBLE":
            caso.estado = EstadoCaso.RECHAZADO
        elif estado_final.get('resultado_repartidor'):
            caso.estado = EstadoCaso.PENDIENTE_ACEPTACION
        
        sesion.add(caso)
        sesion.commit()
        sesion.refresh(caso) 
        print(f"Reporte, estado y MEMORIA actualizados en el Caso {id_caso}.")
        
        return estado_final

    except Exception as e:
        print(f"ERROR CRITICO en el procesamiento síncrono para caso {id_caso}: {e}")
        if caso:
            caso.reporte_consolidado = json.dumps({"error": str(e)})
            caso.estado = EstadoCaso.CERRADO
            sesion.add(caso)
            sesion.commit()
        raise e