# Ubicación: backend/tareas.py

import json
from sqlmodel import Session
# Se ELIMINAN las importaciones de Celery
from .api.modelos_compartidos import Caso, EstadoCaso
from .agentes.orquestador_del_grafo import grafo_compilado
from .agentes.estado_del_grafo import EstadoDelGrafo

# Se ELIMINA el decorador @celery_app.task
# La función ahora acepta 'sesion' como un argumento para ser inyectada por FastAPI
def procesar_evidencia_sincrono(id_caso: int, texto_adicional_usuario: str, sesion: Session):
    """
    Docstring:
    Función SÍNCRONA que procesa un CASO COMPLETO y guarda el resultado
    del análisis como un JSON en el objeto Caso.
    """
    print(f"Iniciando procesamiento SÍNCRONO para el CASO ID: {id_caso}")
    
    caso = None
    try:
        caso = sesion.get(Caso, id_caso)
        if not caso:
            raise ValueError(f"No se pudo encontrar el Caso {id_caso}")

        rutas_archivos = [ev.ruta_archivo for ev in caso.evidencias]
        estado_inicial = {
            "id_caso": id_caso,
            "rutas_archivos_evidencia": rutas_archivos,
            "texto_adicional_usuario": texto_adicional_usuario,
        }

        print(f"El agente analizara un total de {len(rutas_archivos)} evidencia(s).")
        estado_final = grafo_compilado.invoke(estado_inicial)
        print("El grafo de LangGraph completo su ejecucion.")

        reporte_dict = {
            "TRIEJE": estado_final.get('resultado_triaje'),
            "COMPETENCIA": estado_final.get('resultado_determinador_competencias'),
            "ASIGNACION": estado_final.get('resultado_repartidor'),
            "ANALISIS_DOCUMENTO": estado_final.get('resultado_analisis_documento'),
            "ANALISIS_AUDIO": estado_final.get('resultado_analisis_audio'),
            "ANALISIS_JURIDICO": estado_final.get('resultado_agente_juridico'),
        }
        
        reporte_dict_limpio = {k: v for k, v in reporte_dict.items() if v is not None}
        caso.reporte_consolidado = json.dumps(reporte_dict_limpio, indent=2, ensure_ascii=False)
        
        resultado_triaje = estado_final.get('resultado_triaje', {})
        if resultado_triaje.get('admisible') is False:
            caso.estado = EstadoCaso.RECHAZADO
        elif estado_final.get('resultado_repartidor'):
            caso.estado = EstadoCaso.PENDIENTE_ACEPTACION
        
        sesion.add(caso)
        sesion.commit()
        sesion.refresh(caso) 
        print(f"Reporte consolidado y estado actualizados en el Caso {id_caso}.")
        
        # --- CAMBIO CRÍTICO ---
        # Devolvemos el estado final del grafo, no el objeto 'caso'.
        # Esto restaura el contrato de datos que el frontend esperaba.
        return estado_final

    except Exception as e:
        print(f"ERROR CRITICO en el procesamiento síncrono para caso {id_caso}: {e}")
        if caso:
            caso.reporte_consolidado = json.dumps({"error": str(e)})
            caso.estado = EstadoCaso.CERRADO
            sesion.add(caso)
            sesion.commit()
        raise e